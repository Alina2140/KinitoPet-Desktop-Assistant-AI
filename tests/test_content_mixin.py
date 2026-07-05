from unittest.mock import ANY, MagicMock, patch

import pytest

from content import dialogue as dlg
from content import llm_prompts as prompts
from content.facts import FACTS
from content.questions import QUESTIONS
from content.stories import STORIES
from kinito.assets import newbeginnings_file_path
from kinito.features.content import ContentMixin
from kinito.speech import SpeechMixin


class ContentStub(ContentMixin):
    pass


@pytest.fixture
def content():
    stub = ContentStub()
    stub._can_initiate_spontaneous_speech = MagicMock(return_value=True)
    stub.speak = MagicMock()
    stub.speak_whisper = MagicMock()
    stub.play_mp3 = MagicMock()
    stub._pending_story = None
    stub._running = True
    stub.paused = False
    stub.talking = False
    stub._fancy_mode = False
    stub.tk_img_fancy = "fancy"
    stub.change_sprite = MagicMock()
    for name in (
        "print_current_datetime",
        "offer_browser_visit",
        "offer_random_music",
        "offer_game_picker",
        "give_hug",
        "spontaneous_nap",
    ):
        setattr(stub, name, MagicMock())
    return stub


def test_speak_random_question_respects_gate(content):
    content._can_initiate_spontaneous_speech.return_value = False
    content.speak_random_question()
    content.speak.assert_not_called()


def test_perform_random_menu_action_respects_gate(content):
    content._can_initiate_spontaneous_speech.return_value = False
    with patch("kinito.features.content.random.choice") as choice:
        content.perform_random_menu_action()
    choice.assert_not_called()


def test_perform_random_menu_action_calls_one_handler(content):
    action = MagicMock()
    with patch("kinito.features.content.random.choice", return_value=action):
        content.perform_random_menu_action()
    action.assert_called_once()


def test_speak_random_question_speaks_from_pool(content):
    with patch("kinito.features.content.random.choice", return_value=dlg.DAY_QUESTIONS[0]):
        content.speak_random_question()
    content.speak.assert_called_once_with(dlg.DAY_QUESTIONS[0], 45, True)


def test_available_questions_skip_camera_while_active(content):
    content._camera_active = True
    pool = content._available_spontaneous_questions()
    assert all(dlg.CAMERA_QUESTION_MARKER not in q.lower() for q in pool)
    assert len(pool) < len(QUESTIONS)


def test_say_random_poem_whisper(content):
    poem = {"text": "secret poem", "whisper": True, "play_music": False}
    with patch("kinito.features.content.random.choice", return_value=poem):
        content.say_random_poem()
    content.speak_whisper.assert_called_once_with(
        "secret poem", long_bubble=True, ai_hint=ANY
    )


def test_say_random_poem_plays_music_and_uses_normal_voice(content):
    poem = {"text": "loud poem", "whisper": False, "play_music": True}
    with patch("kinito.features.content.random.choice", return_value=poem):
        content.say_random_poem()
    content.play_mp3.assert_called_once_with(
        newbeginnings_file_path,
        volume=ContentMixin.POEM_BACKGROUND_MUSIC_VOLUME,
    )
    content.speak.assert_called_once_with(
        "loud poem",
        pitch=45,
        long_bubble=True,
        voice_candidates=SpeechMixin.VOICE_NORMAL_CANDIDATES,
        ai_hint=ANY,
    )


def test_offer_random_story_sets_pending(content):
    with patch(
        "kinito.features.content.random.choice", side_effect=[STORIES[0], dlg.STORY_QUESTIONS[0]]
    ):
        content.offer_random_story()
    assert content._pending_story == STORIES[0]
    content.speak.assert_called_once()


def test_say_pending_story_clears_pending(content):
    content._pending_story = STORIES[1]
    content.say_pending_story()
    assert content._pending_story is None
    content.speak.assert_called_once_with(STORIES[1], ai_hint=ANY)


def test_say_random_fact(content):
    with patch("kinito.features.content.get_random_fact", return_value=FACTS[0]):
        content.say_random_fact()
    content.speak.assert_called_once_with(FACTS[0], ai_hint=ANY)


def test_say_random_joke(content):
    joke = dlg.JOKES[0]
    with patch("kinito.features.content.dlg.pick_line", return_value=joke):
        content.say_random_joke()
    content.speak.assert_called_once_with(joke, ai_hint=prompts.JOKE_PROMPT)


def test_run_fancy_idle_cycles_sprites_during_speech(content):
    content.tk_img_fancy_2 = "fancy2"
    content._magician_sprites = ("fancy", "fancy2")
    content.perform_fancy_show = MagicMock()

    def fake_sleep(_seconds):
        if content.change_sprite.call_count == 2:
            content.talking = True
        elif content.change_sprite.call_count >= 4:
            content.talking = False

    with patch("kinito.features.content.time.sleep", side_effect=fake_sleep):
        content._run_fancy_idle()

    sprite_calls = [call.args[0] for call in content.change_sprite.call_args_list]
    assert sprite_calls[0] == "fancy"
    assert "fancy2" in sprite_calls
    assert content.change_sprite.call_count >= 3
    assert content._fancy_mode is False
