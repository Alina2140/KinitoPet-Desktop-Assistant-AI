"""Plan interactive memory questions via Ollama or scripted templates."""

from __future__ import annotations

import json
import re
from typing import Any

from content import llm_prompts as prompts
from content.memory_followups import pick_template_followup
from kinito.llm.ollama_client import OllamaClient, OllamaUnavailableError
from kinito.memory.questions import SAVE_AS_NOTE, MemoryQuestion
from kinito.memory.store import MemoryStore

_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")
_VALID_UI = frozenset({"textbox", "yes_no"})


def parse_question_plan(raw: str) -> dict[str, Any]:
    """Parse JSON from an Ollama question-planning reply."""
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


def normalize_question_plan(payload: dict[str, Any]) -> MemoryQuestion | None:
    """Validate planner JSON and return a MemoryQuestion, or None."""
    question = str(payload.get("question", "")).strip()
    if not question or "?" not in question:
        return None

    ui = str(payload.get("ui", "textbox")).strip().lower()
    if ui not in _VALID_UI:
        ui = "textbox"

    topic = str(payload.get("topic", "")).strip()
    if not topic:
        topic = f"ai_{hash(question) & 0xFFFF:x}"

    save_as = str(payload.get("save_as", SAVE_AS_NOTE)).strip()
    if save_as != SAVE_AS_NOTE:
        save_as = SAVE_AS_NOTE

    return MemoryQuestion(question=question, ui=ui, topic=topic, save_as=save_as)


class MemoryQuestionPlanner:
    """Ask Ollama for a new interactive question based on user memory."""

    def __init__(self, client: OllamaClient, store: MemoryStore) -> None:
        self._client = client
        self._store = store

    def plan(self) -> MemoryQuestion | None:
        """Return a new AI-planned question, or None to fall back to templates."""
        if not self._store.as_prompt_block():
            return None

        asked = self._store.asked_topics_list()
        prompt = prompts.MEMORY_QUESTION_PLAN_PROMPT.format(
            known_facts=self._store.as_prompt_block(),
            asked_topics=", ".join(asked) if asked else "(none yet)",
        )
        try:
            raw = self._client.generate(
                prompt,
                system=prompts.MEMORY_QUESTION_PLAN_SYSTEM,
                max_tokens=220,
            )
        except OllamaUnavailableError:
            return None

        spec = normalize_question_plan(parse_question_plan(raw))
        if spec is None:
            return None
        if self._store.is_topic_asked(spec.topic):
            return None
        return spec

    def plan_template(self) -> MemoryQuestion | None:
        """Return a scripted template follow-up, if any."""
        return pick_template_followup(self._store)
