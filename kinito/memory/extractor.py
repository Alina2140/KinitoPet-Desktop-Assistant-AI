"""Extract durable memory updates from chat turns via Ollama."""

from __future__ import annotations

import json
import re
from typing import Any

from content import llm_prompts as prompts
from content.memory_keys import ALLOWED_FACT_KEYS
from kinito.llm.ollama_client import OllamaClient, OllamaUnavailableError
from kinito.memory.store import MAX_NEW_NOTES_PER_TURN, MemoryStore
from kinito.memory.validation import is_storable_note

_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")


def parse_extraction_response(raw: str) -> dict[str, Any]:
    """Parse JSON from an Ollama extraction reply."""
    text = raw.strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = _JSON_BLOCK_RE.search(text)
    if not match:
        return {}
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def normalize_extraction(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and trim extractor JSON before applying to the store."""
    result: dict[str, Any] = {
        "add_notes": [],
        "remove_notes": [],
        "update_facts": {},
    }

    add_notes = payload.get("add_notes")
    if isinstance(add_notes, list):
        for item in add_notes[:MAX_NEW_NOTES_PER_TURN]:
            if isinstance(item, str):
                trimmed = item.strip()
                if trimmed and is_storable_note(trimmed, source="chat"):
                    result["add_notes"].append(trimmed)

    remove_notes = payload.get("remove_notes")
    if isinstance(remove_notes, list):
        for item in remove_notes:
            if isinstance(item, str) and item.strip():
                result["remove_notes"].append(item.strip())

    update_facts = payload.get("update_facts")
    if isinstance(update_facts, dict):
        for key, value in update_facts.items():
            if isinstance(key, str) and key in ALLOWED_FACT_KEYS and isinstance(value, str):
                trimmed = value.strip()
                if trimmed:
                    result["update_facts"][key] = trimmed

    return result


class MemoryExtractor:
    """Ask Ollama what to remember from a single chat exchange."""

    def __init__(self, client: OllamaClient, store: MemoryStore) -> None:
        self._client = client
        self._store = store

    def extract_from_turn(self, user_text: str, assistant_text: str) -> None:
        """Run extraction and apply validated updates to *store*."""
        prompt = prompts.MEMORY_EXTRACT_PROMPT.format(
            user_text=user_text.strip(),
            assistant_text=assistant_text.strip(),
            known_facts=self._store.as_prompt_block() or "(none yet)",
        )
        try:
            raw = self._client.generate(
                prompt,
                system=prompts.MEMORY_EXTRACT_SYSTEM,
                max_tokens=220,
            )
        except OllamaUnavailableError:
            return

        payload = normalize_extraction(parse_extraction_response(raw))
        if not any(payload[key] for key in ("add_notes", "remove_notes", "update_facts")):
            return
        self._store.apply_extraction(
            add_notes=payload["add_notes"],
            remove_notes=payload["remove_notes"],
            update_facts=payload["update_facts"],
            allowed_fact_keys=ALLOWED_FACT_KEYS,
        )
