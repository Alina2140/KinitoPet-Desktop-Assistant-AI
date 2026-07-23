"""User memory initialization and menu actions."""

from __future__ import annotations

from content import dialogue as dlg
from content.memory_keys import ALLOWED_FACT_KEYS, PROTECTED_FACT_KEYS
from kinito.memory.questions import SAVE_AS_NOTE, MemoryQuestion
from kinito.memory.store import MemoryStore


class MemoryMixin:
    """Load persistent memory and expose remember/forget actions."""

    def _init_memory(self) -> None:
        """Create the on-disk memory store (call from app __init__)."""
        self._memory = MemoryStore()
        self._pending_memory_question: MemoryQuestion | None = None
        self._planning_memory_question = False

    def show_memory_summary(self) -> None:
        """Speak what Kinito currently remembers about the user."""
        summary = self._memory.as_spoken_summary()
        if not self._memory.as_prompt_block():
            summary = dlg.MEMORY_EMPTY_LINE
        self.speak(summary, skip_ai=True, long_bubble=True)

    def forget_memory(self) -> None:
        """Clear all saved memory and confirm to the user."""
        self._memory.reset()
        self._pending_memory_question = None
        self.speak(dlg.MEMORY_FORGOTTEN_LINE, skip_ai=True)

    def memory_prompt_block(self) -> str:
        """Return memory text for LLM chat prompts, or empty string."""
        return self._memory.as_prompt_block()

    def facts_prompt_block(self) -> str:
        """Return structured facts only (for idle / line replacement)."""
        return self._memory.as_facts_prompt_block()

    def chat_user_label(self) -> str:
        """Return the display label for chat messages from the user."""
        return self._memory.user_display_name()

    def ask_memory_question(self, spec: MemoryQuestion) -> None:
        """Speak an interactive memory question with textbox or yes/no UI."""
        self._pending_memory_question = spec
        self.speak(spec.question, 45, True, skip_ai=True)

    def _handle_memory_question_response(self, response: str) -> None:
        """Persist the user's answer to a pending memory question."""
        spec = self._pending_memory_question
        self._pending_memory_question = None
        if spec is None:
            return

        answer = self._normalize_memory_answer(response, spec.ui)
        if not answer:
            return

        self._persist_memory_answer(spec, answer)
        self._memory.mark_topic_asked(spec.topic)
        self.speak(dlg.pick_line(dlg.MEMORY_ANSWER_ACK_LINES), skip_ai=True)

    @staticmethod
    def _normalize_memory_answer(response: str, ui: str) -> str:
        """Normalize a textbox or yes/no answer for storage."""
        if ui == "yes_no":
            if response == dlg.BUTTON_YES:
                return "yes"
            if response == dlg.BUTTON_NO:
                return "no"
            return ""
        return response.strip()

    def _persist_memory_answer(self, spec: MemoryQuestion, answer: str) -> None:
        """Store a memory-question answer as a note or structured fact."""
        if (
            spec.save_as != SAVE_AS_NOTE
            and spec.save_as in ALLOWED_FACT_KEYS
            and spec.save_as not in PROTECTED_FACT_KEYS
        ):
            self._memory.set_fact(spec.save_as, answer)
            return

        note = self._compact_memory_note(spec, answer)
        self._memory.add_note(note, source="question")

    @staticmethod
    def _compact_memory_note(spec: MemoryQuestion, answer: str) -> str:
        """Build a short note summarizing the Q&A pair."""
        question = spec.question.strip()
        if len(question) > 60:
            question = f"{question[:57]}..."
        return f"{spec.topic}: {answer} ({question})"
