import subprocess
from unittest.mock import MagicMock, patch

import pytest

from content import dialogue as dlg
from kinito.features.browser import BrowserMixin


class BrowserStub(BrowserMixin):
    BROWSER_WIDTH = 1000
    BROWSER_HEIGHT = 800


@pytest.fixture
def browser():
    stub = BrowserStub()
    stub._browser_active = False
    stub._browser_process = None
    stub._browser_category = None
    stub._running = True
    stub.talking = False
    stub.speak = MagicMock()
    stub.root = MagicMock()
    stub.root.update_idletasks = MagicMock()
    stub.root.winfo_rootx.return_value = 100
    stub.root.winfo_rooty.return_value = 200
    stub.root.winfo_width.return_value = 150
    stub.get_screen_bounds = MagicMock(return_value=(0, 0, 800, 600))
    stub._is_busy_with_speech = MagicMock(return_value=False)
    return stub


def test_close_browser_terminates_running_process(browser):
    process = MagicMock()
    process.poll.return_value = None
    process.wait.return_value = 0
    browser._browser_process = process
    browser._browser_active = True

    browser.close_browser()

    process.terminate.assert_called_once()
    assert browser._browser_active is False
    assert browser._browser_process is None


def test_close_browser_kills_on_timeout(browser):
    process = MagicMock()
    process.poll.return_value = None
    process.wait.side_effect = subprocess.TimeoutExpired("cmd", 2)
    browser._browser_process = process

    browser.close_browser()

    process.kill.assert_called_once()


def test_wait_for_browser_process_speaks_pywebview_hint(browser):
    process = MagicMock()
    process.stderr = MagicMock()
    process.stderr.read.return_value = "pywebview not installed"
    process.wait.return_value = 1
    browser._browser_process = process

    browser._wait_for_browser_process("animals")

    browser.speak.assert_called_once()
    assert "pywebview" in browser.speak.call_args[0][0].lower()


def test_wait_for_browser_process_closes_with_horror_line(browser):
    process = MagicMock()
    process.stderr = MagicMock()
    process.stderr.read.return_value = ""
    process.wait.return_value = 0
    browser._browser_process = process
    browser.talking = False

    with patch("kinito.features.browser.dlg.pick_line", return_value="spooky bye") as pick:
        browser._wait_for_browser_process("horror")

    pick.assert_called_with(dlg.BROWSER_HORROR_CLOSE_LINES)
    browser.speak.assert_called_once_with("spooky bye")


def test_offer_browser_visit_skips_when_busy(browser):
    browser._is_busy_with_speech.return_value = True
    browser.offer_browser_visit()
    browser.speak.assert_not_called()
