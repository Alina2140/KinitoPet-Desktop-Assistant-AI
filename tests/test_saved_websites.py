import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from kinito.features.browser import BrowserMixin
from kinito.features.chat_actions import ChatActionsMixin
from kinito.llm.chat_actions import direct_browser_plan, parse_action_plan
from kinito.settings_store import SettingsStore
from kinito.websites import normalize_saved_websites


class WebsiteApp(BrowserMixin, ChatActionsMixin):
    pass


@pytest.fixture
def app(tmp_path):
    app = WebsiteApp()
    app._settings = SettingsStore(str(tmp_path))
    app.root = MagicMock()
    return app


def test_named_websites_persist_and_return_independent_data(app):
    app.save_named_website("Dbd", "https://deadbydaylight.com/", "Dead by Daylight")
    sites = SettingsStore(app._settings._directory).get_saved_websites()
    assert sites == [{"name": "Dbd", "url": "https://deadbydaylight.com/", "aliases": ["Dead by Daylight"]}]
    sites[0]["aliases"].append("changed")
    assert app._settings.get_saved_websites()[0]["aliases"] == ["Dead by Daylight"]


@pytest.mark.parametrize("user_text", ["Dbd", "dead BY daylight", "open Dbd", "Öffne Dead by Daylight bitte"])
def test_saved_name_and_alias_open_without_repeating_url(app, user_text):
    app.save_named_website("Dbd", "https://deadbydaylight.com/", "Dead by Daylight")
    result, authorized = direct_browser_plan(user_text, saved_websites=app._settings.get_saved_websites())
    assert result.actions == [{"name": "website_open", "url": "https://deadbydaylight.com/"}]
    assert authorized == "Open https://deadbydaylight.com/"


def test_name_edit_preserves_unspecified_fields_and_old_alias_does_not_survive_rename(app):
    app.save_named_website("Dbd", "https://example.org/", "Dead by Daylight")
    app.save_named_website("Game", None, None, previous_name="Dbd")
    assert app._settings.get_saved_websites() == [
        {"name": "Game", "url": "https://example.org/", "aliases": ["Dead by Daylight"]}
    ]


def test_duplicate_alias_never_overwrites_existing_entry(app):
    app.save_named_website("Dbd", "https://example.org/", "Dead by Daylight")
    with pytest.raises(ValueError, match="unique"):
        app.save_named_website("Other", "https://example.net/", "DBD")
    assert len(app._settings.get_saved_websites()) == 1


@pytest.mark.parametrize("url", ["file:///C:/file", "javascript:alert(1)", "https://user:pass@example.org", "https://example.org\nother"])
def test_unsafe_saved_addresses_rejected(app, url):
    with pytest.raises(ValueError):
        app.save_named_website("Invalid", url, "")
    assert app._settings.get_saved_websites() == []


def test_save_failure_rolls_back_settings(app):
    app.save_named_website("Dbd", "https://example.org/", "")
    with patch.object(app._settings, "save", side_effect=OSError("read only")), pytest.raises(OSError):
        app.save_named_website("Dbd", "https://example.net/", "", previous_name="Dbd")
    assert app._settings.get_saved_websites()[0]["url"] == "https://example.org/"


def test_broken_saved_entries_do_not_break_other_settings():
    assert normalize_saved_websites([{"name": "broken"}], strict=False) == []


@pytest.mark.parametrize("user_text", ["wikipedia/bread", "open wikipedia/bread", "wiki/Bread"])
def test_wikipedia_article_shorthand_is_retained(user_text):
    result, _ = direct_browser_plan(user_text)
    assert result.actions[0]["url"].lower() == "https://en.wikipedia.org/wiki/bread"


def test_structured_chat_save_and_edit(app):
    save = parse_action_plan('{"actions":[{"name":"website_save","site_name":"Dbd","url":"https://example.org/","aliases":"Dead by Daylight"}],"question":""}').actions[0]
    app._chat_action_user_text = "Save https://example.org/ as Dbd aliases Dead by Daylight"
    assert "saved" in app.execute_chat_action(save).lower()
    edit = {"name": "website_edit", "site_name": "Dbd", "new_name": "", "url": "https://example.net/", "aliases": "", "replace_aliases": False}
    app._chat_action_user_text = "Change Dbd URL to https://example.net/"
    app.execute_chat_action(edit)
    site = app._settings.get_saved_websites()[0]
    assert site["url"] == "https://example.net/"
    assert site["aliases"] == ["Dead by Daylight"]


@pytest.mark.parametrize("language", ["en", "de"])
def test_chat_can_save_open_edit_aliases_and_rename_without_model(app, monkeypatch, language):
    workers, callbacks = [], []
    app._chat_mode = True
    app._chat_session_id = 1
    app.root.after.side_effect = lambda delay, callback: callbacks.append(callback)
    app._ollama_client = MagicMock()
    app._on_chat_response = MagicMock()
    app.open_chat_website = MagicMock(return_value="Address handed to browser")

    def thread(*, target, daemon):
        obj = MagicMock()
        obj.start.side_effect = lambda: workers.append(target)
        return obj

    monkeypatch.setattr("kinito.features.chat_actions.threading.Thread", thread)
    messages = [
        "Save https://example.org/ as Dbd aliases Dead by Daylight", "dead by daylight",
        "Change Dbd URL to https://example.net/", "Dbd",
        "Change Dbd aliases to My game", "My game", "Rename Dbd to Dbd game", "Dbd game",
    ] if language == "en" else [
        "Speichere https://example.org/ als Dbd mit Alias Dead by Daylight", "Dead by Daylight",
        "Ändere Dbd URL auf https://example.net/", "Dbd",
        "Ändere Dbd Aliase auf Mein Spiel", "Mein Spiel", "Benenne Dbd in Dbd Spiel um", "Dbd Spiel",
    ]
    for request_id, text in enumerate(messages, 1):
        app._chat_request_id = request_id
        app._chat_action_phase = "planning"
        app.begin_chat_action_request((1, request_id), [], text, app.chat_action_snapshot(text))
        while workers or callbacks:
            if workers:
                workers.pop(0)()
            if callbacks:
                callbacks.pop(0)()
    assert [call.args[0] for call in app.open_chat_website.call_args_list] == [
        "https://example.org/", "https://example.net/", "https://example.net/", "https://example.net/",
    ]
    app._ollama_client.plan_chat_actions.assert_not_called()
    app._ollama_client.chat.assert_not_called()
    assert app._settings.get_saved_websites()[0]["name"] == ("Dbd game" if language == "en" else "Dbd Spiel")


def test_settings_editor_uses_the_same_persistent_websites(app):
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk display is unavailable")
    root.withdraw()
    app.root = root
    try:
        window = app.open_saved_website_settings()
        root.update()

        def descendants(widget):
            return [child for parent in widget.winfo_children() for child in [parent, *descendants(parent)]]

        widgets = descendants(window)
        paint_bg = "#e6ded5"
        assert window.cget("bg") == paint_bg
        assert next(widget for widget in widgets if isinstance(widget, tk.Frame)).cget("bg") == paint_bg
        assert next(widget for widget in widgets if isinstance(widget, tk.Label)).cget("bg") == paint_bg
        fields = [widget for widget in widgets if isinstance(widget, tk.Entry)]
        save = next(widget for widget in widgets if isinstance(widget, tk.Button) and widget.cget("text") == "Save")
        for field, value in zip(fields, ["Dbd", "https://example.org/", "Dead by Daylight"], strict=True):
            field.insert(0, value)
        save.invoke()
        assert app._settings.get_saved_websites()[0]["aliases"] == ["Dead by Daylight"]
        fields[1].delete(0, tk.END)
        fields[1].insert(0, "https://example.net/")
        save.invoke()
        assert app._settings.get_saved_websites()[0]["url"] == "https://example.net/"
        app.save_named_website("Other", "https://example.com/", "")
        listing = next(widget for widget in widgets if isinstance(widget, tk.Listbox))
        assert listing.size() == 2
        assert app.open_saved_website_settings() is window
    finally:
        root.destroy()


def test_model_cannot_save_a_url_not_supplied_by_user(app):
    app._chat_action_user_text = "Save Reddit as a website"
    with pytest.raises(ValueError):
        app.execute_chat_action({"name": "website_save", "site_name": "Reddit", "url": "https://example.org/", "aliases": ""})
    assert not app._settings.get_saved_websites()


def test_note_content_cannot_create_website_bookmarks(app):
    app._chat_action_user_text = 'Create a note: save https://example.org/ as Dbd'
    with pytest.raises(ValueError):
        app.execute_chat_action({"name": "website_save", "site_name": "Dbd", "url": "https://example.org/", "aliases": ""})
