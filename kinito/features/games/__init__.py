"""Mini-games mixin: game picker and individual game launchers."""

from content import dialogue as dlg
from content.trivia_questions import ROUND_SIZE
from kinito.features.games.battleships_ui import BattleshipsGame
from kinito.features.games.memory_ui import MemoryGame
from kinito.features.games.number_guess import new_secret_number
from kinito.features.games.tic_tac_toe import TicTacToeGame


class GamesMixin:
    """Offer and launch built-in mini-games."""

    def offer_game_picker(self):
        """Ask the user which mini-game to play."""
        if self._is_busy_with_speech():
            return
        self.speak(dlg.GAME_PICKER_QUESTION, 45, True)

    def offer_quick_games(self):
        """Show the quick-games submenu."""
        if self._is_busy_with_speech():
            return
        self.speak(dlg.QUICK_GAMES_QUESTION, 45, True)

    def offer_board_games(self):
        """Show the board-games submenu."""
        if self._is_busy_with_speech():
            return
        self.speak(dlg.BOARD_GAMES_QUESTION, 45, True)

    def speak_game_line(self, line, *, show_bubble=True):
        """Speak a game comment with TTS and show Kinito's speech bubble."""
        self.speak(line, show_bubble=show_bubble, skip_ai=True)

    def _is_game_active(self) -> bool:
        """Return True while any mini-game is in progress."""
        window = getattr(self, "_game_window", None)
        if window is not None:
            try:
                if window.winfo_exists():
                    return True
                self._game_window = None
            except Exception:
                self._game_window = None

        if getattr(self, "_number_guess_target", None) is not None:
            return True

        if getattr(self, "_trivia_current", None) is not None:
            return True

        trivia_round = getattr(self, "_trivia_round", 0)
        trivia_used = getattr(self, "_trivia_used", None)
        return trivia_round < ROUND_SIZE and trivia_used and len(trivia_used) > 0

    def _ensure_single_game_window(self):
        """Close any open game window so only one game runs at a time."""
        window = getattr(self, "_game_window", None)
        if window is not None:
            try:
                if window.winfo_exists():
                    self._game_window = None
                    window.destroy()
            except Exception:
                self._game_window = None

    def start_tic_tac_toe(self):
        """Open a tic-tac-toe game window."""
        self.root.after(0, lambda: TicTacToeGame(self).open())

    def start_rock_paper_scissors(self):
        """Start a rock-paper-scissors round in the speech bubble."""
        self.speak(dlg.RPS_QUESTION, 45, True)

    def start_number_guess(self):
        """Start a number-guessing round."""
        self._number_guess_target = new_secret_number()
        self._number_guess_attempts = 0
        self.speak(dlg.NUMBER_GUESS_QUESTION, 45, True)

    def start_memory(self):
        """Open a memory card game window."""
        self.root.after(0, lambda: MemoryGame(self).open())

    def start_coin_dice(self):
        """Start the coin-and-dice quick game."""
        self.speak(dlg.COIN_DICE_QUESTION, 45, True)

    def start_magic_8_ball(self):
        """Start a Magic 8-Ball question round."""
        self.speak(dlg.MAGIC_8_BALL_QUESTION, 45, True)

    def start_true_false(self):
        """Start a true-or-false trivia round."""
        self._trivia_score = 0
        self._trivia_round = 0
        self._trivia_used = set()
        self._ask_next_trivia()

    def _ask_next_trivia(self):
        """Ask the next true-or-false question in the current round."""
        from content.trivia_questions import pick_random_question

        if self._trivia_round >= ROUND_SIZE:
            return
        question = pick_random_question(self._trivia_used)
        self._trivia_used.add(question)
        self._trivia_current = question
        prompt = f"True or false: {question.statement}"
        self.speak(prompt, 45, True, skip_ai=True)

    def start_battleships(self):
        """Open a mini battleships game window."""
        self.root.after(0, lambda: BattleshipsGame(self).open())
