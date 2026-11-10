# Project verification

Use the existing Windows virtual environment for verification; the system Python does not have pytest installed.

- Tests: `.\.venv\Scripts\python.exe -m pytest tests/ -q`
- Lint: `.\.venv\Scripts\python.exe -m ruff check .`

Mini-game logic lives in `kinito/features/games/`; Battleships separates pure rules in `battleships.py` from its Tkinter Canvas UI in `battleships_ui.py`.
