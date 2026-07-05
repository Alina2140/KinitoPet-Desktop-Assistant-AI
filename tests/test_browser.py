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


def test_launch_browser_skips_when_not_running(browser):
    browser._running = False
    with (
        patch.object(browser, "_has_pywebview", return_value=False),
        patch("kinito.features.browser.webbrowser.open") as open_url,
    ):
        browser._launch_browser("https://www.kinitopet.com/", 0, 0, "Hi")
    browser.speak.assert_called_once_with("Hi", show_bubble=True, wait_for_tts=True)
    open_url.assert_not_called()
