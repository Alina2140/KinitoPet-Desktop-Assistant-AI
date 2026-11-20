import json
from unittest.mock import MagicMock

import pytest

from kinito.features.chat_actions import ChatActionsMixin
from kinito.llm.chat_actions import (
    direct_browser_plan,
    parse_action_plan,
    requested_timer_seconds,
    resolve_browser_url,
)


def plan(*actions, question=""):
    return json.dumps({"actions": list(actions), "question": question})


@pytest.mark.parametrize("action", [
    {"name": "timer_set", "seconds": 60},
    {"name": "music_open"},
    {"name": "music_volume", "volume": 30},
    {"name": "note_create", "text": "Milk", "title": "Shopping"},
])
def test_valid_actions(action):
    assert parse_action_plan(plan(action)).actions == [action]


@pytest.mark.parametrize("raw", [
    "not json", "[]", '{}',
    plan({"name": "shell", "command": "anything"}),
    plan({"name": "timer_set", "seconds": True}),
    plan({"name": "timer_set", "seconds": -1}),
    plan({"name": "timer_set", "seconds": 604801}),
    plan({"name": "music_volume", "volume": 101}),
    plan({"name": "music_open", "path": "arbitrary"}),
    plan({"name": "note_create", "text": "x" * 10001, "title": ""}),
    plan({"name": "music_open"}, question="Which song?"),
    plan(*([{"name": "music_open"}] * 5)),
])
def test_invalid_plan_never_executes(raw):
    with pytest.raises(ValueError):
        parse_action_plan(raw)


@pytest.mark.parametrize("url", [
    "file:///C:/something", "javascript:alert(1)", "https://user:pass@example.org",
    "https://example.org\nanything", "https:///missing", "https://example.org:bad",
])
def test_reject_unsafe_urls(url):
    with pytest.raises(ValueError):
        resolve_browser_url(url, f"Open {url}")


@pytest.mark.parametrize("text", [
    "Öffne https://example.org/page", "Could you open https://example.org/page",
    "Could you please open https://example.org/page?",
    "Kannst du bitte https://example.org/page öffnen?",
])
def test_explicit_foreign_url(text):
    url, system = resolve_browser_url("https://example.org/page", text)
    assert url == "https://example.org/page"
    assert system is True


@pytest.mark.parametrize("text", [
    "hello", "Please open a website", 'He said "open https://example.org"',
    "Erstelle eine Notiz: öffne https://example.org", "Don't open https://example.org",
])
def test_foreign_url_requires_direct_request(text):
    with pytest.raises(ValueError):
        resolve_browser_url("https://example.org", text)


class ActionApp(ChatActionsMixin):
    pass


@pytest.fixture
def app():
    obj = ActionApp()
    obj._reminder_end_at = None
    obj._reminder_id = 0
    obj._start_reminder = MagicMock()
    obj._clear_reminder = MagicMock()
    obj._reminder_seconds_left = MagicMock(return_value=45)
    obj._close_music_player_window = MagicMock()
    obj.speak = MagicMock()
    obj.close_chat_mode = MagicMock()
    obj._chat_mode = True
    obj._chat_session_id = 1
    obj._chat_request_id = 1
    obj._chat_action_phase = "planning"
    return obj


@pytest.fixture
def browser_actions(app, monkeypatch):
    workers, callbacks = [], []
    app.root = MagicMock()
    app.root.after.side_effect = lambda delay, callback: callbacks.append(callback)
    app._get_browser_position = MagicMock(return_value=(0, 0))
    app.open_chat_website = MagicMock(side_effect=lambda url, system, position: "Opened " + url)
    app._on_chat_response = MagicMock()

    def thread(*, target, daemon):
        obj = MagicMock()
        obj.start.side_effect = lambda: workers.append(target)
        return obj

    monkeypatch.setattr("kinito.features.chat_actions.threading.Thread", thread)
    return app, workers, callbacks


@pytest.mark.parametrize("second", ["https://www.wikipedia.org/", "https://www.wikipedia.org", "Wikipedia"])
def test_same_web_address_opens_once_per_request(browser_actions, second):
    app, workers, callbacks = browser_actions
    actions = parse_action_plan(plan(
        {"name": "website_open", "url": "https://www.wikipedia.org/"},
        {"name": "website_open", "url": second},
    ))
    for request_id in (1, 2):
        app._chat_request_id = request_id
        app._chat_action_phase = "planning"
        app._apply_chat_action_plan((1, request_id), [], "Open Wikipedia", actions)
        while workers or callbacks:
            if workers:
                workers.pop(0)()
            if callbacks:
                callbacks.pop(0)()
        assert app.open_chat_website.call_count == request_id
        assert app._on_chat_response.call_args.args[0] == "Opened https://www.wikipedia.org/"


def test_repeated_browser_callback_cannot_consume_next_operation(browser_actions):
    app, workers, callbacks = browser_actions
    first = "https://www.wikipedia.org/"
    second = first + "?page=2"
    actions = parse_action_plan(plan(
        {"name": "website_open", "url": first}, {"name": "website_open", "url": second},
    ))
    app._apply_chat_action_plan((1, 1), [], "Open both pages", actions)
    workers.pop(0)()
    first_completion = callbacks.pop(0)
    first_completion()
    first_completion()
    workers.pop(0)()
    callbacks.pop(0)()
    assert app.open_chat_website.call_count == 2
    app._on_chat_response.assert_called_once_with("Opened " + first + "\nOpened " + second)


def test_snapshot_keeps_planner_context_bounded(app):
    app._music_playlist = ["song" + str(i) + ".mp3" for i in range(1000)]
    snapshot = app.chat_action_snapshot("open Wikipedia")
    assert len(snapshot["music_titles"]) == 20
    assert len(snapshot["websites"]) <= 16
    assert any("wikipedia" in site["title"].casefold() for site in snapshot["websites"])


def test_timer_and_player_actions_are_silent(app):
    app.execute_chat_action({"name": "timer_set", "seconds": 60})
    app.execute_chat_action({"name": "music_close"})
    app._start_reminder.assert_called_once_with(60)
    app._close_music_player_window.assert_called_once()
    app.speak.assert_not_called()
    app.close_chat_mode.assert_not_called()


def test_timer_replacement_requires_confirmation(app):
    app._reminder_end_at = 123
    with pytest.raises(ValueError, match="replace"):
        app.execute_chat_action({"name": "timer_set", "seconds": 60})
    app._start_reminder.assert_not_called()
    assert app.confirm_pending_chat_action("yes") == {"name": "timer_change", "seconds": 60}


def test_timer_confirmation_expires_when_timer_changes(app):
    app._reminder_end_at = 123
    with pytest.raises(ValueError):
        app.execute_chat_action({"name": "timer_set", "seconds": 60})
    app._reminder_id += 1
    assert app.confirm_pending_chat_action("yes") is None


def test_request_must_match_session_and_phase(app):
    assert app.chat_request_current((1, 1), "planning")
    assert not app.chat_request_current((2, 1), "planning")
    assert not app.chat_request_current((1, 2), "planning")
    app._chat_action_phase = "executing"
    assert not app.chat_request_current((1, 1), "planning")
    app._chat_mode = False
    assert not app.chat_request_current((1, 1), "executing")


@pytest.mark.parametrize("state", ["closed", "new_session", "new_request", "already_done"])
def test_late_or_duplicate_plans_do_not_execute(app, state):
    app._generate_chat_action_reply = MagicMock()
    action_plan = parse_action_plan(plan({"name": "music_close"}))
    if state == "closed":
        app._chat_mode = False
    elif state == "new_session":
        app._chat_session_id += 1
    elif state == "new_request":
        app._chat_request_id += 1
    else:
        app._chat_action_phase = "done"
    app._apply_chat_action_plan((1, 1), [], "close player", action_plan)
    app._close_music_player_window.assert_not_called()
    app._generate_chat_action_reply.assert_not_called()


def test_duplicate_plan_executes_once(app):
    app._generate_chat_action_reply = MagicMock()
    action_plan = parse_action_plan(plan({"name": "music_close"}))
    for _ in range(2):
        app._apply_chat_action_plan((1, 1), [], "close player", action_plan)
    app._close_music_player_window.assert_called_once()


def test_action_failure_stops_remaining_actions(app):
    app._generate_chat_action_reply = MagicMock()
    app._reminder_end_at = 123
    action_plan = parse_action_plan(plan(
        {"name": "timer_set", "seconds": 60}, {"name": "music_close"},
    ))
    app._apply_chat_action_plan((1, 1), [], "set timer and close player", action_plan)
    app._close_music_player_window.assert_not_called()
    assert "not completed" in app._generate_chat_action_reply.call_args.args[-1][0]


def test_clarification_has_no_side_effects(app):
    app._generate_chat_action_reply = MagicMock()
    app._apply_chat_action_plan((1, 1), [], "timer", parse_action_plan(plan(question="How long?")))
    app._start_reminder.assert_not_called()
    assert app._chat_action_phase == "answering"


def test_note_action_uses_exact_text(app):
    app.create_chat_note = MagicMock()
    app.execute_chat_action({"name": "note_create", "text": "Milk\nBread", "title": "Shopping"})
    app.create_chat_note.assert_called_once_with("Shopping", "Milk\nBread")
    app.speak.assert_not_called()


def test_known_since_uses_stored_date(app):
    app._memory = MagicMock()
    app._memory.get_fact.return_value = "2020-01-01"
    result = app.execute_chat_action({"name": "known_since"})
    assert "known each other" in result
    assert "not available" not in result
    app._memory.get_fact.assert_called_once_with("first_met")


@pytest.mark.parametrize("failure", [None, "invalid_plan", "answer_error", "planner_error"])
def test_background_pipeline_delivers_only_final_text(app, monkeypatch, failure):
    workers, callbacks = [], []
    app.root = MagicMock()
    app.root.after.side_effect = lambda delay, callback: callbacks.append(callback)
    app._ollama_client = MagicMock()
    app._ollama_client.plan_chat_actions.return_value = plan({"name": "note_create", "title": "", "text": "Milk"})
    app._ollama_client.chat.return_value = "The note is saved."
    app.create_chat_note = MagicMock()
    app._on_chat_response = MagicMock()
    if failure == "invalid_plan":
        app._ollama_client.plan_chat_actions.return_value = '{"actions":[{"name":"bad"}],"question":""}'
    if failure == "planner_error":
        app._ollama_client.plan_chat_actions.side_effect = RuntimeError("failure")
    if failure == "answer_error":
        app._ollama_client.chat.side_effect = RuntimeError("failure")

    def thread(*, target, daemon):
        obj = MagicMock()
        obj.start.side_effect = lambda: workers.append(target)
        return obj

    monkeypatch.setattr("kinito.features.chat_actions.threading.Thread", thread)
    app.begin_chat_action_request((1, 1), [{"role": "user", "content": "create a note: Milk"}], "create a note: Milk", {})
    app.create_chat_note.assert_not_called()
    workers.pop(0)()
    app.create_chat_note.assert_not_called()
    callbacks.pop(0)()
    if failure in {"invalid_plan", "planner_error"}:
        app.create_chat_note.assert_not_called()
    else:
        app.create_chat_note.assert_called_once_with("", "Milk")
    if workers:
        workers.pop(0)()
        callbacks.pop(0)()
    app._on_chat_response.assert_called_once()
    assert '"actions"' not in app._on_chat_response.call_args.args[0]
    assert app._chat_action_phase == "done"
    app.speak.assert_not_called()
    app.close_chat_mode.assert_not_called()


def test_music_reply_uses_actual_track_not_model_invention(app):
    app._user_music_path = r"C:\Music\NewBeginningsPoemEdit.mp3"
    app._music_paused = False
    app._user_music_is_active = lambda: True
    app.control_music_from_chat = MagicMock(return_value="Requested music resume.")
    app._ollama_client = MagicMock()
    app._ollama_client.chat.return_value = "assistant\nThe Gorillaz song is playing again."
    app._on_chat_response = MagicMock()
    app._apply_chat_action_plan((1, 1), [], "can you resume it?", parse_action_plan(plan({"name": "music_play"})))
    app._on_chat_response.assert_called_once()
    reply = app._on_chat_response.call_args.args[0]
    assert "NewBeginningsPoemEdit" in reply
    assert "Gorillaz" not in reply
    app._ollama_client.chat.assert_not_called()


@pytest.mark.parametrize("text", ["now reddit pls!", "jetzt Reddit bitte", "and now Reddit please"])
def test_browser_followup_does_not_reopen_previous_site(text):
    action_plan, _ = direct_browser_plan(text, browser_context=True)
    assert action_plan.actions == []
    assert "address" in action_plan.question
    assert direct_browser_plan(text) is None


def test_browser_context_is_recorded_only_after_success(app):
    app._chat_action_phase = "browser"
    app._run_next_chat_action = MagicMock()
    app._finish_chat_browser((1, 1), [], "Open Wikipedia", [], [], "Sent address", False)
    assert app._last_chat_browser_request == (1, 1)


def test_named_external_site_requires_address_without_inventing_success():
    action_plan, _ = direct_browser_plan("Could you open Reddit pls")
    assert not action_plan.actions
    assert "address" in action_plan.question


@pytest.mark.parametrize("text", ["Open https://example.org", "Could you open example.org pls"])
def test_direct_external_address_becomes_real_action(text):
    action_plan, authorized_text = direct_browser_plan(text)
    assert action_plan.actions == [{"name": "website_open", "url": "https://example.org"}]
    assert resolve_browser_url(action_plan.actions[0]["url"], authorized_text) == ("https://example.org", True)


@pytest.mark.parametrize("text", [
    "open https://deadbydaylight.com/ in the browser",
    "Could you open https://deadbydaylight.com/ in my default browser please?",
    "Open https://deadbydaylight.com/ in the browser, please.",
    "Öffne https://deadbydaylight.com/ im Browser bitte",
    "Kannst du https://deadbydaylight.com/ im Browser öffnen?",
])
def test_exact_external_url_with_browser_phrase_is_not_treated_as_site_name(text):
    action_plan, authorized_text = direct_browser_plan(text)
    assert action_plan.actions == [{"name": "website_open", "url": "https://deadbydaylight.com/"}]
    assert resolve_browser_url(action_plan.actions[0]["url"], authorized_text) == ("https://deadbydaylight.com/", True)


def test_exact_external_url_reaches_browser_once_without_model_rewriting(browser_actions):
    app, workers, callbacks = browser_actions
    app._ollama_client = MagicMock()
    app.begin_chat_action_request((1, 1), [], "open https://deadbydaylight.com/ in the browser", {})
    while workers or callbacks:
        if workers:
            workers.pop(0)()
        if callbacks:
            callbacks.pop(0)()
    app.open_chat_website.assert_called_once_with("https://deadbydaylight.com/", True, (0, 0))
    app._ollama_client.plan_chat_actions.assert_not_called()
    app._ollama_client.chat.assert_not_called()


def test_url_words_are_not_interpreted_as_negation_or_multiple_commands():
    url = "https://example.org/not/and?q=bread#part"
    action_plan, _ = direct_browser_plan("Open " + url + " in the browser")
    assert action_plan.actions == [{"name": "website_open", "url": url}]


def test_browser_phrase_does_not_authorize_negated_request():
    assert direct_browser_plan("Open https://example.org/ not in the browser") is None


@pytest.mark.parametrize("request_text,previous_browser", [
    ("Could you open Reddit pls", None), ("now reddit pls!", (1, 0)),
])
def test_named_site_then_supplied_address_opens_browser_without_model_claims(app, monkeypatch, request_text, previous_browser):
    workers, callbacks = [], []
    app.root = MagicMock()
    app.root.after.side_effect = lambda delay, callback: callbacks.append(callback)
    app._ollama_client = MagicMock()
    app._on_chat_response = MagicMock()
    app.open_chat_website = MagicMock(return_value="Address handed to the system browser.")

    def thread(*, target, daemon):
        obj = MagicMock()
        obj.start.side_effect = lambda: workers.append(target)
        return obj

    monkeypatch.setattr("kinito.features.chat_actions.threading.Thread", thread)
    app._last_chat_browser_request = previous_browser
    app.begin_chat_action_request((1, 1), [], request_text, {})
    workers.pop(0)()
    callbacks.pop(0)()
    app.open_chat_website.assert_not_called()
    assert app._pending_chat_website == 1
    assert "address" in app._on_chat_response.call_args.args[0]

    app._chat_request_id = 2
    app._chat_action_phase = "planning"
    app.begin_chat_action_request((1, 2), [], "example.org", {})
    workers.pop(0)()
    callbacks.pop(0)()
    workers.pop(0)()
    callbacks.pop(0)()
    app.open_chat_website.assert_called_once_with("https://example.org", True, (0, 0))
    app._ollama_client.plan_chat_actions.assert_not_called()
    app._ollama_client.chat.assert_not_called()
    assert app._on_chat_response.call_args.args[0] == "Address handed to the system browser."


def test_url_only_reply_requires_pending_address_question():
    assert direct_browser_plan("https://example.org") is None
    action_plan, _ = direct_browser_plan("https://example.org", awaiting_url=True)
    assert action_plan.actions[0]["name"] == "website_open"


@pytest.mark.parametrize("text", [
    "Could you open the music player pls", "He said open https://example.org",
    "Don't open https://example.org", "Erstelle eine Notiz: open https://example.org",
])
def test_direct_browser_routing_does_not_consume_other_requests(text):
    assert direct_browser_plan(text) is None


def test_music_state_does_not_infer_artist_from_filename(app):
    app._user_music_path = r"C:\Music\Some Song.mp3"
    state = app.current_chat_music_state()
    assert state["track"] == "Some Song"
    assert state["artist"] is None


def test_confirmation_cannot_replace_a_newer_timer(app):
    app._chat_action_phase = "executing"
    app._reminder_end_at = 999
    app._confirmed_chat_timer = ((1, 1), 0, 123)
    app._generate_chat_action_reply = MagicMock()
    app._run_next_chat_action((1, 1), [], "yes", [{"name": "timer_change", "seconds": 60}], [])
    app._start_reminder.assert_not_called()


@pytest.mark.parametrize(("text", "seconds"), [
    ("Stelle einen Timer", None), ("Set a timer for 5", None),
    ("Timer auf 5 Minuten", 300), ("Timer auf fünf Minuten", 300),
    ("1h 30m", 5400), ("45 seconds", 45), ("1,5 Minuten", 90),
    ("Timer 1:30", 90), ("Timer 1:02:03", 3723),
    ("-5 minutes", None), ("99999999 hours", None),
    ("45 Sek.", 45), ("1 Std.", 3600), ("half an hour", 1800), ("einer Stunde", 3600),
])
def test_timer_duration_must_be_explicit(text, seconds):
    assert requested_timer_seconds(text) == seconds


def test_invented_timer_duration_cannot_execute(app):
    app._generate_chat_action_reply = MagicMock()
    action_plan = parse_action_plan(plan({"name": "timer_set", "seconds": 3600}))
    app._apply_chat_action_plan((1, 1), [], "Stelle einen Timer", action_plan)
    app._start_reminder.assert_not_called()
    assert "specify" in app._generate_chat_action_reply.call_args.args[-1][0]


def test_misconverted_timer_duration_cannot_execute(app):
    app._generate_chat_action_reply = MagicMock()
    action_plan = parse_action_plan(plan({"name": "timer_set", "seconds": 5}))
    app._apply_chat_action_plan((1, 1), [], "Stelle einen Timer auf 5 Minuten", action_plan)
    app._start_reminder.assert_not_called()


def test_timer_change_cannot_be_inferred_from_stale_yes(app):
    app._chat_action_phase = "executing"
    app._generate_chat_action_reply = MagicMock()
    app._run_next_chat_action((1, 1), [], "yes", [{"name": "timer_change", "seconds": 60}], [])
    app._start_reminder.assert_not_called()
