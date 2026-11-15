"""Tests for the Ollama LLM mixin."""

from unittest.mock import MagicMock, patch

import pytest

from kinito.features.llm import LLMMixin
from kinito.llm.config import LLMConfig
from kinito.llm.ollama_client import OllamaUnavailableError
from kinito.speech import SpeechMixin


class LLMStub(LLMMixin, SpeechMixin):
    pass


@pytest.fixture
def llm_app():
    app = LLMStub()
    app.root = MagicMock()
    app._delayed_callbacks = []

    def after(delay, fn, *args):
        if delay == 0:
            return fn(*args)
        app._delayed_callbacks.append(lambda: fn(*args))
        return f"timer-{len(app._delayed_callbacks)}"

    app.root.after = after
    app.talking = False
    app._awaiting_response = False
    app._speech_epoch = 0
    app._speech_lock = MagicMock()
    app._speech_lock.__enter__ = MagicMock(return_value=None)
    app._speech_lock.__exit__ = MagicMock(return_value=False)
    app._llm_config = LLMConfig(
        enabled=True,
        idle_lines=True,
        idle_chance=1.0,
        replace_chance=1.0,
    )
    app._ollama_client = MagicMock()
    app._ollama_client.is_available.return_value = True
    app._ollama_client.chat.return_value = "Hello friend!"
    app._ollama_client.generate.return_value = "Just checking in on you."
    app._init_chat_state()
    app._memory = MagicMock()
    app._memory.get_fact.return_value = None
    app._memory.pick_user_name.return_value = None
    app._memory.as_prompt_block.return_value = ""
    app._memory.user_display_name.return_value = "You"
    app.chat_user_label = MagicMock(return_value="You")
    app._pin_chat_user_label = MagicMock(return_value="You")
    app.memory_prompt_block = MagicMock(return_value="")
    app._memory_extractor = MagicMock()
    app._last_chat_user_text = ""
    app._conversation = MagicMock()
    app._conversation.messages_for_api.return_value = [{"role": "user", "content": "Hi"}]
    app._conversation.reset = MagicMock()
    app._conversation.add_user = MagicMock()
    app._conversation.add_assistant = MagicMock()
    app.open_chat_bubble = MagicMock()
    app.open_chat_mode_picker = MagicMock()
    app.append_chat_message = MagicMock()
    app.set_chat_generating = MagicMock()
    app.speak_chat_response = MagicMock()
    app._can_initiate_spontaneous_speech = MagicMock(return_value=True)
    app._chat_mode = False
    app._chat_generating = False
    app._ai_generating = False
    return app


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('Kinito:"Hello friend!"', "Hello friend!"),
        ('  kinito : "Hello friend!"  ', "Hello friend!"),
        ('Kinito: “Hello friend!”', "Hello friend!"),
        ('Kinito: „Hallo!“', "Hallo!"),
        ("Kinito: 'Hello!'", "Hello!"),
        ("Kinito: Hello friend!", "Hello friend!"),
        ('Hello, "friend"!', 'Hello, "friend"!'),
        ("I am Kinito: your desktop friend.", "I am Kinito: your desktop friend."),
        ("Kinito is here!", "Kinito is here!"),
        ("Kinito:", ""),
    ],
)
def test_clean_generated_speech(raw, expected):
    assert LLMMixin._clean_generated_speech(raw) == expected


def test_chat_response_removes_speaker_label(llm_app):
    llm_app._chat_mode = True
    llm_app._on_chat_response('Kinito: "Hello friend!"')
    llm_app._conversation.add_assistant.assert_called_once_with("Hello friend!")
    llm_app.speak_chat_response.assert_called_once_with("Hello friend!")


def test_append_memory_context_omits_facts_for_poem_replacement(llm_app):
    llm_app._memory.pick_user_name.return_value = "Ben"
    prompt = llm_app._append_memory_context(
        "Say something fun.",
        scripted_text="Why did the chicken cross the road?",
        ai_hint=None,
    )
    assert "Cherry Cola" not in prompt
    assert "favorite_drink" not in prompt
    assert prompt == "Say something fun."


def test_append_memory_context_includes_name_for_idle_prompt(llm_app):
    from content import llm_prompts as prompts

    llm_app._memory.pick_user_name.return_value = "Ben"
    prompt = llm_app._append_memory_context(
        prompts.IDLE_PROMPT,
        scripted_text="",
        ai_hint=prompts.IDLE_PROMPT,
    )
    assert "The user's name is Ben." in prompt
    assert "favorite_drink" not in prompt
    llm_app.start_chat()
    llm_app._conversation.reset.assert_called_once()
    llm_app.open_chat_mode_picker.assert_called_once()
    llm_app.open_chat_bubble.assert_not_called()


def test_append_memory_context_omits_name_for_random_question(llm_app):
    from content import llm_prompts as prompts

    llm_app._memory.pick_user_name.return_value = "Alina"
    prompt = llm_app._append_memory_context(
        prompts.RANDOM_QUESTION_PROMPT,
        scripted_text="",
        ai_hint=prompts.RANDOM_QUESTION_PROMPT,
    )
    assert "Alina" not in prompt
    assert prompt == prompts.RANDOM_QUESTION_PROMPT


def test_generation_system_prompt_omits_memory_for_idle_hints(llm_app):
    from content import llm_prompts as prompts

    llm_app.memory_prompt_block.return_value = "Known facts about the user:\n- user name: Alina"
    idle_system = llm_app._generation_system_prompt(prompts.RANDOM_QUESTION_PROMPT)
    assert "Alina" not in idle_system
    assert idle_system == prompts.SYSTEM_PROMPT

    chat_system = llm_app._generation_system_prompt(prompts.POEM_PROMPT)
    assert "Alina" in chat_system


@patch.object(SpeechMixin, "speak")
def test_start_chat_fallback_when_unavailable(mock_speak, llm_app):
    llm_app._ollama_client.is_available.return_value = False
    llm_app.start_chat()
    mock_speak.assert_called_once()
    llm_app.open_chat_mode_picker.assert_not_called()
    llm_app.open_chat_bubble.assert_not_called()


def test_send_chat_message_calls_ollama_and_updates_ui(llm_app):
    llm_app._chat_mode = True

    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        thread_cls.return_value = MagicMock()
        llm_app.send_chat_message("Hello")

        thread_cls.assert_called_once()
        worker = thread_cls.call_args.kwargs["target"]
        worker()

    llm_app._conversation.add_user.assert_called_once_with("Hello")
    llm_app.append_chat_message.assert_called()
    llm_app._conversation.add_assistant.assert_called_once_with("Hello friend!")
    llm_app.speak_chat_response.assert_called_once_with("Hello friend!")


def test_send_chat_message_error_shows_fallback(llm_app):
    llm_app._chat_mode = True
    llm_app._ollama_client.chat.side_effect = OllamaUnavailableError("down")

    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        thread_cls.return_value = MagicMock()
        llm_app.send_chat_message("Hello")
        thread_cls.call_args.kwargs["target"]()

    llm_app.speak_chat_response.assert_called_once()


def test_should_use_ai_idle_line_requires_availability(llm_app):
    llm_app._chat_mode = False
    assert llm_app._should_use_ai_idle_line() is True
    llm_app._ollama_client.is_available.return_value = False
    assert llm_app._should_use_ai_idle_line() is False


def test_activate_pending_visuals_starts_hug(llm_app):
    llm_app._begin_hug_after_speech = True
    llm_app._enter_hug_pose = MagicMock()
    llm_app._activate_pending_visuals()
    llm_app._enter_hug_pose.assert_called_once()
    assert llm_app._begin_hug_after_speech is False


@patch.object(SpeechMixin, "speak")
def test_speak_ai_idle_line_fallback_on_error(mock_speak, llm_app):
    llm_app._ollama_client.generate.side_effect = OllamaUnavailableError("down")

    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        thread_cls.return_value = MagicMock()
        llm_app.speak_ai_idle_line()
        thread_cls.call_args.kwargs["target"]()

    mock_speak.assert_called_once()
    assert mock_speak.call_args.args[0]
    assert llm_app._ai_generating is False


def test_memory_question_delivered_after_thinking(llm_app):
    from kinito.memory.questions import MemoryQuestion

    question = MemoryQuestion("What is your favorite color?", "textbox", "favorite_color")
    llm_app._memory_question_planner = MagicMock()
    llm_app._memory_question_planner.plan.return_value = question
    llm_app.ask_memory_question = MagicMock()
    llm_app._can_initiate_spontaneous_speech = lambda: not llm_app._is_busy_with_speech()
    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        llm_app.speak_ai_memory_question()
        assert llm_app.talking is True
        thread_cls.call_args.kwargs["target"]()
    llm_app.ask_memory_question.assert_called_once_with(question)
    assert llm_app._planning_memory_question is False
    assert llm_app._ai_generating is False


@pytest.mark.parametrize("failure_stage", ["prompt", "generation"])
@patch.object(SpeechMixin, "speak")
def test_unexpected_generation_error_uses_fallback(mock_speak, llm_app, failure_stage):
    if failure_stage == "prompt":
        llm_app._build_generation_prompt = MagicMock(side_effect=ValueError("bad context"))
    else:
        llm_app._ollama_client.generate.side_effect = ValueError("bad response")
    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        llm_app._generate_and_speak("scripted fallback")
        thread_cls.call_args.kwargs["target"]()
    mock_speak.assert_called_once()
    assert mock_speak.call_args.args[0] == "scripted fallback"
    assert llm_app._ai_generating is False
    assert llm_app.talking is False
    assert llm_app._talk_sprite_mode == "talking"


@patch.object(SpeechMixin, "speak")
def test_generation_timeout_speaks_fallback_only_once(mock_speak, llm_app):
    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        llm_app._generate_and_speak("scripted fallback")
        worker = thread_cls.call_args.kwargs["target"]
    llm_app._delayed_callbacks[-1]()
    mock_speak.assert_called_once()
    assert mock_speak.call_args.args[0] == "scripted fallback"
    assert llm_app._ai_generating is False
    assert llm_app.talking is False
    worker()
    mock_speak.assert_called_once()


@pytest.mark.parametrize("kind", ["line", "memory"])
@patch.object(SpeechMixin, "speak")
def test_generated_result_waits_until_drag_ends(mock_speak, llm_app, kind):
    llm_app._memory_question_planner = MagicMock()
    llm_app.ask_memory_question = MagicMock()
    llm_app._can_initiate_spontaneous_speech = lambda: not llm_app._is_busy_with_speech()
    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        if kind == "line":
            llm_app._generate_and_speak("fallback")
        else:
            llm_app.speak_ai_memory_question()
        llm_app.is_dragging = True
        thread_cls.call_args.kwargs["target"]()
    mock_speak.assert_not_called()
    llm_app.ask_memory_question.assert_not_called()
    assert llm_app._ai_generating is True
    assert llm_app._ai_generation_timer is None
    llm_app._resume_pending_ai_delivery()
    mock_speak.assert_not_called()
    llm_app.ask_memory_question.assert_not_called()
    llm_app.is_dragging = False
    llm_app._resume_pending_ai_delivery()
    llm_app._resume_pending_ai_delivery()
    if kind == "line":
        mock_speak.assert_called_once()
        assert mock_speak.call_args.args[0] == "Just checking in on you."
    else:
        llm_app.ask_memory_question.assert_called_once_with(
            llm_app._memory_question_planner.plan.return_value
        )
    assert llm_app._ai_generating is False
    assert llm_app._planning_memory_question is False


@patch.object(SpeechMixin, "speak")
def test_pending_line_survives_timeout_and_waits_for_throw(mock_speak, llm_app):
    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        llm_app._generate_and_speak("fallback")
        timeout = llm_app._delayed_callbacks[-1]
        llm_app.is_dragging = True
        thread_cls.call_args.kwargs["target"]()
    timeout()
    llm_app.is_dragging = False
    llm_app._throwing = True
    llm_app._resume_pending_ai_delivery()
    mock_speak.assert_not_called()
    llm_app._throwing = False
    llm_app._resume_pending_ai_delivery()
    mock_speak.assert_called_once()
    assert mock_speak.call_args.args[0] == "Just checking in on you."


@patch.object(SpeechMixin, "speak")
def test_interrupt_discards_result_waiting_for_release(mock_speak, llm_app):
    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        llm_app._generate_and_speak("fallback")
        llm_app.is_dragging = True
        thread_cls.call_args.kwargs["target"]()
    llm_app.interrupt_speech()
    llm_app.is_dragging = False
    llm_app._resume_pending_ai_delivery()
    mock_speak.assert_not_called()
    assert llm_app._pending_ai_delivery is None
    assert llm_app._ai_delivery_timer is None


@pytest.mark.parametrize("blocked_state", ["paused", "_focus_mode", "_game_active"])
@patch.object(SpeechMixin, "speak")
def test_pending_line_respects_changed_mode(mock_speak, llm_app, blocked_state):
    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        llm_app._generate_and_speak("fallback")
        llm_app.is_dragging = True
        thread_cls.call_args.kwargs["target"]()
    setattr(llm_app, blocked_state, True)
    if blocked_state == "_game_active":
        llm_app._is_game_active = lambda: True
    llm_app.is_dragging = False
    llm_app._delayed_callbacks[-1]()
    mock_speak.assert_not_called()
    assert llm_app._ai_generating is False
    assert llm_app._pending_ai_delivery is None


@patch.object(SpeechMixin, "speak")
def test_new_generation_replaces_pending_line(mock_speak, llm_app):
    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        llm_app._generate_and_speak("first fallback")
        llm_app.is_dragging = True
        llm_app._ollama_client.generate.return_value = "first result"
        thread_cls.call_args.kwargs["target"]()
        old_delivery = llm_app._delayed_callbacks[-1]
        llm_app._generate_and_speak("second fallback")
        llm_app._ollama_client.generate.return_value = "second result"
        thread_cls.call_args.kwargs["target"]()
    llm_app.is_dragging = False
    llm_app._delayed_callbacks[-1]()
    old_delivery()
    mock_speak.assert_called_once()
    assert mock_speak.call_args.args[0] == "second result"


@patch.object(SpeechMixin, "speak")
def test_generation_uses_nonempty_fallback(mock_speak, llm_app):
    llm_app._ollama_client.generate.return_value = "Kinito:"
    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        llm_app._generate_and_speak("")
        thread_cls.call_args.kwargs["target"]()
    assert mock_speak.call_args.args[0].strip()


@patch.object(SpeechMixin, "speak")
def test_stale_generation_does_not_clear_new_thinking_state(mock_speak, llm_app):
    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        llm_app._generate_and_speak("first")
        first_worker = thread_cls.call_args.kwargs["target"]
        first_timeout = llm_app._delayed_callbacks[-1]
        llm_app._generate_and_speak("second")
        second_worker = thread_cls.call_args.kwargs["target"]
    first_worker()
    first_timeout()
    mock_speak.assert_not_called()
    assert llm_app._ai_generating is True
    assert llm_app.talking is True
    second_worker()
    mock_speak.assert_called_once()
    assert llm_app._ai_generating is False


def test_memory_question_timeout_uses_template_and_ignores_late_plan(llm_app):
    llm_app._memory_question_planner = MagicMock()
    template = llm_app._memory_question_planner.plan_template.return_value
    llm_app.ask_memory_question = MagicMock()
    llm_app._can_initiate_spontaneous_speech = lambda: not llm_app._is_busy_with_speech()
    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        llm_app.speak_ai_memory_question()
        worker = thread_cls.call_args.kwargs["target"]
    llm_app._delayed_callbacks[-1]()
    llm_app.ask_memory_question.assert_called_once_with(template)
    assert llm_app._planning_memory_question is False
    assert llm_app.talking is False
    worker()
    llm_app.ask_memory_question.assert_called_once()


def test_interruption_cancels_memory_planning_and_discards_late_result(llm_app):
    llm_app._memory_question_planner = MagicMock()
    llm_app.ask_memory_question = MagicMock()
    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        llm_app.speak_ai_memory_question()
        worker = thread_cls.call_args.kwargs["target"]
    llm_app.interrupt_speech()
    assert llm_app._ai_generating is False
    assert llm_app._planning_memory_question is False
    assert llm_app._ai_generation_timer is None
    llm_app.talking = True
    worker()
    llm_app.ask_memory_question.assert_not_called()
    assert llm_app.talking is True


@patch.object(SpeechMixin, "speak")
def test_template_error_leaves_no_thinking_state(mock_speak, llm_app):
    llm_app._memory_question_planner = MagicMock()
    llm_app._memory_question_planner.plan.side_effect = ValueError("bad plan")
    llm_app._memory_question_planner.plan_template.side_effect = ValueError("bad template")
    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        llm_app.speak_ai_memory_question()
        thread_cls.call_args.kwargs["target"]()
    mock_speak.assert_called_once()
    assert mock_speak.call_args.args[0].strip()
    assert llm_app._planning_memory_question is False
    assert llm_app._ai_generating is False
    assert llm_app.talking is False


@patch.object(SpeechMixin, "speak")
def test_generate_and_speak_shows_thinking_sprite(mock_speak, llm_app):
    llm_app.change_sprite = MagicMock()
    llm_app.tk_img_thinking = "thinking"

    with patch("kinito.features.llm.threading.Thread") as thread_cls:
        thread_cls.return_value = MagicMock()
        llm_app._generate_and_speak("fallback", ai_hint="say hi")

    llm_app.change_sprite.assert_called_with("thinking")
    assert llm_app._talk_sprite_mode == "thinking"
    assert llm_app._ai_generating is True


def test_show_ai_thinking_sprite_skips_override_during_dizzy(llm_app):
    llm_app.change_sprite = MagicMock()
    llm_app.tk_img_thinking = "thinking"
    llm_app._dizzy_mode = True
    llm_app._show_ai_thinking_sprite()
    llm_app.change_sprite.assert_not_called()
    assert llm_app._ai_generating is True


@patch.object(SpeechMixin, "speak")
def test_speak_skips_ai_for_interactive_dialog(mock_speak, llm_app):
    with patch("kinito.features.llm.find_dialog_spec", return_value=object()):
        llm_app.speak("Want to play a game?", 45, True)

    mock_speak.assert_called_once()
    assert "skip_ai" not in mock_speak.call_args.kwargs


@pytest.mark.parametrize("long_bubble,budget", [(False, 256), (True, 1024)])
@pytest.mark.parametrize("speaker_label", [False, True])
@patch.object(SpeechMixin, "speak")
def test_speak_uses_ai_for_plain_lines(mock_speak, llm_app, long_bubble, budget, speaker_label):
    reply = "Just checking in on you and your wonderful little world. " * 12
    llm_app._ollama_client.generate.return_value = f'Kinito: "{reply}"' if speaker_label else reply
    with patch("kinito.features.llm.find_dialog_spec", return_value=None):
        with patch("kinito.features.llm.threading.Thread") as thread_cls:
            thread_cls.return_value = MagicMock()
            llm_app.speak("Hello there!", long_bubble=long_bubble)
            thread_cls.call_args.kwargs["target"]()

    mock_speak.assert_called_once()
    assert mock_speak.call_args.args[0] == reply.strip()
    assert llm_app._ollama_client.generate.call_args.kwargs["max_tokens"] == budget


@patch.object(SpeechMixin, "speak")
def test_speak_blocked_during_game_for_plain_lines(mock_speak, llm_app):
    llm_app._is_game_active = MagicMock(return_value=True)
    with patch("kinito.features.llm.find_dialog_spec", return_value=None):
        llm_app.speak("Hello there!")

    mock_speak.assert_not_called()


@patch.object(SpeechMixin, "speak")
def test_speak_allowed_during_paint_only(mock_speak, llm_app):
    llm_app._is_game_active = MagicMock(return_value=True)
    llm_app._is_paint_only_active = MagicMock(return_value=True)
    llm_app._should_ai_replace = MagicMock(return_value=False)
    with patch("kinito.features.llm.find_dialog_spec", return_value=None):
        llm_app.speak("Nice strokes!")

    mock_speak.assert_called_once()
    assert mock_speak.call_args.args[0] == "Nice strokes!"


@patch.object(SpeechMixin, "speak")
def test_deliver_generated_line_ignored_during_game(mock_speak, llm_app):
    llm_app._is_game_active = MagicMock(return_value=True)
    llm_app.close_speech_bubble = MagicMock()
    llm_app.talking = True

    llm_app._deliver_generated_line("Late AI line", {"show_bubble": True})

    llm_app.close_speech_bubble.assert_not_called()
    mock_speak.assert_not_called()
    assert llm_app.talking is False


@patch.object(SpeechMixin, "speak")
def test_deliver_generated_line_ignored_during_memory_question(mock_speak, llm_app):
    from kinito.memory.questions import MemoryQuestion

    llm_app._pending_memory_question = MemoryQuestion(
        "What is your favorite color?",
        "textbox",
        "favorite_color",
    )
    llm_app._awaiting_response = True
    llm_app.close_speech_bubble = MagicMock()
    llm_app.talking = True

    llm_app._deliver_generated_line("Late AI line", {"show_bubble": True})

    llm_app.close_speech_bubble.assert_not_called()
    mock_speak.assert_not_called()
    assert llm_app.talking is False


@patch.object(SpeechMixin, "speak")
def test_deliver_generated_line_ignored_during_focus_mode(mock_speak, llm_app):
    llm_app._focus_mode = True
    llm_app.close_speech_bubble = MagicMock()
    llm_app.talking = True
    llm_app._speech_epoch = 3

    llm_app._deliver_generated_line(
        "Late AI line",
        {"show_bubble": True},
        generation_epoch=3,
    )

    llm_app.close_speech_bubble.assert_not_called()
    mock_speak.assert_not_called()
    assert llm_app.talking is False


@patch.object(SpeechMixin, "speak")
def test_deliver_generated_line_ignored_when_speech_interrupted(mock_speak, llm_app):
    llm_app.close_speech_bubble = MagicMock()
    llm_app.talking = True
    llm_app._speech_epoch = 5

    llm_app._deliver_generated_line(
        "Stale AI line",
        {"show_bubble": True},
        generation_epoch=4,
    )

    llm_app.close_speech_bubble.assert_not_called()
    mock_speak.assert_not_called()
    assert llm_app.talking is True


@patch.object(SpeechMixin, "speak")
def test_speak_blocked_while_memory_question_pending(mock_speak, llm_app):
    from kinito.memory.questions import MemoryQuestion

    llm_app._pending_memory_question = MemoryQuestion(
        "Do you like coffee?",
        "textbox",
        "likes_coffee",
    )
    llm_app.speak("Random interruption!")
    mock_speak.assert_not_called()


@patch.object(SpeechMixin, "speak")
def test_should_ai_replace_false_during_game(mock_speak, llm_app):
    llm_app._is_game_active = MagicMock(return_value=True)
    assert llm_app._should_ai_replace("Correct! Nice one.") is False


@patch.object(SpeechMixin, "speak")
def test_speak_preserves_poem_accompaniment_through_ai(mock_speak, llm_app):
    llm_app.close_speech_bubble = MagicMock()

    with patch("kinito.features.llm.find_dialog_spec", return_value=None):
        with patch("kinito.features.llm.threading.Thread") as thread_cls:
            thread_cls.return_value = MagicMock()
            llm_app.speak(
                "Roses are red",
                long_bubble=True,
                speech_accompaniment_path="poem.mp3",
                speech_accompaniment_volume=0.75,
            )
            thread_cls.call_args.kwargs["target"]()

    mock_speak.assert_called_once()
    assert mock_speak.call_args.args[0] == "Just checking in on you."
    assert mock_speak.call_args.kwargs["speech_accompaniment_path"] == "poem.mp3"
    assert mock_speak.call_args.kwargs["speech_accompaniment_volume"] == 0.75
    assert mock_speak.call_args.kwargs["long_bubble"] is True
