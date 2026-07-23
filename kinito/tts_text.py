"""Normalize text before TTS so balcon does not spell ALL-CAPS letter by letter.

Display text (bubbles, chat log) stays unchanged; only the string passed to balcon
or pyttsx3 is lowercased in ``SpeechMixin._run_tts``.
"""


def normalize_text_for_tts(text: str) -> str:
    """Return a speakable copy of *text*; the original UI text is not modified."""
    return text.lower()
