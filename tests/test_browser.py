import time
from unittest.mock import MagicMock, patch

import pytest

from content.allowed_sites import ALLOWED_SITES
from kinito.features.browser import BrowserMixin


class BrowserStub(BrowserMixin):
    BROWSER_WIDTH = 1000
    BROWSER_HEIGHT = 800


@pytest.fixture
def browser():
    stub = BrowserStub()
    stub._browser_active = False
    stub._running = True
    stub.speak = MagicMock()
    stub.root = MagicMock()
    stub.root.update_idletasks = MagicMock()
    stub.root.winfo_rootx.return_value = 100
    stub.root.winfo_rooty.return_value = 200
    stub.root.winfo_width.return_value = 150
    stub.get_screen_bounds = MagicMock(return_value=(0, 0, 800, 600))
    return stub


def test_chat_foreign_url_uses_system_browser_without_speech(browser):
    browser._browser_use_system = False
    with patch("kinito.features.browser.webbrowser.open", return_value=True) as open_url:
        result = browser.open_chat_website("https://example.org", True, (0, 0))
    assert "https://example.org" in result
    open_url.assert_called_once_with("https://example.org")
    browser.speak.assert_not_called()


def test_chat_approved_site_respects_browser_preference(browser):
    browser._browser_use_system = False
    url = ALLOWED_SITES["animals"][0]["url"]
    with (
        patch.object(browser, "_has_pywebview", return_value=True),
        patch.object(browser, "_start_browser_process") as start,
    ):
        browser.open_chat_website(url, False, (100, 200))
    start.assert_called_once_with(url, 100, 200, silent=True)
    browser.speak.assert_not_called()


def test_chat_browser_reports_failure_without_speech(browser):
    with (
        patch("kinito.features.browser.webbrowser.open", return_value=False),
        pytest.raises(OSError),
    ):
        browser.open_chat_website("https://example.org", True, (0, 0))
    browser.speak.assert_not_called()


def test_chat_browser_never_expands_embedded_allowlist(browser):
    with pytest.raises(ValueError):
        browser.open_chat_website("https://example.org", False, (0, 0))


def test_open_allowed_site_rejects_invalid_category_site(browser):
    with patch(
        "kinito.features.browser.pick_random_site",
        return_value={"title": "Bad", "url": "https://evil.example.com"},
    ):
        browser.open_allowed_site("animals")
    browser.speak.assert_called_once()


def test_open_allowed_site_launches_thread_for_valid_site(browser):
    site = ALLOWED_SITES["animals"][0]
    with (
        patch("kinito.features.browser.pick_random_site", return_value=site),
        patch.object(browser, "_roll_browser_surprise", return_value=None),
        patch("kinito.features.browser.threading.Thread") as thread_cls,
    ):
        browser.open_allowed_site("animals")
    thread_cls.assert_called_once()
    assert browser._browser_category == "animals"


def test_open_allowed_site_kinitopet_surprise(browser):
    site = ALLOWED_SITES["animals"][0]
    with (
        patch("kinito.features.browser.pick_random_site", return_value=site),
        patch.object(browser, "_roll_browser_surprise", return_value="kinitopet"),
        patch("kinito.features.browser.threading.Thread") as thread_cls,
    ):
        browser.open_allowed_site("animals")
    thread_cls.assert_called_once()
    args = thread_cls.call_args.kwargs["args"]
    assert args[0] == "https://www.kinitopet.com/"


def test_open_allowed_site_fake_website_surprise(browser):
    site = ALLOWED_SITES["animals"][0]
    with (
        patch("kinito.features.browser.pick_random_site", return_value=site),
        patch.object(browser, "_roll_browser_surprise", return_value="fake_image"),
        patch.object(browser, "_pick_website_image", return_value="C:/fake/site.png"),
        patch("kinito.features.browser.threading.Thread") as thread_cls,
    ):
        browser.open_allowed_site("animals")
    thread_cls.assert_called_once()
    assert thread_cls.call_args.kwargs["target"] == browser._launch_fake_website


@pytest.mark.parametrize("use_system", [True, False])
def test_launch_browser_respects_mode(browser, use_system):
    browser._browser_use_system = use_system
    with (
        patch.object(browser, "_has_pywebview", return_value=True),
        patch.object(browser, "_start_browser_process") as start,
        patch("kinito.features.browser.webbrowser.open", return_value=True) as open_url,
    ):
        browser._launch_browser("https://www.kinitopet.com/", 0, 0, "Hi")
    assert open_url.call_count == int(use_system)
    assert start.call_count == int(not use_system)
    assert browser._browser_active is False


def test_launch_browser_defaults_to_system(browser):
    with (
        patch.object(browser, "_has_pywebview", return_value=True),
        patch.object(browser, "_start_browser_process") as start,
        patch("kinito.features.browser.webbrowser.open", return_value=True) as open_url,
    ):
        browser._launch_browser("https://www.kinitopet.com/", 0, 0, "Hi")
    open_url.assert_called_once_with("https://www.kinitopet.com/")
    start.assert_not_called()


def test_internal_browser_falls_back_to_system(browser):
    browser._browser_use_system = False
    with (
        patch.object(browser, "_has_pywebview", return_value=False),
        patch("kinito.features.browser.webbrowser.open", return_value=True) as open_url,
    ):
        browser._launch_browser("https://www.kinitopet.com/", 0, 0, "Hi")
    open_url.assert_called_once()


@pytest.mark.parametrize("raises", [True, False])
def test_system_browser_failure_is_reported(browser, raises):
    import webbrowser

    with (
        patch.object(browser, "_has_pywebview", return_value=False),
        patch(
            "kinito.features.browser.webbrowser.open",
            return_value=False,
            side_effect=webbrowser.Error("unavailable") if raises else None,
        ) as open_url,
    ):
        browser._launch_browser("https://www.kinitopet.com/", 0, 0, "Hi")
    open_url.assert_called_once()
    assert browser.speak.call_count == 2


@pytest.mark.parametrize("initial", [True, False])
def test_toggle_browser_mode_persists_without_closing_session(browser, initial):
    browser._browser_use_system = initial
    browser._browser_active = True
    browser._persist_settings = MagicMock()
    browser.toggle_browser_mode()
    assert browser._browser_use_system is not initial
    assert browser._browser_active is True
    browser._persist_settings.assert_called_once()
    assert browser.speak.call_args.kwargs["skip_ai"] is True


@pytest.mark.parametrize("use_system", [True, False])
def test_browser_setting_menu_label_and_dispatch(browser, use_system):
    from content import dialogue as dlg
    from content.dialog_registry import (
        find_dialog_spec,
        handle_dialog_response,
        settings_options_for,
    )

    browser._browser_use_system = use_system
    browser.paused = False
    browser._focus_mode = False
    browser._hidden_menu_buttons = set()
    label = dlg.BUTTON_BROWSER_SYSTEM if use_system else dlg.BUTTON_BROWSER_KINITO
    assert label in settings_options_for(browser)
    browser.toggle_browser_mode = MagicMock()
    handle_dialog_response(browser, find_dialog_spec(dlg.SETTINGS_MENU_QUESTION), label)
    browser.toggle_browser_mode.assert_called_once()


@pytest.mark.parametrize("blocked_state", ["paused", "_focus_mode"])
def test_browser_setting_blocked_during_sleep_or_focus(browser, blocked_state):
    from content import dialogue as dlg
    from content.dialog_registry import find_dialog_spec, handle_dialog_response

    browser.paused = False
    browser._focus_mode = False
    setattr(browser, blocked_state, True)
    browser.toggle_browser_mode = MagicMock()
    handle_dialog_response(
        browser, find_dialog_spec(dlg.SETTINGS_MENU_QUESTION), dlg.BUTTON_BROWSER_SYSTEM
    )
    browser.toggle_browser_mode.assert_not_called()


def test_launch_browser_skips_when_not_running(browser):
    browser._running = False
    with (
        patch.object(browser, "_has_pywebview", return_value=False),
        patch("kinito.features.browser.webbrowser.open") as open_url,
    ):
        browser._launch_browser("https://www.kinitopet.com/", 0, 0, "Hi")
    browser.speak.assert_called_once()
    assert browser.speak.call_args.args[0] == "Hi"
    assert browser.speak.call_args.kwargs["wait_for_tts"] is True
    open_url.assert_not_called()


def _enable_browser_ai(browser):
    browser._should_ai_replace = MagicMock(return_value=True)
    browser._ai_generating = False
    browser._show_ai_thinking_sprite = MagicMock()
    browser._clear_ai_generating = MagicMock()


def test_speak_browser_intro_uses_generated_line(browser):
    _enable_browser_ai(browser)
    browser.generate_line_sync = MagicMock(return_value="AI browse line")
    browser._speak_browser_intro("scripted", time.monotonic() + 5)
    browser.speak.assert_called_once()
    assert browser.speak.call_args.args[0] == "AI browse line"
    assert browser.speak.call_args.kwargs["max_wait_s"] <= 5


def test_speak_browser_intro_shows_thinking_sprite_while_generating(browser):
    _enable_browser_ai(browser)
    order = []
    browser._show_ai_thinking_sprite.side_effect = lambda: order.append("think")
    browser._clear_ai_generating.side_effect = lambda: order.append("clear")
    browser.speak.side_effect = lambda *a, **k: order.append("speak")
    browser.generate_line_sync = MagicMock(return_value="AI line")
    browser._speak_browser_intro("scripted", time.monotonic() + 5)
    assert order == ["think", "clear", "speak"]


def test_speak_browser_intro_skips_generation_when_ai_busy(browser):
    _enable_browser_ai(browser)
    browser._ai_generating = True
    browser.generate_line_sync = MagicMock(return_value="AI line")
    browser._speak_browser_intro("scripted", time.monotonic() + 5)
    browser.generate_line_sync.assert_not_called()
    browser._show_ai_thinking_sprite.assert_not_called()
    assert browser.speak.call_args.args[0] == "scripted"


def test_speak_browser_intro_falls_back_when_generation_is_slow(browser):
    _enable_browser_ai(browser)
    browser.generate_line_sync = MagicMock(
        side_effect=lambda *a, **k: time.sleep(2)
    )
    browser._speak_browser_intro("scripted", time.monotonic() + 0.05)
    assert browser.speak.call_args.args[0] == "scripted"
    browser._clear_ai_generating.assert_called_once()


def test_speak_browser_intro_without_llm_support(browser):
    browser._speak_browser_intro("scripted", time.monotonic() + 5)
    assert browser.speak.call_args.args[0] == "scripted"


def test_launch_browser_opens_within_deadline(browser):
    browser.generate_line_sync = MagicMock(return_value="AI line")
    deadline_margin = 1.0
    started = time.monotonic()
    with (
        patch.object(browser, "_speak_browser_intro") as intro,
        patch("kinito.features.browser.webbrowser.open", return_value=True) as open_url,
    ):
        browser._launch_browser("https://example.com", 10, 20, "hi")
    intro.assert_called_once()
    deadline = intro.call_args.args[1]
    assert deadline - started <= BrowserMixin.BROWSER_OPEN_DEADLINE_S + deadline_margin
    open_url.assert_called_once_with("https://example.com")


def test_speak_browser_intro_passes_category_hint(browser):
    _enable_browser_ai(browser)
    browser.generate_line_sync = MagicMock(return_value="AI line")
    browser._speak_browser_intro("scripted", time.monotonic() + 5, "horror")
    hint = browser.generate_line_sync.call_args.kwargs["ai_hint"]
    assert "horror" in hint
