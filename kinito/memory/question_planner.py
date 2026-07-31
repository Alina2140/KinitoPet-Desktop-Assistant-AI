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
_ASKED_TOPICS_PROMPT_LIMIT = 40
_OPEN_STARTERS = re.compile(
    r"^(what|which|where|when|how|why|who|if|tell me|describe|name)\b",
    re.IGNORECASE,
)
_YES_NO_STARTERS = re.compile(
    r"^(is|are|am|do|does|did|have|has|had|can|could|will|would|should|"
    r"may|might|was|were|aren't|isn't|don't|doesn't)\b",
    re.IGNORECASE,
)
_TOPIC_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "to",
        "of",
        "in",
        "on",
        "for",
        "and",
        "or",
        "you",
        "your",
        "me",
        "my",
        "i",
        "we",
        "our",
        "is",
        "are",
        "do",
        "does",
        "did",
        "be",
        "been",
        "being",
        "with",
        "at",
        "from",
        "as",
        "into",
        "about",
        "just",
        "still",
        "any",
        "some",
        "that",
        "this",
        "these",
        "those",
    }
)


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


def coerce_question_ui(question: str, ui: str) -> str:
    """Force textbox when the question cannot sensibly be answered yes/no."""
    requested = ui.strip().lower() if ui else "textbox"
    if requested not in _VALID_UI:
        requested = "textbox"

    lower = question.strip().lower()
    if "would you rather" in lower or "would you prefer" in lower:
        return "textbox"
    if _OPEN_STARTERS.match(lower):
        return "textbox"
    # A-or-B choice questions need a typed answer, not Yes/No.
    if " or " in lower:
        return "textbox"
    if requested == "yes_no" and _YES_NO_STARTERS.match(lower) and "rather" not in lower:
        return "yes_no"
    return "textbox"


def _topic_from_question(question: str) -> str:
    """Build a readable snake_case topic id from question text."""
    words = re.findall(r"[a-z0-9]+", question.lower())
    keep = [word for word in words if word not in _TOPIC_STOPWORDS and len(word) > 1]
    if not keep:
        return f"ai_{hash(question) & 0xFFFF:x}"
    base = "_".join(keep[:5])[:48].strip("_")
    return base or f"ai_{hash(question) & 0xFFFF:x}"


def _unique_topic(store: MemoryStore, topic: str, question: str) -> str:
    """Return *topic*, or a reminted readable id when that topic was already asked."""
    candidate = re.sub(r"[^a-z0-9_]+", "_", topic.strip().lower()).strip("_")
    if not candidate:
        candidate = _topic_from_question(question)
    if not store.is_topic_asked(candidate):
        return candidate
    reminted = _topic_from_question(question)
    if not store.is_topic_asked(reminted):
        return reminted
    suffix = f"{hash(question) & 0xFFFF:x}"
    for index in range(2, 50):
        alt = f"{reminted}_{suffix}" if index == 2 else f"{reminted}_{suffix}_{index}"
        if not store.is_topic_asked(alt):
            return alt
    return f"{reminted}_{hash(question) & 0xFFFFFF:x}"


def normalize_question_plan(payload: dict[str, Any]) -> MemoryQuestion | None:
    """Validate planner JSON and return a MemoryQuestion, or None."""
    question = str(payload.get("question", "")).strip()
    if not question or "?" not in question:
        return None

    ui = coerce_question_ui(question, str(payload.get("ui", "textbox")))

    topic = str(payload.get("topic", "")).strip()
    if not topic:
        topic = _topic_from_question(question)

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
        asked = self._store.asked_topics_list()
        # Keep the prompt short; oldest topics are still blocked via reminting.
        asked_for_prompt = asked[-_ASKED_TOPICS_PROMPT_LIMIT:]
        known = self._store.as_prompt_block() or "(none yet — invent a completely open question)"
        prompt = prompts.MEMORY_QUESTION_PLAN_PROMPT.format(
            time_context=prompts.local_time_context(include_special_day=True),
            known_facts=known,
            asked_topics=", ".join(asked_for_prompt) if asked_for_prompt else "(none yet)",
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
        unique_topic = _unique_topic(self._store, spec.topic, spec.question)
        if unique_topic == spec.topic:
            return spec
        return MemoryQuestion(
            question=spec.question,
            ui=spec.ui,
            topic=unique_topic,
            save_as=spec.save_as,
        )

    def plan_template(self) -> MemoryQuestion | None:
        """Return a scripted template follow-up, if any."""
        return pick_template_followup(self._store)
