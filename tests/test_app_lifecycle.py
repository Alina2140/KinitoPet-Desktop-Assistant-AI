from unittest.mock import MagicMock, patch

import pytest

from content.goodbye_lines import GOODBYE_LINES
from kinito.app import FloatingAssistant, _open_sprite
from kinito.speech import SpeechMixin


class AppStub(SpeechMixin):
    BUBBLE_MAX_WIDTH = 800


@pytest.fixture
def app_stub():
    stub = AppStub()
    stub._speech_lock = MagicMock()
    stub._speech_lock.__enter__ = MagicMock(return_value=None)
    stub._speech_lock.__exit__ = MagicMock(return_value=False)
    stub._startup_complete = True
    stub._allow_random_questions = True
    stub.moving = False
    stub.talking = False
    stub._awaiting_response = False
    stub._running = True
    stub.root = MagicMock()
    stub.close_camera = MagicMock()
    stub.close_browser = MagicMock()
    stub.end_hug = MagicMock()
    stub.close_speech_bubble = MagicMock()
    stub.speak = MagicMock(side_effect=lambda text, **kw: setattr(stub, "_last_spoken", text))
    return stub


@pytest.fixture
def goodbye_app(app_stub):
    app = FloatingAssistant.__new__(FloatingAssistant)
    app.__dict__.update(app_stub.__dict__)
    app._bubble_display_duration = AppStub._bubble_display_duration.__get__(app, FloatingAssistant)
    app.speak = MagicMock()
    app.root = MagicMock()
    app.close_camera = MagicMock()
    app.close_browser = MagicMock()
    app.end_hug = MagicMock()
    app._quit_app = MagicMock()
    return app


def test_can_initiate_spontaneous_speech_requires_startup(app_stub):
    app = FloatingAssistant.__new__(FloatingAssistant)
    app._startup_complete = False
    app._allow_random_questions = True
    app.moving = False
    app.talking = False
    app._awaiting_response = False
    assert FloatingAssistant._can_initiate_spontaneous_speech(app) is False


def test_can_initiate_spontaneous_speech_blocks_while_moving(app_stub):
    app = FloatingAssistant.__new__(FloatingAssistant)
    app._startup_complete = True
    app._allow_random_questions = True
    app.moving = True
    app.talking = False
    app._awaiting_response = False
    assert FloatingAssistant._can_initiate_spontaneous_speech(app) is False


def test_say_goodbye_shuts_down_and_schedules_quit(goodbye_app):
    goodbye_app._bubble_close_delay_after_tts = SpeechMixin._bubble_close_delay_after_tts.__get__(
        goodbye_app, FloatingAssistant
    )
    with (
        patch("kinito.app.random.choice", return_value=GOODBYE_LINES[0]),
        patch(
            "kinito.app.threading.Thread",
            side_effect=lambda target, daemon=True: MagicMock(start=target),
        ),
    ):
        goodbye_app.say_goodbye()

    assert goodbye_app._running is False
    goodbye_app.close_camera.assert_called_once()
    goodbye_app.close_browser.assert_called_once()
    goodbye_app.end_hug.assert_called_once()
    goodbye_app.speak.assert_called_once_with(GOODBYE_LINES[0], show_bubble=True, wait_for_tts=True)
    goodbye_app.root.after.assert_called_once()
    delay = goodbye_app.root.after.call_args[0][0]
    assert delay >= 3000


def test_on_destroy_ignores_child_widgets(goodbye_app):
    event = MagicMock()
    event.widget = MagicMock()
    goodbye_app._running = True
    FloatingAssistant._on_destroy(goodbye_app, event)
    assert goodbye_app._running is True


def test_on_destroy_cleans_up_root(goodbye_app):
    goodbye_app._running = True
    FloatingAssistant._on_destroy(goodbye_app, None)
    assert goodbye_app._running is False
    goodbye_app.close_camera.assert_called_once()


def test_open_sprite_uses_fallback_when_missing(tmp_path):
    missing = tmp_path / "missing.png"
    fallback = tmp_path / "fallback.png"
    from PIL import Image

    Image.new("RGB", (4, 4), "red").save(fallback)
    img = _open_sprite(str(missing), str(fallback))
    assert img.size == (4, 4)


def test_play_mp3_skips_missing_file(goodbye_app):
    goodbye_app.play_mp3("definitely/not/a/file.mp3")


def test_play_mp3_swallows_pygame_errors(goodbye_app, tmp_path):
    import pygame

    mp3 = tmp_path / "test.mp3"
    mp3.write_bytes(b"not a real mp3")
    with patch("kinito.app.pygame.mixer") as mixer:
        mixer.get_init.return_value = True
        mixer.music.load.side_effect = pygame.error("boom")
        goodbye_app.play_mp3(str(mp3))


def test_play_sfx_skips_missing_file(goodbye_app):
    goodbye_app.play_sfx("definitely/not/a/file.mp3")


def test_play_sfx_swallows_pygame_errors(goodbye_app, tmp_path):
    import pygame

    mp3 = tmp_path / "test.mp3"
    mp3.write_bytes(b"not a real mp3")
    with (
        patch.object(goodbye_app, "_ensure_mixer"),
        patch(
            "kinito.app.pygame.mixer.Sound",
            side_effect=pygame.error("boom"),
        ),
    ):
        goodbye_app.play_sfx(str(mp3))
