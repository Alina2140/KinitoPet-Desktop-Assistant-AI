from unittest.mock import MagicMock, patch

from content import credits
from content import dialogue as dlg
from content.dialog_registry import find_dialog_spec, handle_dialog_response


def test_credits_text_matches_dialog_spec():
    spec = find_dialog_spec(credits.CREDITS_TEXT)
    assert spec is not None
    assert credits.CREDITS_MARKER.lower() in spec.marker.lower()


def test_credits_dialog_spec_has_link_buttons():
    spec = find_dialog_spec(credits.CREDITS_TEXT)
    assert dlg.BUTTON_CREDITS_STEAM in spec.ui.buttons
    assert dlg.BUTTON_CREDITS_GITHUB in spec.ui.buttons
    assert dlg.BUTTON_OKAY in spec.ui.buttons


@patch("content.dialog_registry.webbrowser.open")
def test_credits_handler_opens_steam_link(mock_open):
    app = MagicMock()
    spec = find_dialog_spec(credits.CREDITS_TEXT)
    handle_dialog_response(app, spec, dlg.BUTTON_CREDITS_STEAM)
    mock_open.assert_called_once_with(credits.CREDITS_URL_STEAM)


@patch("content.dialog_registry.webbrowser.open")
def test_credits_handler_opens_github_link(mock_open):
    app = MagicMock()
    spec = find_dialog_spec(credits.CREDITS_TEXT)
    handle_dialog_response(app, spec, dlg.BUTTON_CREDITS_GITHUB)
    mock_open.assert_called_once_with(credits.CREDITS_URL_GITHUB)
