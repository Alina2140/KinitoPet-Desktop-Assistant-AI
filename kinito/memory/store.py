"""File-backed user memory store (facts, answered questions, chat notes)."""

from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from datetime import date
from typing import Any

from content.memory_keys import PROTECTED_FACT_KEYS
from kinito.assets import user_media_directory
from kinito.memory.validation import is_duplicate_of_existing_note, is_storable_note

MEMORY_VERSION = 1
MEMORY_FILENAME = "memory.json"
NOTES_FILENAME = "notes.txt"

MAX_FACTS = 20
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
            for key, value in list(facts.items())[:MAX_FACTS]:
                if isinstance(key, str) and isinstance(value, str):
                    trimmed = value.strip()[:MAX_FACT_VALUE_LEN]
                    if trimmed:
                        data["facts"][key] = trimmed

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
        return data

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

    def get_fact(self, key: str) -> str | None:
        """Return a stored fact value or None."""
        value = self._data["facts"].get(key)
        return value if isinstance(value, str) else None

    def set_fact(self, key: str, value: str) -> None:
        """Store or update a structured fact."""
        trimmed_key = key.strip()
        trimmed_value = value.strip()[:MAX_FACT_VALUE_LEN]
        if not trimmed_key or not trimmed_value:
            return
        facts: dict[str, str] = self._data["facts"]
        if trimmed_key not in facts and len(facts) >= MAX_FACTS:
            return
        facts[trimmed_key] = trimmed_value
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

    def mark_topic_asked(self, topic: str) -> None:
        """Record that an interactive memory question topic was used."""
        normalized = topic.strip()
        if not normalized:
            return
        topics: list[str] = self._data["asked_topics"]
        if normalized in topics:
            return
        topics.append(normalized)
        if len(topics) > MAX_ASKED_TOPICS:
            del topics[0]
        self.save()

    def asked_topics_list(self) -> list[str]:
        """Return a copy of asked memory-question topics."""
        return list(self._data["asked_topics"])

    def facts_dict(self) -> dict[str, str]:
        """Return a shallow copy of stored facts for template formatting."""
        facts = self._data.get("facts")
        if not isinstance(facts, dict):
            return {}
        return {key: value for key, value in facts.items() if isinstance(key, str) and isinstance(value, str)}

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
        update_facts: dict[str, str] | None = None,
        allowed_fact_keys: frozenset[str] | None = None,
    ) -> None:
        """Apply validated memory updates from the chat extractor."""
        changed = False
        if update_facts:
            for key, value in update_facts.items():
                if allowed_fact_keys is not None and key not in allowed_fact_keys:
                    continue
                if not isinstance(value, str):
                    continue
                trimmed = value.strip()[:MAX_FACT_VALUE_LEN]
                if not trimmed:
                    continue
                facts: dict[str, str] = self._data["facts"]
                if key in PROTECTED_FACT_KEYS and facts.get(key):
                    continue
                if key not in facts and len(facts) >= MAX_FACTS:
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
        facts: dict[str, str] = self._data["facts"]
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
        """Return the user's preferred name for chat labels."""
        return self.get_fact("user_name") or fallback

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
