"""Ollama-powered chat and AI-enhanced speech for Kinito."""

from __future__ import annotations

import random
import threading

from content import dialogue as dlg
from content import llm_prompts as prompts
from content.dialog_registry import find_dialog_spec
from kinito.features.memory import MemoryMixin
from kinito.llm.config import LLMConfig
from kinito.llm.conversation import ConversationHistory
from kinito.llm.ollama_client import OllamaClient, OllamaUnavailableError
from kinito.memory.extractor import MemoryExtractor
from kinito.memory.question_planner import MemoryQuestionPlanner
from kinito.speech_chat import SpeechChatMixin


class LLMMixin(MemoryMixin, SpeechChatMixin):
    """Chat with a local Ollama model and optional AI-generated lines."""

    def _init_llm(self) -> None:
        """Initialize LLM client and conversation (call from app __init__)."""
        self._init_memory()
        self._init_chat_state()
        self._llm_config = LLMConfig.from_env()
        self._ollama_client = OllamaClient(self._llm_config)
        self._conversation = ConversationHistory(max_messages=self._llm_config.max_history)
        self._memory_extractor = MemoryExtractor(self._ollama_client, self._memory)
        self._memory_question_planner = MemoryQuestionPlanner(self._ollama_client, self._memory)
        self._last_chat_user_text = ""
        self._begin_hug_after_speech = False
        if self._llm_config.enabled and self._llm_config.warmup_on_start:
            threading.Thread(target=self._warm_ollama_model, daemon=True).start()

    def _warm_ollama_model(self) -> None:
        """Pre-load the Ollama model in the background."""
        try:
            if self._ollama_client.is_available():
                self._ollama_client.warmup()
        except OllamaUnavailableError:
            pass

    def _activate_pending_visuals(self) -> None:
        """Start pose-specific visuals once the spoken line is actually ready."""
        if getattr(self, "_begin_hug_after_speech", False):
            self._begin_hug_after_speech = False
            self._enter_hug_pose()

    def _show_ai_thinking_sprite(self) -> None:
        """Show the thinking sprite while Ollama generates a line."""
        if hasattr(self, "_stop_roaming"):
            self._stop_roaming()
        self._ai_generating = True
        self.talking = True
        self._talk_sprite_mode = "thinking"
        if hasattr(self, "change_sprite") and hasattr(self, "tk_img_thinking"):
            self.change_sprite(self.tk_img_thinking)

    def _clear_ai_generating(self) -> None:
        """Clear the in-flight AI generation flag."""
        self._ai_generating = False

    def speak(
        self,
        text,
        pitch=45,
        slow=False,
        show_bubble=True,
        voice_candidates=None,
        long_bubble=False,
        wait_for_tts=False,
        allow_in_focus=False,
        preserve_sprite=False,
        question=None,
        *,
        ai_hint=None,
        skip_ai=False,
        speech_accompaniment_path=None,
        speech_accompaniment_volume=None,
    ):
        """Speak *text*, optionally replacing scripted lines with Ollama output."""
        if not self._may_start_speech(str(text)):
            return
        if (
            getattr(self, "_is_game_active", lambda: False)()
            and not skip_ai
            and find_dialog_spec(str(text)) is None
        ):
            return
        if skip_ai or wait_for_tts or not self._should_ai_replace(text):
            self._activate_pending_visuals()
            super().speak(
                text,
                pitch,
                slow,
                show_bubble=show_bubble,
                voice_candidates=voice_candidates,
                long_bubble=long_bubble,
                wait_for_tts=wait_for_tts,
                allow_in_focus=allow_in_focus,
                preserve_sprite=preserve_sprite,
                question=question,
                speech_accompaniment_path=speech_accompaniment_path,
                speech_accompaniment_volume=speech_accompaniment_volume,
            )
            return

        max_tokens = self._llm_config.max_tokens_long if long_bubble else self._llm_config.max_tokens_short
        self._generate_and_speak(
            str(text),
            ai_hint=ai_hint,
            pitch=pitch,
            slow=slow,
            show_bubble=show_bubble,
            voice_candidates=voice_candidates,
            long_bubble=long_bubble,
            wait_for_tts=wait_for_tts,
            allow_in_focus=allow_in_focus,
            preserve_sprite=preserve_sprite,
            question=question,
            max_tokens=max_tokens,
            speech_accompaniment_path=speech_accompaniment_path,
            speech_accompaniment_volume=speech_accompaniment_volume,
        )

    def speak_whisper(
        self,
        text,
        pitch=25,
        slow=False,
        long_bubble=False,
        *,
        ai_hint=None,
        skip_ai=False,
        speech_accompaniment_path=None,
        speech_accompaniment_volume=None,
    ):
        """Speak with whisper voices, with the same optional AI replacement."""
        self.speak(
            text,
            pitch=pitch,
            slow=slow,
            voice_candidates=self.VOICE_WHISPER_CANDIDATES,
            long_bubble=long_bubble,
            ai_hint=ai_hint,
            skip_ai=skip_ai,
            speech_accompaniment_path=speech_accompaniment_path,
            speech_accompaniment_volume=speech_accompaniment_volume,
        )

    def _should_ai_replace(self, text: str | None) -> bool:
        """Return whether a scripted line should be replaced by Ollama."""
        if getattr(self, "_is_game_active", lambda: False)():
            return False
        if not self._llm_config.enabled or not self._llm_config.idle_lines:
            return False
        if getattr(self, "_chat_mode", False):
            return False
        if text and find_dialog_spec(text) is not None:
            return False
        if random.random() >= self._llm_config.replace_chance:
            return False
        return self._ollama_client.is_available()

    def _append_memory_context(self, prompt: str, *, scripted_text: str = "", ai_hint: str | None = None) -> str:
        """Append at most the user's name for light personalization of short lines."""
        if not self._should_personalize_generated_line(scripted_text, ai_hint):
            return prompt
        name = self._memory.get_fact("user_name")
        if not name:
            return prompt
        return f"{prompt}\n\nThe user's name is {name}.\n\n{prompts.MEMORY_GENERATION_HINT}"

    @staticmethod
    def _should_personalize_generated_line(scripted_text: str, ai_hint: str | None) -> bool:
        """Return True only when a generated idle line may use the user's name."""
        if ai_hint in (prompts.IDLE_PROMPT, prompts.RANDOM_QUESTION_PROMPT):
            return True
        blob = f"{scripted_text} {ai_hint or ''}".lower()
        return any(token in blob for token in ("hey", "hello", "hi ", "good morning", "good evening"))

    def _build_generation_prompt(self, scripted_text: str, ai_hint: str | None) -> str:
        """Build the Ollama prompt for replacing a scripted line."""
        if ai_hint and not scripted_text.strip():
            prompt = ai_hint
        elif ai_hint:
            prompt = f"{ai_hint}\nInspired by: {scripted_text.strip()}"
        else:
            hint = prompts.replacement_hint_for(scripted_text)
            prompt = prompts.REPLACEMENT_PROMPT.format(
                scripted=scripted_text.strip(),
                hint=hint,
            )
        prompt = prompts.append_time_context_if_needed(prompt, scripted_text, ai_hint)
        return self._append_memory_context(prompt, scripted_text=scripted_text, ai_hint=ai_hint)

    def _chat_greeting(self) -> str:
        """Return a chat greeting, personalizing when the user's name is known."""
        name = self._memory.get_fact("user_name")
        if name:
            return dlg.CHAT_GREETING_WITH_NAME.format(user_name=name)
        return dlg.CHAT_GREETING

    def _system_prompt(self) -> str:
        """Build the system prompt including persistent memory."""
        return prompts.build_system_prompt(self.memory_prompt_block())

    def _generate_and_speak(self, scripted_text: str, *, ai_hint=None, max_tokens=None, **speak_kwargs):
        """Generate a line in the background, then speak it or fall back to scripted text."""
        if getattr(self, "_is_game_active", lambda: False)():
            return
        if self._has_protected_interactive_state():
            return
        if getattr(self, "_focus_mode", False) and not speak_kwargs.get("allow_in_focus", False):
            return
        if max_tokens is None:
            max_tokens = (
                self._llm_config.max_tokens_long
                if speak_kwargs.get("long_bubble")
                else self._llm_config.max_tokens_short
            )
        self._show_ai_thinking_sprite()
        generation_epoch = getattr(self, "_speech_epoch", 0)
        prompt = self._build_generation_prompt(scripted_text, ai_hint)

        def worker():
            try:
                line = self._ollama_client.generate(
                    prompt,
                    system=self._system_prompt(),
                    max_tokens=max_tokens,
                )
                spoken = line.strip() or scripted_text.strip()
            except OllamaUnavailableError:
                spoken = scripted_text.strip()
            self.root.after(
                0,
                lambda spoken=spoken: self._deliver_generated_line(
                    spoken,
                    speak_kwargs,
                    generation_epoch=generation_epoch,
                ),
            )

        threading.Thread(target=worker, daemon=True).start()

    def _deliver_generated_line(self, spoken: str, speak_kwargs: dict, *, generation_epoch=None) -> None:
        """Speak a generated line on the UI thread."""
        self._clear_ai_generating()
        if generation_epoch is not None and generation_epoch != getattr(self, "_speech_epoch", 0):
            self.talking = False
            return
        if getattr(self, "_is_game_active", lambda: False)():
            self.talking = False
            return
        if self._has_protected_interactive_state():
            self.talking = False
            return
        if getattr(self, "_focus_mode", False) and not speak_kwargs.get("allow_in_focus", False):
            self.talking = False
            return
        self.close_speech_bubble()
        self.speak(spoken, skip_ai=True, **speak_kwargs)

    def start_chat(self) -> None:
        """Open chat mode if Ollama is reachable, otherwise show a fallback line."""
        if not self._llm_config.enabled:
            self.speak(dlg.CHAT_UNAVAILABLE, skip_ai=True)
            return
        if not self._ollama_client.is_available():
            self.speak(dlg.CHAT_UNAVAILABLE, skip_ai=True)
            return
        self._conversation.reset()
        self.open_chat_bubble(self._chat_greeting())

    def send_chat_message(self, user_text: str) -> None:
        """Send a user message to Ollama and display the reply in the chat bubble."""
        text = user_text.strip()
        if not text or not getattr(self, "_chat_mode", False):
            return
        if getattr(self, "_chat_generating", False):
            return

        self._last_chat_user_text = text
        self.append_chat_message(self.chat_user_label(), text)
        self._conversation.add_user(text)
        self.set_chat_generating(True)

        messages = self._conversation.messages_for_api(self._system_prompt())

        def worker():
            try:
                reply = self._ollama_client.chat(messages)
            except OllamaUnavailableError:
                self.root.after(0, self._on_chat_error)
                return
            self.root.after(0, lambda: self._on_chat_response(reply))

        threading.Thread(target=worker, daemon=True).start()

    def _on_chat_response(self, text: str) -> None:
        """Handle a successful Ollama chat reply on the UI thread."""
        if not getattr(self, "_chat_mode", False):
            return
        reply = text.strip() or prompts.CHAT_EMPTY_RESPONSE_FALLBACK
        self._conversation.add_assistant(reply)
        self.append_chat_message(prompts.CHAT_ASSISTANT_LABEL, reply)
        self.set_chat_generating(False)
        self.speak_chat_response(reply)
        self._extract_chat_memory(self._last_chat_user_text, reply)

    def _extract_chat_memory(self, user_text: str, assistant_text: str) -> None:
        """Run memory extraction in the background after a chat reply."""
        if not self._llm_config.enabled:
            return

        def worker():
            self._memory_extractor.extract_from_turn(user_text, assistant_text)

        threading.Thread(target=worker, daemon=True).start()

    def _on_chat_error(self) -> None:
        """Handle Ollama failures during chat on the UI thread."""
        if not getattr(self, "_chat_mode", False):
            return
        fallback = prompts.CHAT_ERROR_FALLBACK
        self.append_chat_message(prompts.CHAT_ASSISTANT_LABEL, fallback)
        self.set_chat_generating(False)
        self.speak_chat_response(fallback)

    def _should_use_ai_idle_line(self) -> bool:
        """Return whether the next idle speech should use Ollama."""
        if not self._can_initiate_spontaneous_speech():
            return False
        return self._should_ai_replace(None)

    def speak_ai_idle_line(self) -> None:
        """Speak a short AI-generated idle line, with scripted fallback."""
        if not self._can_initiate_spontaneous_speech():
            return
        fallback = random.choice(prompts.IDLE_ERROR_FALLBACK_LINES)
        prompt = random.choice([prompts.IDLE_PROMPT, prompts.RANDOM_QUESTION_PROMPT])
        self._generate_and_speak(
            fallback,
            ai_hint=prompt,
            pitch=45,
            slow=True,
            show_bubble=True,
        )

    def speak_ai_memory_question(self) -> None:
        """Plan and ask an interactive AI memory question."""
        if not self._can_initiate_spontaneous_speech():
            return
        self._planning_memory_question = True
        try:
            spec = self._memory_question_planner.plan()
            if spec is not None:
                self.ask_memory_question(spec)
        finally:
            self._planning_memory_question = False

    def speak_memory_question_idle(self) -> None:
        """Ask a memory-aware question via Ollama or scripted templates."""
        if not self._can_initiate_spontaneous_speech():
            return
        if self._llm_config.enabled and self._ollama_client.is_available():
            self.speak_ai_memory_question()
            if self._pending_memory_question is not None:
                return
        spec = self._memory_question_planner.plan_template()
        if spec is not None:
            self.ask_memory_question(spec)
            return
        self.speak_random_question()
