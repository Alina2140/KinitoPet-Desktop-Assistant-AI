"""Ollama-powered chat and AI-enhanced speech for Kinito."""

from __future__ import annotations

import random
import threading

from content import dialogue as dlg
from content import llm_prompts as prompts
from content.dialog_registry import find_dialog_spec
from kinito.llm.config import LLMConfig
from kinito.llm.conversation import ConversationHistory
from kinito.llm.ollama_client import OllamaClient, OllamaUnavailableError
from kinito.speech_chat import SpeechChatMixin


class LLMMixin(SpeechChatMixin):
    """Chat with a local Ollama model and optional AI-generated lines."""

    def _init_llm(self) -> None:
        """Initialize LLM client and conversation (call from app __init__)."""
        self._init_chat_state()
        self._llm_config = LLMConfig.from_env()
        self._ollama_client = OllamaClient(self._llm_config)
        self._conversation = ConversationHistory(max_messages=self._llm_config.max_history)
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
        if not self._llm_config.enabled or not self._llm_config.idle_lines:
            return False
        if getattr(self, "_chat_mode", False):
            return False
        if text and find_dialog_spec(text) is not None:
            return False
        if random.random() >= self._llm_config.replace_chance:
            return False
        return self._ollama_client.is_available()

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
        return prompts.append_time_context_if_needed(prompt, scripted_text, ai_hint)

    def _generate_and_speak(self, scripted_text: str, *, ai_hint=None, max_tokens=None, **speak_kwargs):
        """Generate a line in the background, then speak it or fall back to scripted text."""
        if max_tokens is None:
            max_tokens = (
                self._llm_config.max_tokens_long
                if speak_kwargs.get("long_bubble")
                else self._llm_config.max_tokens_short
            )
        self._show_ai_thinking_sprite()
        prompt = self._build_generation_prompt(scripted_text, ai_hint)

        def worker():
            try:
                line = self._ollama_client.generate(
                    prompt,
                    system=prompts.SYSTEM_PROMPT,
                    max_tokens=max_tokens,
                )
                spoken = line.strip() or scripted_text.strip()
            except OllamaUnavailableError:
                spoken = scripted_text.strip()
            self.root.after(
                0,
                lambda spoken=spoken: self._deliver_generated_line(spoken, speak_kwargs),
            )

        threading.Thread(target=worker, daemon=True).start()

    def _deliver_generated_line(self, spoken: str, speak_kwargs: dict) -> None:
        """Speak a generated line on the UI thread."""
        self._clear_ai_generating()
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
        self.open_chat_bubble(dlg.CHAT_GREETING)

    def send_chat_message(self, user_text: str) -> None:
        """Send a user message to Ollama and display the reply in the chat bubble."""
        text = user_text.strip()
        if not text or not getattr(self, "_chat_mode", False):
            return
        if getattr(self, "_chat_generating", False):
            return

        self.append_chat_message(prompts.CHAT_USER_LABEL, text)
        self._conversation.add_user(text)
        self.set_chat_generating(True)

        messages = self._conversation.messages_for_api(prompts.SYSTEM_PROMPT)

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
