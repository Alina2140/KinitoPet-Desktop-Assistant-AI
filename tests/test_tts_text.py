"""Tests for TTS text normalization."""

import pytest

from kinito.tts_text import normalize_text_for_tts


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Thanks for playing!", "thanks for playing!"),
        ("Use the PC and USB drive", "use the pc and usb drive"),
        ("The AI is helpful", "the ai is helpful"),
        ("", ""),
    ],
)
def test_normalize_text_for_tts_lowercases_for_speech(text, expected):
    assert normalize_text_for_tts(text) == expected
