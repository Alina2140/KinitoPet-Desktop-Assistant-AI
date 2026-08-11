Kinito User Media
=================

This folder stores personal data for Kinito.

Memory
------
Kinito can remember things about you across sessions.

- memory.json  — structured facts and chat notes (auto-managed)
- notes.txt    — human-readable mirror of chat notes (optional to edit)

Paintings
---------
Drawings saved from Actions → Paint:

- paintings/   — PNG files (paint_YYYYMMDD_HHMMSS.png)

Open Actions → Paint → My Paintings to browse them in-app.

Settings
--------
Toggle preferences from the in-app Settings menu are saved here:

- settings.json — screen effects, ambient reminders, app awareness, mood system, TTS volume, …

Game scores
-----------
Highscores for selected mini-games (Snake, Memory, True or False, Number Guess, Battleships):

- game_scores.json — snake highscore, memory best moves, trivia best/streak,
  number-guess best attempts, battleships best shots

These files are not in Git (personal data). You do not need to create them
yourself — Kinito writes them on first save. The folder is created at startup.

Right-click Kinito → Settings → Memories to hear a summary.
Right-click Kinito → Settings → Forget to clear saved memory.
