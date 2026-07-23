"""Spontaneous questions, poems, facts, stories, and fancy idle performances."""

import random
import threading
import time

from content import dialogue as dlg
from content import llm_prompts as prompts
from content.facts import get_random_fact
from content.fancy_lines import FANCY_LINES
from content.poems import POEMS
from content.questions import QUESTIONS
from content.stories import STORIES
from content.wisdom import get_random_wisdom
from kinito.assets import newbeginnings_file_path, tune_file_path
from kinito.speech import SpeechMixin


class ContentMixin:
    """Read-aloud content and random idle interactions."""

    POEM_BACKGROUND_MUSIC_VOLUME = 0.6
    MEMORY_FOLLOWUP_CHANCE = 0.25

    def speak_random_question(self):
        """Ask a random question from the question pool."""
        if not self._can_initiate_spontaneous_speech():
            return
        memory = getattr(self, "_memory", None)
        if (
            memory is not None
            and memory.has_any_memory()
            and random.random() < self.MEMORY_FOLLOWUP_CHANCE
            and hasattr(self, "_memory_question_planner")
        ):
            spec = self._memory_question_planner.plan_template()
            if spec is not None:
                self.ask_memory_question(spec)
                return
        pool = self._available_spontaneous_questions()
        self.speak(random.choice(pool), 45, True)

    def _available_spontaneous_questions(self):
        """Return question pool entries that fit the current app state."""
        pool = list(QUESTIONS)
        memory = getattr(self, "_memory", None)
        if memory is not None:
            pool = [q for q in pool if not memory.is_question_answered(q)]
        if getattr(self, "_camera_active", False):
            marker = dlg.CAMERA_QUESTION_MARKER.lower()
            pool = [q for q in pool if marker not in q.lower()]
        return pool or list(QUESTIONS)

    def perform_random_menu_action(self):
        """Pick and run a random built-in action (time, poem, browser, hug, etc.)."""
        if not self._can_initiate_spontaneous_speech():
            return

        actions = [
            self.print_current_datetime,
            self.say_random_poem,
            self.say_random_fact,
            self.offer_browser_visit,
            self.offer_random_music,
            self.offer_game_picker,
            self.give_hug,
            self.spontaneous_nap,
        ]
        random.choice(actions)()

    def say_random_poem(self):
        """Recite a random poem in Kinito's normal voice, optionally with background music."""
        poem = random.choice(POEMS)
        play_music = poem.get("play_music") and not poem.get("whisper")
        accompaniment_path = newbeginnings_file_path if play_music else None
        accompaniment_volume = self.POEM_BACKGROUND_MUSIC_VOLUME if play_music else None
        if poem.get("whisper"):
            self.speak_whisper(
                poem["text"],
                long_bubble=True,
                ai_hint=prompts.POEM_PROMPT,
                speech_accompaniment_path=accompaniment_path,
                speech_accompaniment_volume=accompaniment_volume,
            )
        else:
            self.speak(
                poem["text"],
                pitch=45,
                long_bubble=True,
                voice_candidates=SpeechMixin.VOICE_NORMAL_CANDIDATES,
                ai_hint=prompts.POEM_PROMPT,
                speech_accompaniment_path=accompaniment_path,
                speech_accompaniment_volume=accompaniment_volume,
            )

    def spontaneous_nap(self):
        """Fall asleep on idle and wake up again after a short nap."""
        self.pause(spontaneous=True)

    def say_random_fact(self):
        """Speak a random fun fact."""
        self.speak(get_random_fact(), ai_hint=prompts.FUN_FACT_PROMPT)

    def say_random_wisdom(self):
        """Share a random wisdom line during idle reading."""
        if not self._can_initiate_spontaneous_speech():
            return
        self.speak(get_random_wisdom())

    def offer_random_story(self):
        """Offer to tell a short story the user can accept or decline."""
        if not self._can_initiate_spontaneous_speech():
            return
        self._pending_story = random.choice(STORIES)
        self.speak(dlg.pick_line(dlg.STORY_QUESTIONS), 45, True)

    def say_pending_story(self):
        """Tell the story queued by offer_random_story."""
        story = self._pending_story or random.choice(STORIES)
        self._pending_story = None
        self.speak(story, ai_hint="Tell a very short story in two to four sentences. No markdown.")

    def perform_fancy_show(self):
        """Play TinyTune and deliver a fancy-mode line."""
        if not self._can_initiate_spontaneous_speech():
            return
        self.play_mp3(tune_file_path, volume=self.POEM_BACKGROUND_MUSIC_VOLUME)
        self.speak(random.choice(FANCY_LINES))

    def _run_fancy_idle(self):
        """Cycle magician sprites for the full fancy performance, including while talking."""
        self._fancy_mode = True
        magician_sprites = getattr(self, "_magician_sprites", (self.tk_img_fancy,))
        if len(magician_sprites) < 2:
            magician_sprites = (self.tk_img_fancy, getattr(self, "tk_img_fancy_2", self.tk_img_fancy))
        frame = 0
        self.change_sprite(magician_sprites[0])
        threading.Thread(target=self.perform_fancy_show, daemon=True).start()

        speech_started = False
        while self._running and not self.paused:
            time.sleep(0.45)
            frame += 1
            self.change_sprite(magician_sprites[frame % len(magician_sprites)])
            if self.talking:
                speech_started = True
            elif speech_started:
                break

        self._fancy_mode = False

    def say_random_joke(self):
        """Tell a random corny joke."""
        self.speak(dlg.pick_line(dlg.JOKES), ai_hint=prompts.JOKE_PROMPT)

    def say_random_compliment(self):
        """Give the user a random compliment."""
        self.speak(dlg.pick_line(dlg.COMPLIMENTS))
