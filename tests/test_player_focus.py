"""Tests for quiet Player Focus while the music player is open."""

from unittest.mock import MagicMock, patch

import pytest

from content import dialogue as dlg
from kinito.app import FloatingAssistant
from kinito.speech import SpeechMixin


class SpeechStub(SpeechMixin):
    def __init__(self):
        self._speech_epoch = 0
        self._focus_mode = False
        self._player_focus_enabled = True
        self.talking = False
        self._awaiting_response = False
        self._player_focus_active = MagicMock(return_value=False)


@pytest.fixture
def speech():
    return SpeechStub()


def test_speak_is_blocked_when_player_focus_is_active(speech):
    speech._player_focus_active.return_value = True
    speech.interrupt_speech = MagicMock()
    speech.speak("Hello")
    speech.interrupt_speech.assert_not_called()


def test_speak_allow_in_focus_still_runs_when_player_focus_is_active(speech):
    speech._player_focus_active.return_value = True
    speech.interrupt_speech = MagicMock()
    speech._may_start_speech = MagicMock(return_value=False)
    speech.speak("Menu", allow_in_focus=True)
    speech._may_start_speech.assert_called_once()


def test_speak_brief_is_blocked_when_player_focus_is_active(speech):
    speech._player_focus_active.return_value = True
    speech.interrupt_speech = MagicMock()
    speech.show_speech_bubble = MagicMock()
    speech.speak_brief("Quiet")
    speech.show_speech_bubble.assert_not_called()


def test_run_tts_is_skipped_when_player_focus_is_active(speech):
    speech._tts_enabled = True
    speech._player_focus_active.return_value = True
    assert speech._run_tts("Hello") is False


def test_play_sfx_is_muted_when_player_focus_is_active():
    app = FloatingAssistant.__new__(FloatingAssistant)
    app._player_focus_active = MagicMock(return_value=True)
    with patch("kinito.app.os.path.isfile") as isfile:
        app.play_sfx("boop.mp3")
    isfile.assert_not_called()


def test_play_mp3_accompaniment_is_muted_when_player_focus_is_active():
    app = FloatingAssistant.__new__(FloatingAssistant)
    app._player_focus_active = MagicMock(return_value=True)
    with patch("kinito.app.os.path.isfile") as isfile:
        app.play_mp3("poem.mp3", speech_accompaniment=True)
    isfile.assert_not_called()


def test_play_mp3_user_music_still_plays_when_player_focus_is_active():
    app = FloatingAssistant.__new__(FloatingAssistant)
    app._player_focus_active = MagicMock(return_value=True)
    with patch("kinito.app.os.path.isfile", return_value=False) as isfile:
        app.play_mp3("song.mp3")
    isfile.assert_called_once()


def test_can_initiate_spontaneous_speech_blocks_during_player_focus():
    app = FloatingAssistant.__new__(FloatingAssistant)
    app._startup_complete = True
    app._allow_random_questions = True
    app.moving = False
    app.talking = False
    app._awaiting_response = False
    app._focus_mode = False
    app._is_game_active = MagicMock(return_value=False)
    app._is_busy_with_speech = MagicMock(return_value=False)
    app._player_focus_active = MagicMock(return_value=True)
    assert FloatingAssistant._can_initiate_spontaneous_speech(app) is False


def test_toggle_player_focus_on_speaks_confirmation():
    app = FloatingAssistant.__new__(FloatingAssistant)
    app._player_focus_enabled = False
    app._music_player_window = None
    app._persist_settings = MagicMock()
    app.speak = MagicMock()

    with patch("kinito.features.music.dlg.pick_line", return_value=dlg.PLAYER_FOCUS_ON_LINES[0]):
        FloatingAssistant.toggle_player_focus(app)

    assert app._player_focus_enabled is True
    app._persist_settings.assert_called_once()
    app.speak.assert_called_once_with(
        dlg.PLAYER_FOCUS_ON_LINES[0],
        skip_ai=True,
        allow_in_focus=True,
    )
