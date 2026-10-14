"""File-backed user memory store (facts, answered questions, chat notes)."""

from __future__ import annotations

import json
import os
import random
import sys
import threading
import time
from copy import deepcopy
from datetime import date
from typing import Any

from content.memory_keys import (
    DAILY_FACT_KEYS,
    LEGACY_FACT_KEY_ALIASES,
    MULTI_VALUE_FACT_KEYS,
    PROTECTED_FACT_KEYS,
)
from kinito.assets import user_media_directory
from kinito.memory.daily_facts import format_daily_fact, parse_daily_fact
from kinito.memory.fact_values import (
    compact_fact_storage,
    format_fact_values,
    normalize_fact_value_list,
    should_reject_fact_value,
    split_fact_values,
)
from kinito.memory.validation import (
    dedupe_note_entries,
    find_near_duplicate_note_index,
    is_assistant_spam_note,
    is_ephemeral_note,
    is_meaningfully_richer_note,
    is_storable_note,
)

MEMORY_VERSION = 1
MEMORY_FILENAME = "memory.json"

MAX_FACTS = 50
MAX_FACT_VALUE_LEN = 80
# Soft cap for editor replace_notes only — chat extraction does not delete old notes.
MAX_NOTES_STORED = 500
MAX_NOTES_IN_PROMPT = 35
MAX_NOTES_RECENT_IN_PROMPT = 8
MAX_NOTE_LEN = 120
MAX_PROMPT_BLOCK_CHARS = 2500
MAX_FACTS_PROMPT_CHARS = 1600
MAX_NOTES_PROMPT_CHARS = 900
MAX_NEW_NOTES_PER_TURN = 1
MAX_ASKED_TOPICS = 100


def memory_file_path(directory: str | None = None) -> str:
    """Return the path to the JSON memory file."""
    base = directory or user_media_directory
    return os.path.join(base, MEMORY_FILENAME)


def _atomic_replace(temp_path: str, final_path: str) -> None:
    """Replace *final_path* atomically; retry once on Windows file locks."""
    try:
        os.replace(temp_path, final_path)
    except PermissionError:
        if sys.platform != "win32":
            raise
        if os.path.isfile(final_path):
            os.remove(final_path)
        os.replace(temp_path, final_path)


def _write_text_atomic(path: str, payload: str, *, attempts: int = 5) -> None:
    """Write *payload* to *path* via a unique temp file (Windows-safe)."""
    directory = os.path.dirname(path) or "."
    last_error: OSError | None = None
    for attempt in range(attempts):
        temp_path = os.path.join(
            directory,
            f".{os.path.basename(path)}.{os.getpid()}.{threading.get_ident()}.{attempt}.tmp",
        )
        try:
            with open(temp_path, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            _atomic_replace(temp_path, path)
            return
        except OSError as exc:
            last_error = exc
            try:
                if os.path.isfile(temp_path):
                    os.remove(temp_path)
            except OSError:
                pass
            if attempt + 1 < attempts:
                time.sleep(0.05 * (attempt + 1))
    if last_error is not None:
        raise last_error
    raise OSError(f"Failed to write {path}")


class MemoryStore:
    """Load, update, and persist user memory under GameAssets/UserMedia/."""

    def __init__(self, directory: str | None = None) -> None:
        self._directory = directory or user_media_directory
        self._path = memory_file_path(self._directory)
        self._data: dict[str, Any] = self._empty_data()
        # Mood drift runs on the movement thread while chat may save concurrently.
        self._lock = threading.RLock()
        self.load()

    @staticmethod
    def _empty_data() -> dict[str, Any]:
        return {
            "version": MEMORY_VERSION,
            "facts": {},
            "answered_markers": [],
            "asked_topics": [],
            "topic_asked_at": {},
            "notes": [],
        }

    def load(self) -> None:
        """Load memory from disk, or start fresh if missing or invalid."""
        if not os.path.isfile(self._path):
            self._data = self._empty_data()
            return
        try:
            with open(self._path, encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            print(f"Warning: memory.json unreadable ({exc!r}); starting empty.", flush=True)
            self._backup_corrupt_file()
            self._data = self._empty_data()
            return
        if not isinstance(raw, dict):
            print("Warning: memory.json has invalid root type; starting empty.", flush=True)
            self._backup_corrupt_file()
            self._data = self._empty_data()
            return
        normalized, notes_cleaned = self._normalize_loaded(raw)
        self._data = normalized
        if notes_cleaned:
            try:
                self.save()
            except OSError as exc:
                print(f"Warning: memory note migration save failed: {exc!r}", flush=True)

    def _backup_corrupt_file(self) -> None:
        """Move a bad memory.json aside so the original bytes are not lost."""
        if not os.path.isfile(self._path):
            return
        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup = f"{self._path}.corrupt-{stamp}"
        try:
            os.replace(self._path, backup)
            print(f"Warning: corrupt memory backed up to {backup}", flush=True)
        except OSError as exc:
            print(f"Warning: could not backup corrupt memory: {exc!r}", flush=True)

    def save(self) -> None:
        """Persist memory atomically to memory.json."""
        with self._lock:
            os.makedirs(self._directory, exist_ok=True)
            payload = json.dumps(self._data, ensure_ascii=False, indent=2)
            _write_text_atomic(self._path, payload)

    def reset(self) -> None:
        """Clear all memory and remove the persisted memory file."""
        self._data = self._empty_data()
        if os.path.isfile(self._path):
            try:
                os.remove(self._path)
            except OSError:
                pass

    def _normalize_loaded(self, raw: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        data = self._empty_data()
        notes_cleaned = False
        facts = raw.get("facts")
        if isinstance(facts, dict):
            migrated: dict[str, Any] = {}
            for key, value in list(facts.items())[: MAX_FACTS * 2]:
                if not isinstance(key, str):
                    continue
                target_key = LEGACY_FACT_KEY_ALIASES.get(key, key)
                normalized = self._normalize_stored_fact(target_key, value)
                if normalized is None:
                    continue
                if target_key in migrated and target_key in MULTI_VALUE_FACT_KEYS:
                    # Merge legacy + new key when both appear in the same file.
                    existing = normalize_fact_value_list(
                        migrated[target_key]
                        if isinstance(migrated[target_key], list)
                        else [migrated[target_key]]
                    )
                    incoming = normalize_fact_value_list(
                        normalized if isinstance(normalized, list) else [normalized]
                    )
                    merged = compact_fact_storage(
                        normalize_fact_value_list(existing + incoming)
                    )
                    if merged is not None:
                        migrated[target_key] = merged
                elif target_key not in migrated:
                    migrated[target_key] = normalized
            for key, value in list(migrated.items())[:MAX_FACTS]:
                data["facts"][key] = value
            self._drop_stale_daily_facts(data["facts"])

        markers = raw.get("answered_markers")
        if isinstance(markers, list):
            seen: set[str] = set()
            for marker in markers:
                if isinstance(marker, str):
                    normalized = marker.strip()
                    if normalized and normalized not in seen:
                        data["answered_markers"].append(normalized)
                        seen.add(normalized)

        notes = raw.get("notes")
        if isinstance(notes, list):
            collected: list[dict[str, str]] = []
            for entry in notes:
                note = self._normalize_note(entry)
                if not note:
                    notes_cleaned = True
                    continue
                if is_assistant_spam_note(note["text"]) or is_ephemeral_note(note["text"]):
                    notes_cleaned = True
                    continue
                collected.append(note)
            deduped = dedupe_note_entries(collected)
            if len(deduped) != len(collected):
                notes_cleaned = True
            if len(deduped) > MAX_NOTES_STORED:
                deduped = deduped[-MAX_NOTES_STORED:]
                notes_cleaned = True
            data["notes"] = deduped

        topics = raw.get("asked_topics")
        if isinstance(topics, list):
            seen_topics: set[str] = set()
            for topic in topics[-MAX_ASKED_TOPICS:]:
                if isinstance(topic, str):
                    normalized = topic.strip()
                    if normalized and normalized not in seen_topics:
                        data["asked_topics"].append(normalized)
                        seen_topics.add(normalized)

        asked_at = raw.get("topic_asked_at")
        if isinstance(asked_at, dict):
            for topic, stamped in asked_at.items():
                if not isinstance(topic, str) or not isinstance(stamped, str):
                    continue
                normalized = topic.strip()
                day = stamped.strip()
                if not normalized or not day:
                    continue
                try:
                    date.fromisoformat(day)
                except ValueError:
                    continue
                data["topic_asked_at"][normalized] = day
        return data, notes_cleaned

    @classmethod
    def _normalize_stored_fact(cls, key: str, value: Any) -> str | list[str] | None:
        """Normalize one on-disk fact value (string or list for multi keys)."""
        if key in MULTI_VALUE_FACT_KEYS:
            if isinstance(value, str):
                trimmed = value.strip()[:MAX_FACT_VALUE_LEN]
                return trimmed or None
            if isinstance(value, list):
                values = normalize_fact_value_list(value)
                return compact_fact_storage(values)
            return None

        if isinstance(value, str):
            trimmed = value.strip()[:MAX_FACT_VALUE_LEN]
            return trimmed or None
        return None

    @staticmethod
    def _drop_stale_daily_facts(facts: dict[str, Any], *, today: date | None = None) -> bool:
        """Remove undated or non-today daily facts from *facts*. Returns True if changed."""
        moment = today or date.today()
        changed = False
        for key in list(facts):
            if key not in DAILY_FACT_KEYS:
                continue
            raw = facts.get(key)
            if not isinstance(raw, str):
                facts.pop(key, None)
                changed = True
                continue
            parsed = parse_daily_fact(raw)
            if parsed is None or parsed[1] != moment:
                facts.pop(key, None)
                changed = True
        return changed

    def _fresh_daily_value(self, key: str, *, today: date | None = None) -> str | None:
        """Return today's value for a daily fact, clearing stale/undated storage."""
        facts: dict[str, Any] = self._data["facts"]
        raw = facts.get(key)
        if raw is None:
            return None
        if not isinstance(raw, str):
            facts.pop(key, None)
            self.save()
            return None
        parsed = parse_daily_fact(raw)
        moment = today or date.today()
        if parsed is None or parsed[1] != moment:
            facts.pop(key, None)
            self.save()
            return None
        return parsed[0]

    @staticmethod
    def _normalize_note(entry: Any) -> dict[str, str] | None:
        if isinstance(entry, str):
            text = entry.strip()[:MAX_NOTE_LEN]
            if not text:
                return None
            return {"text": text, "source": "chat", "created": date.today().isoformat()}
        if not isinstance(entry, dict):
            return None
        text = str(entry.get("text", "")).strip()[:MAX_NOTE_LEN]
        if not text:
            return None
        source = str(entry.get("source", "chat")).strip() or "chat"
        created = str(entry.get("created", date.today().isoformat())).strip()
        return {"text": text, "source": source, "created": created}

    def get_fact_values(self, key: str) -> list[str]:
        """Return fact values as a list (empty if missing)."""
        if key in DAILY_FACT_KEYS:
            fresh = self._fresh_daily_value(key)
            return [fresh] if fresh else []
        value = self._data["facts"].get(key)
        if value is None:
            return []
        if key in MULTI_VALUE_FACT_KEYS:
            if isinstance(value, list):
                return normalize_fact_value_list(value)
            if isinstance(value, str):
                return split_fact_values(value) or ([value.strip()] if value.strip() else [])
            return []
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    def get_fact(self, key: str) -> str | None:
        """Return a stored fact as a display string, or None."""
        values = self.get_fact_values(key)
        if not values:
            return None
        display = format_fact_values(values)
        return display[:MAX_FACT_VALUE_LEN] if display else None

    def set_fact(self, key: str, value: str) -> None:
        """Store or replace a structured fact (multi-keys parse lists from text)."""
        trimmed_key = key.strip()
        if not trimmed_key or not isinstance(value, str):
            return
        if trimmed_key in MULTI_VALUE_FACT_KEYS:
            values = [
                item
                for item in split_fact_values(value)
                if not should_reject_fact_value(trimmed_key, item)
            ]
            self._write_fact_values(trimmed_key, values, merge=False)
            return

        trimmed_value = value.strip()[:MAX_FACT_VALUE_LEN]
        if not trimmed_value:
            return
        if should_reject_fact_value(trimmed_key, trimmed_value):
            return
        if trimmed_key == "birthday":
            from content.birthday import BIRTHDAY_DECLINED, parse_birthday

            lowered = trimmed_value.casefold()
            if lowered in {BIRTHDAY_DECLINED, "no", "private", "none"}:
                trimmed_value = BIRTHDAY_DECLINED
            else:
                parsed = parse_birthday(trimmed_value)
                if parsed is None:
                    return
                trimmed_value = parsed
        elif trimmed_key == "first_met":
            from content.friendship import parse_first_met

            parsed = parse_first_met(trimmed_value)
            if parsed is None:
                return
            trimmed_value = parsed.isoformat()
        elif trimmed_key == "mood_today":
            lowered = trimmed_value.casefold()
            if lowered in {"good", "great"}:
                trimmed_value = "good"
            elif lowered in {
                "neutral",
                "fine",
                "ok",
                "okay",
                "meh",
                "alright",
                "so-so",
                "average",
            }:
                trimmed_value = "neutral"
            elif lowered in {"bad", "rough", "sad", "awful", "terrible"}:
                trimmed_value = "bad"
            else:
                return
        elif trimmed_key == "energy_today":
            lowered = trimmed_value.casefold()
            if lowered in {"high", "energetic", "full", "good"}:
                trimmed_value = "high"
            elif lowered in {
                "neutral",
                "medium",
                "okay",
                "ok",
                "fine",
                "meh",
                "so-so",
                "average",
            }:
                trimmed_value = "neutral"
            elif lowered in {"low", "tired", "exhausted", "drained"}:
                trimmed_value = "low"
            else:
                return
        elif trimmed_key == "focus_today":
            lowered = trimmed_value.casefold()
            if lowered in {"busy", "packed", "hectic"}:
                trimmed_value = "busy"
            elif lowered in {
                "neutral",
                "normal",
                "okay",
                "ok",
                "mixed",
                "so-so",
                "average",
            }:
                trimmed_value = "neutral"
            elif lowered in {"chill", "free", "relaxed", "calm"}:
                trimmed_value = "chill"
            else:
                return
        elif trimmed_key == "partner_status":
            lowered = trimmed_value.casefold()
            if lowered in {"private", "prefer not", "prefer not to say", "none of your business"}:
                trimmed_value = "private"
        if trimmed_key in DAILY_FACT_KEYS:
            # Leave room for "YYYY-MM-DD|" prefix in storage.
            prefix_budget = 11
            trimmed_value = trimmed_value[: max(1, MAX_FACT_VALUE_LEN - prefix_budget)]
            trimmed_value = format_daily_fact(trimmed_value)
        facts: dict[str, Any] = self._data["facts"]
        if trimmed_key not in facts and len(facts) >= MAX_FACTS:
            return
        facts[trimmed_key] = trimmed_value
        self.save()

    def merge_fact_values(self, key: str, values: list[str]) -> None:
        """Append values to a multi-value fact (no-op for singular keys)."""
        trimmed_key = key.strip()
        if trimmed_key not in MULTI_VALUE_FACT_KEYS:
            if values:
                self.set_fact(trimmed_key, values[0])
            return
        self._write_fact_values(trimmed_key, values, merge=True)

    def replace_fact_values(self, key: str, values: list[str]) -> None:
        """Replace a multi-value fact with an explicit list of values."""
        trimmed_key = key.strip()
        if trimmed_key not in MULTI_VALUE_FACT_KEYS:
            if values:
                self.set_fact(trimmed_key, values[0])
            return
        self._write_fact_values(trimmed_key, values, merge=False)

    def remove_fact_value(self, key: str, value: str) -> bool:
        """Remove one item from a multi-value fact. Returns True if something changed."""
        trimmed_key = key.strip()
        if trimmed_key not in MULTI_VALUE_FACT_KEYS:
            return False
        target = value.strip().casefold()
        if not target:
            return False
        existing = self.get_fact_values(trimmed_key)
        remaining = [item for item in existing if item.casefold() != target]
        if len(remaining) == len(existing):
            return False
        facts: dict[str, Any] = self._data["facts"]
        if not remaining:
            facts.pop(trimmed_key, None)
            self.save()
            return True
        stored = compact_fact_storage(remaining)
        if stored is None:
            facts.pop(trimmed_key, None)
        else:
            facts[trimmed_key] = stored
        self.save()
        return True

    def delete_fact(self, key: str) -> bool:
        """Remove an entire fact key. Returns True if something changed."""
        trimmed_key = key.strip()
        if not trimmed_key:
            return False
        facts: dict[str, Any] = self._data["facts"]
        if trimmed_key not in facts:
            return False
        facts.pop(trimmed_key, None)
        self.save()
        return True

    def _write_fact_values(self, key: str, values: list[str], *, merge: bool) -> None:
        cleaned = normalize_fact_value_list(values)
        if not cleaned:
            return
        facts: dict[str, Any] = self._data["facts"]
        if key not in facts and len(facts) >= MAX_FACTS:
            return

        if merge:
            existing = self.get_fact_values(key)
            seen = {item.casefold() for item in existing}
            merged = list(existing)
            for item in cleaned:
                if item.casefold() in seen:
                    continue
                seen.add(item.casefold())
                merged.append(item)
            cleaned = normalize_fact_value_list(merged)

        stored = compact_fact_storage(cleaned)
        if stored is None:
            return
        facts[key] = stored
        self.save()

    def mark_answered(self, marker: str) -> None:
        """Record that a dialog marker question was answered."""
        normalized = marker.strip()
        if not normalized:
            return
        markers: list[str] = self._data["answered_markers"]
        if normalized not in markers:
            markers.append(normalized)
            self.save()

    def is_answered(self, marker: str) -> bool:
        """Return whether a dialog marker was already answered."""
        normalized = marker.strip()
        return normalized in self._data["answered_markers"]

    def is_question_answered(self, question_text: str) -> bool:
        """Return True if any answered marker appears in *question_text*."""
        lower = question_text.lower()
        for marker in self._data["answered_markers"]:
            if isinstance(marker, str) and marker.lower() in lower:
                return True
        return False

    def is_topic_asked(self, topic: str) -> bool:
        """Return whether a memory-question topic was already asked."""
        normalized = topic.strip()
        return normalized in self._data["asked_topics"]

    def is_topic_on_cooldown(self, topic: str, *, days: int, today: date | None = None) -> bool:
        """Return True when *topic* was asked fewer than *days* ago.

        Topics without a stored ask-date are treated as not on cooldown so older
        verify questions can be asked again after this feature was added.
        """
        if days <= 0:
            return False
        normalized = topic.strip()
        if not normalized:
            return False
        asked_at = self._data.get("topic_asked_at")
        if not isinstance(asked_at, dict):
            return False
        stamped = asked_at.get(normalized)
        if not isinstance(stamped, str) or not stamped.strip():
            return False
        try:
            last = date.fromisoformat(stamped.strip())
        except ValueError:
            return False
        moment = today or date.today()
        return (moment - last).days < days

    def mark_topic_asked(self, topic: str, *, today: date | None = None) -> None:
        """Record that an interactive memory question topic was used."""
        normalized = topic.strip()
        if not normalized:
            return
        topics: list[str] = self._data["asked_topics"]
        if normalized not in topics:
            topics.append(normalized)
            if len(topics) > MAX_ASKED_TOPICS:
                del topics[0]
        asked_at = self._data.setdefault("topic_asked_at", {})
        if not isinstance(asked_at, dict):
            asked_at = {}
            self._data["topic_asked_at"] = asked_at
        asked_at[normalized] = (today or date.today()).isoformat()
        self.save()

    def asked_topics_list(self) -> list[str]:
        """Return a copy of asked memory-question topics."""
        return list(self._data["asked_topics"])

    def facts_dict(self) -> dict[str, str]:
        """Return facts as display strings for template formatting."""
        facts = self._data.get("facts")
        if not isinstance(facts, dict):
            return {}
        result: dict[str, str] = {}
        for key in facts:
            if not isinstance(key, str):
                continue
            display = self.get_fact(key)
            if display:
                result[key] = display
        return result

    def has_any_memory(self) -> bool:
        """Return True when facts or notes exist."""
        return bool(self._data["facts"] or self._data["notes"])

    def add_note(self, text: str, *, source: str = "chat") -> bool:
        """Append a note, or upgrade a near-duplicate when the new text is richer."""
        trimmed = text.strip()[:MAX_NOTE_LEN]
        if not trimmed or not is_storable_note(trimmed, source=source):
            return False
        notes: list[dict[str, str]] = self._data["notes"]
        duplicate_index = find_near_duplicate_note_index(trimmed, notes)
        if duplicate_index is not None:
            existing_text = notes[duplicate_index].get("text", "")
            if not isinstance(existing_text, str) or not is_meaningfully_richer_note(
                trimmed, existing_text
            ):
                return False
            notes[duplicate_index] = {
                "text": trimmed,
                "source": source.strip() or "chat",
                "created": notes[duplicate_index].get("created") or date.today().isoformat(),
            }
            self.save()
            return True
        notes.append(
            {
                "text": trimmed,
                "source": source.strip() or "chat",
                "created": date.today().isoformat(),
            }
        )
        self.save()
        return True

    def add_notes(self, texts: list[str], *, source: str = "chat", max_new: int = MAX_NEW_NOTES_PER_TURN) -> int:
        """Add up to *max_new* notes; return how many were stored."""
        added = 0
        for text in texts:
            if added >= max_new:
                break
            if self.add_note(text, source=source):
                added += 1
        return added

    def remove_note(self, text: str) -> bool:
        """Remove the first note matching *text*."""
        trimmed = text.strip()
        if not trimmed:
            return False
        notes: list[dict[str, str]] = self._data["notes"]
        for index, note in enumerate(notes):
            if note.get("text") == trimmed:
                del notes[index]
                self.save()
                return True
        return False

    def notes_list(self) -> list[dict[str, str]]:
        """Return a shallow copy of stored notes for UI display."""
        notes: list[dict[str, str]] = self._data.get("notes") or []
        return [dict(note) for note in notes if isinstance(note, dict)]

    def replace_notes(self, texts: list[str], *, source: str = "editor") -> None:
        """Replace all notes with *texts* (empty strings skipped) and save once."""
        cleaned: list[dict[str, str]] = []
        today = date.today().isoformat()
        seen: set[str] = set()
        for text in texts:
            trimmed = text.strip()[:MAX_NOTE_LEN]
            if not trimmed:
                continue
            key = trimmed.casefold()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(
                {
                    "text": trimmed,
                    "source": source.strip() or "editor",
                    "created": today,
                }
            )
            if len(cleaned) >= MAX_NOTES_STORED:
                break
        self._data["notes"] = cleaned
        self.save()

    def apply_extraction(
        self,
        *,
        add_notes: list[str] | None = None,
        remove_notes: list[str] | None = None,
        update_facts: dict[str, Any] | None = None,
        allowed_fact_keys: frozenset[str] | None = None,
    ) -> None:
        """Apply validated memory updates from the chat extractor."""
        changed = False
        if update_facts:
            for key, raw in update_facts.items():
                if allowed_fact_keys is not None and key not in allowed_fact_keys:
                    continue
                facts: dict[str, Any] = self._data["facts"]
                if key in PROTECTED_FACT_KEYS and facts.get(key):
                    continue
                if key not in facts and len(facts) >= MAX_FACTS:
                    continue

                intent, value = self._split_extraction_claim(key, raw)
                if intent is None:
                    continue

                if key in MULTI_VALUE_FACT_KEYS:
                    items = (
                        normalize_fact_value_list(value)
                        if isinstance(value, list)
                        else split_fact_values(value)
                        if isinstance(value, str)
                        else []
                    )
                    cleaned = [item for item in items if not should_reject_fact_value(key, item)]
                    if not cleaned:
                        continue
                    before = facts.get(key)
                    if intent == "replace":
                        self.replace_fact_values(key, cleaned)
                    elif intent == "add":
                        self.merge_fact_values(key, cleaned)
                    elif intent == "remove":
                        for item in cleaned:
                            self.remove_fact_value(key, item)
                    if facts.get(key) != before:
                        changed = True
                    continue

                if not isinstance(value, str):
                    continue
                if intent == "remove":
                    current = self.get_fact(key)
                    if (
                        current
                        and current.casefold() == value.strip().casefold()
                        and self.delete_fact(key)
                    ):
                        changed = True
                    continue
                if intent == "add" and facts.get(key):
                    continue
                if key in DAILY_FACT_KEYS:
                    before = facts.get(key)
                    self.set_fact(key, value)
                    if facts.get(key) != before:
                        changed = True
                    continue
                trimmed = value.strip()[:MAX_FACT_VALUE_LEN]
                if not trimmed or should_reject_fact_value(key, trimmed):
                    continue
                facts[key] = trimmed
                changed = True

        if remove_notes:
            for text in remove_notes:
                if self.remove_note(text):
                    changed = True

        if add_notes:
            before = len(self._data["notes"])
            self.add_notes(add_notes)
            if len(self._data["notes"]) != before:
                changed = True

        if changed:
            self.save()

    @staticmethod
    def _split_extraction_claim(key: str, raw: Any) -> tuple[str | None, Any]:
        """Return (intent, value) for an extraction claim; legacy strings/lists supported."""
        if isinstance(raw, dict):
            intent_raw = raw.get("intent")
            intent = intent_raw.strip().casefold() if isinstance(intent_raw, str) else ""
            if intent not in {"add", "replace", "remove"}:
                return None, None
            return intent, raw.get("value")
        if key in MULTI_VALUE_FACT_KEYS:
            if isinstance(raw, list):
                return "replace", raw
            if isinstance(raw, str):
                return "add", raw
            return None, None
        if isinstance(raw, str):
            return "replace", raw
        return None, None

    def as_facts_prompt_block(self) -> str:
        """Return only structured facts for short AI generation prompts."""
        facts = self.facts_dict()
        if not facts:
            return ""
        fact_lines = [f"- {key.replace('_', ' ')}: {value}" for key, value in facts.items()]
        block = "Known facts about the user:\n" + "\n".join(fact_lines)
        if len(block) <= MAX_FACTS_PROMPT_CHARS:
            return block
        return block[: MAX_FACTS_PROMPT_CHARS - 3].rstrip() + "..."

    def _sample_notes_for_prompt(self, notes: list[dict[str, str]]) -> list[dict[str, str]]:
        """Pick recent notes plus a day-stable random sample of older notes."""
        if not notes:
            return []
        recent_n = min(MAX_NOTES_RECENT_IN_PROMPT, MAX_NOTES_IN_PROMPT, len(notes))
        recent = notes[-recent_n:]
        if len(notes) <= recent_n:
            return recent
        older = notes[:-recent_n]
        need = max(0, MAX_NOTES_IN_PROMPT - len(recent))
        if need <= 0 or not older:
            return recent
        rng = random.Random(date.today().isoformat())
        if len(older) <= need:
            sampled = list(older)
        else:
            sampled = rng.sample(older, need)
        # Keep chronological order among the selected notes.
        selected = {id(note) for note in sampled} | {id(note) for note in recent}
        return [note for note in notes if id(note) in selected]

    def as_prompt_block(self) -> str:
        """Return a compact memory summary for LLM system/generation prompts."""
        parts: list[str] = []
        facts_block = self.as_facts_prompt_block()
        if facts_block:
            parts.append(facts_block)

        notes: list[dict[str, str]] = self._data["notes"]
        if notes:
            selected = self._sample_notes_for_prompt(notes)
            recent_ids = {id(note) for note in notes[-MAX_NOTES_RECENT_IN_PROMPT:]}
            recent_selected = [note for note in selected if id(note) in recent_ids]
            older_selected = [note for note in selected if id(note) not in recent_ids]
            # Fit recent notes first so the char budget cannot drop them for older ones.
            note_lines: list[str] = []
            notes_budget = MAX_NOTES_PROMPT_CHARS
            used = len("Additional notes:\n")
            for note in recent_selected + older_selected:
                text = note.get("text")
                if not text:
                    continue
                line = f"- {text}"
                if used + len(line) + 1 > notes_budget and note_lines:
                    break
                note_lines.append(line)
                used += len(line) + 1
            if note_lines:
                parts.append("Additional notes:\n" + "\n".join(note_lines))

        if not parts:
            return ""

        block = "\n\n".join(parts)
        if len(block) <= MAX_PROMPT_BLOCK_CHARS:
            return block
        return block[: MAX_PROMPT_BLOCK_CHARS - 3].rstrip() + "..."

    def as_spoken_summary(self) -> str:
        """Return a short spoken summary for the remember-me menu action."""
        block = self.as_prompt_block()
        if block:
            return block.replace("\n", " ")
        return "I don't have anything saved about you yet. Tell me about yourself!"

    def user_display_name(self, fallback: str = "You") -> str:
        """Return one of the user's names for chat labels (random if several)."""
        names = self.get_fact_values("user_names")
        if not names:
            return fallback
        return random.choice(names)

    def pick_user_name(self, fallback: str | None = None) -> str | None:
        """Return a random stored user name, or *fallback* / None."""
        names = self.get_fact_values("user_names")
        if names:
            return random.choice(names)
        return fallback

    def snapshot(self) -> dict[str, Any]:
        """Return a deep copy of the in-memory data (for tests)."""
        return deepcopy(self._data)
