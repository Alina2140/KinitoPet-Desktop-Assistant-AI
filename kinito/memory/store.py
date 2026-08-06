"""File-backed user memory store (facts, answered questions, chat notes)."""

from __future__ import annotations

import json
import os
import random
import sys
from copy import deepcopy
from datetime import date
from typing import Any

from content.memory_keys import (
    LEGACY_FACT_KEY_ALIASES,
    MULTI_VALUE_FACT_KEYS,
    PROTECTED_FACT_KEYS,
)
from kinito.assets import user_media_directory
from kinito.memory.fact_values import (
    compact_fact_storage,
    format_fact_values,
    normalize_fact_value_list,
    split_fact_values,
)
from kinito.memory.validation import is_duplicate_of_existing_note, is_storable_note

MEMORY_VERSION = 1
MEMORY_FILENAME = "memory.json"
NOTES_FILENAME = "notes.txt"

MAX_FACTS = 50
MAX_FACT_VALUE_LEN = 80
MAX_NOTES_STORED = 50
MAX_NOTES_IN_PROMPT = 20
MAX_NOTE_LEN = 120
MAX_PROMPT_BLOCK_CHARS = 800
MAX_NEW_NOTES_PER_TURN = 1
MAX_ASKED_TOPICS = 100


def memory_file_path(directory: str | None = None) -> str:
    """Return the path to the JSON memory file."""
    base = directory or user_media_directory
    return os.path.join(base, MEMORY_FILENAME)


def notes_file_path(directory: str | None = None) -> str:
    """Return the path to the human-readable notes mirror file."""
    base = directory or user_media_directory
    return os.path.join(base, NOTES_FILENAME)


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


class MemoryStore:
    """Load, update, and persist user memory under GameAssets/UserMedia/."""

    def __init__(self, directory: str | None = None) -> None:
        self._directory = directory or user_media_directory
        self._path = memory_file_path(self._directory)
        self._notes_path = notes_file_path(self._directory)
        self._data: dict[str, Any] = self._empty_data()
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
        except (OSError, json.JSONDecodeError, TypeError):
            self._data = self._empty_data()
            return
        if not isinstance(raw, dict):
            self._data = self._empty_data()
            return
        self._data = self._normalize_loaded(raw)

    def save(self) -> None:
        """Persist memory atomically and refresh the notes mirror file."""
        os.makedirs(self._directory, exist_ok=True)
        temp_path = f"{self._path}.tmp"
        payload = json.dumps(self._data, ensure_ascii=False, indent=2)
        with open(temp_path, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        _atomic_replace(temp_path, self._path)
        self._write_notes_mirror()

    def reset(self) -> None:
        """Clear all memory and remove persisted files."""
        self._data = self._empty_data()
        for path in (self._path, self._notes_path):
            if os.path.isfile(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def _normalize_loaded(self, raw: dict[str, Any]) -> dict[str, Any]:
        data = self._empty_data()
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
            for entry in notes[-MAX_NOTES_STORED:]:
                note = self._normalize_note(entry)
                if note:
                    data["notes"].append(note)

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
        return data

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
            values = split_fact_values(value)
            self._write_fact_values(trimmed_key, values, merge=False)
            return

        trimmed_value = value.strip()[:MAX_FACT_VALUE_LEN]
        if not trimmed_value:
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
            if lowered in {"good", "great", "fine", "ok", "okay"}:
                trimmed_value = "good"
            elif lowered in {"bad", "rough", "sad", "awful", "terrible"}:
                trimmed_value = "bad"
            else:
                return
        elif trimmed_key == "energy_today":
            lowered = trimmed_value.casefold()
            if lowered in {"high", "energetic", "full", "good"}:
                trimmed_value = "high"
            elif lowered in {"low", "tired", "exhausted", "drained"}:
                trimmed_value = "low"
            else:
                return
        elif trimmed_key == "focus_today":
            lowered = trimmed_value.casefold()
            if lowered in {"busy", "packed", "hectic"}:
                trimmed_value = "busy"
            elif lowered in {"chill", "free", "relaxed", "calm"}:
                trimmed_value = "chill"
            else:
                return
        elif trimmed_key == "partner_status":
            lowered = trimmed_value.casefold()
            if lowered in {"private", "prefer not", "prefer not to say", "none of your business"}:
                trimmed_value = "private"
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
        """Append a note if under limits and not a duplicate."""
        trimmed = text.strip()[:MAX_NOTE_LEN]
        if not trimmed or not is_storable_note(trimmed, source=source):
            return False
        notes: list[dict[str, str]] = self._data["notes"]
        if is_duplicate_of_existing_note(trimmed, notes):
            return False
        if len(notes) >= MAX_NOTES_STORED:
            del notes[0]
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
            for key, value in update_facts.items():
                if allowed_fact_keys is not None and key not in allowed_fact_keys:
                    continue
                facts: dict[str, Any] = self._data["facts"]
                if key in PROTECTED_FACT_KEYS and facts.get(key):
                    continue
                if key not in facts and len(facts) >= MAX_FACTS:
                    continue

                if key in MULTI_VALUE_FACT_KEYS:
                    if isinstance(value, list):
                        # Explicit list = full replacement (user corrected the set).
                        before = facts.get(key)
                        self.replace_fact_values(key, normalize_fact_value_list(value))
                        if facts.get(key) != before:
                            changed = True
                    elif isinstance(value, str):
                        before = facts.get(key)
                        # Plain string adds/merges newly mentioned items.
                        self.merge_fact_values(key, split_fact_values(value))
                        if facts.get(key) != before:
                            changed = True
                    continue

                if not isinstance(value, str):
                    continue
                trimmed = value.strip()[:MAX_FACT_VALUE_LEN]
                if not trimmed:
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

    def as_facts_prompt_block(self) -> str:
        """Return only structured facts for short AI generation prompts."""
        facts = self.facts_dict()
        if not facts:
            return ""
        fact_lines = [f"- {key.replace('_', ' ')}: {value}" for key, value in facts.items()]
        block = "Known facts about the user:\n" + "\n".join(fact_lines)
        if len(block) <= MAX_PROMPT_BLOCK_CHARS:
            return block
        return block[: MAX_PROMPT_BLOCK_CHARS - 3].rstrip() + "..."

    def as_prompt_block(self) -> str:
        """Return a compact memory summary for LLM system/generation prompts."""
        parts: list[str] = []
        facts_block = self.as_facts_prompt_block()
        if facts_block:
            parts.append(facts_block)

        notes: list[dict[str, str]] = self._data["notes"]
        if notes:
            recent = notes[-MAX_NOTES_IN_PROMPT:]
            note_lines = [f"- {note['text']}" for note in recent if note.get("text")]
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

    def _write_notes_mirror(self) -> None:
        notes: list[dict[str, str]] = self._data["notes"]
        lines = [f"- {note['text']}" for note in notes if note.get("text")]
        os.makedirs(self._directory, exist_ok=True)
        content = "\n".join(lines)
        if content:
            content += "\n"
        temp_path = f"{self._notes_path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        _atomic_replace(temp_path, self._notes_path)

    def snapshot(self) -> dict[str, Any]:
        """Return a deep copy of the in-memory data (for tests)."""
        return deepcopy(self._data)
