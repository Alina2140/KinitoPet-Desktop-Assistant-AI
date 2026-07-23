# KinitoPET — Python Virtual Assistant

A free, open-source desktop companion inspired by **KinitoPET**. Kinito lives on your screen as a small floating character: he talks, wanders around, asks questions, opens safe websites, plays music, and keeps you company while you work.

> **Platform:** Built and tested on **Windows 10/11**. Some features (TTS via `balcon.exe`, opening programs from the Desktop, window minimize) are Windows-specific. The core app may run on other OSes with reduced functionality.

---

## Table of contents

1. [Features](#features)
2. [Quick start (5 minutes)](#quick-start-5-minutes)
3. [How to use Kinito](#how-to-use-kinito)
4. [Project structure](#project-structure)
5. [Optional features & dependencies](#optional-features--dependencies)
6. [Troubleshooting](#troubleshooting)
7. [For developers](#for-developers)
8. [Documentation](#documentation)
9. [License & attribution](#license--attribution)

---

## Features

| Feature | Description |
|---------|-------------|
| **Floating desktop friend** | Transparent window; drag Kinito anywhere on screen |
| **Text-to-speech** | Speaks lines aloud (Balcon TTS + pyttsx3 fallback) |
| **Speech bubbles** | Interactive buttons and text boxes for replies |
| **Random questions** | 30+ conversation topics while idle |
| **AI chat (Ollama)** | Free-form chat via local Ollama model; optional AI idle lines |
| **Right-click menu** | Grouped Modes / Settings / Actions, plus chat and goodbye |
| **Safe browser** | Opens whitelisted HTTPS sites in a small window (or your default browser) |
| **Camera** | Optional webcam view (requires OpenCV) |
| **Music player** | Play MP3s from your PC |
| **Hug** | Hug sprites + sweet lines |
| **Idle animations** | Blinking, reading, fancy hat mode, sleep sprites |
| **Reminders** | Timer with sound after X minutes |
| **Mini-games** | Tic-tac-toe, memory, battleships, RPS, trivia, and more (right-click → **Actions** → **Play Game**) |

---

## Quick start (5 minutes)

### What you need

- **Windows 10 or 11**
- **Python 3.11 or 3.12** (recommended) — [python.org/downloads](https://www.python.org/downloads/)
  - During install, check **“Add python.exe to PATH”**
- This repository folder, including the **`GameAssets`** directory (sprites, sounds, `balcon.exe`)

### Steps

```powershell
# 1. Open PowerShell and go to the project folder
cd C:\path\to\KinitoPET-Python-Virtual-Assistant

# 2. Create a virtual environment (keeps dependencies isolated)
python -m venv .venv

# 3. Activate it
.\.venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start Kinito
python Kinito.py
```

If PowerShell blocks activation, run once:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**First launch:** Kinito appears at a random position, says a startup line, and begins idle movement after a few seconds.

For a **full beginner walkthrough** (screenshots-level detail), see **[docs/INSTALL.md](docs/INSTALL.md)**.

---

## How to use Kinito

### Mouse controls

| Action | What happens |
|--------|----------------|
| **Left-click + drag** | Move Kinito around the screen |
| **Right-click** | Open the action menu |

### Right-click menu

Top level:

- **Modes** — Sleep / Wake up, Focus / Unfocus, Focus Timer
- **Settings** — Screen Effects, Memories, Forget, Credits
- **Actions** — Reminder, Tell Time, Sing, Fun Fact, Visit Website, Play Music, Play Game, Hug
- **Chat** — free-form conversation with a local Ollama model (see below)
- **Goodbye** — farewell line, then closes the app

Submenus (same pattern as **Play Game**):

- **Modes → Sleep / Wake up** — nap mode (sleep animations); label switches while sleeping
- **Modes → Focus / Unfocus** — quiet mode; label switches while active
- **Modes → Focus Timer** — set / adjust / end a focus countdown (focus mode only)
- **Settings → Screen Effects** — toggle rare glitch effects
- **Settings → Memories** — hear a summary of saved memory
- **Settings → Forget** — clear saved memory
- **Settings → Credits** — attribution links
- **Actions → Set Reminder** — type minutes (e.g. `15`); Kinito reminds you with sound + speech
- **Actions → Tell Time** — speaks the current time
- **Actions → Sing** — recites a random poem (some include background music)
- **Actions → Fun Fact** — random fact
- **Actions → Visit Website** — pick a category (Animals, Knowledge, Games, Horror, Surprise Me)
- **Actions → Play Music** — pick an MP3 or play a random one from your Music/Downloads folders
- **Actions → Play Game** — mini-games (quick games and board games)
- **Actions → Hug** — hug pose sprites + hug line

### Spontaneous speech

While idle, Kinito may:

- Ask a random question (answer with buttons or a text field)
- Say a short AI-generated line (when Ollama is running)
- Offer to open the camera, browser, music, or a hug
- Read a short story or wisdom quote
- Do a “fancy” show with a top hat sprite

Click the buttons in the speech bubble to respond. Press **Enter** in text boxes to submit.

### Easter eggs (intentional behavior)

Some choices trigger **KinitoPET-style surprises** — not bugs:

- **Declining a poem** (**No**) or **declining a secret image** (**Not now**) can cause certain intended things to happen. It needs `pyautogui` installed.

### Browser safety

Kinito only opens URLs from a **manual whitelist** in `content/allowed_sites.py`. Navigation to other HTTPS sites is blocked inside the built-in browser window.

---

## Project structure

```
KinitoPET-Python-Virtual-Assistant/
├── Kinito.py              # Entry point — run this file
├── kinito/                  # Application code
│   ├── app.py               # Main window & lifecycle
│   ├── speech.py            # TTS, speech bubbles, menu
│   ├── speech_chat.py       # Multi-turn chat bubble UI
│   ├── bubble_ui.py         # Chamfered bubble chrome & buttons
│   ├── movement.py          # Drag, wander, idle animations
│   ├── assets.py            # Paths to GameAssets files
│   ├── llm/                 # Ollama client & config
│   └── features/            # Browser, camera, music, hug, llm, programs, content, games
├── content/                 # All dialogue & data (easy to edit!)
│   ├── dialogue.py          # Questions, buttons, response lines
│   ├── dialog_registry.py   # Links questions → UI → actions
│   ├── questions.py         # Pool of random questions
│   ├── allowed_sites.py     # Browser whitelist
│   ├── facts.py, poems.py, stories.py, ...
│   └── site_validator.py    # URL safety checks
├── GameAssets/              # Sprites, MP3s, balcon.exe (required)
├── tests/                   # Automated tests (800+)
├── docs/                    # Detailed guides
├── requirements.txt         # Runtime dependencies
└── requirements-dev.txt     # pytest, ruff (for contributors)
```

---

## Optional features & dependencies

| Package | Purpose | If missing |
|---------|---------|------------|
| `pywebview` | Built-in browser window | Falls back to system default browser |
| `opencv-python` | Webcam feature | Camera questions still appear; opening camera shows a message |
| `pyttsx3` | TTS fallback | Uses `balcon.exe` only |
| `pygame` | Sound effects & MP3 | Required for sounds |
| `pyautogui` | Minimize windows (poem/image easter egg) | That easter egg silently fails |
| `Pillow` | Images / sprites | Required |
| **Ollama** (local) | AI chat & optional idle lines | Chat disabled; scripted lines still work |

On startup, Kinito prints optional dependency status to the console, e.g.:

```
Kinito optional deps: {'pywebview': 'ok', 'opencv': 'missing', 'balcon': 'ok', 'pyttsx3': 'ok', 'ollama': 'ok'}
```

### Ollama (AI chat)

1. Install [Ollama](https://ollama.com/) and start it (default: `http://127.0.0.1:11434`)
2. Pull a model, e.g. `ollama pull llama3.2:3b`
3. Right-click Kinito → **Chat**

Optional environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama API URL |
| `OLLAMA_MODEL` | `llama3.2:3b` | Model name |
| `OLLAMA_ENABLED` | `true` | Enable/disable AI features |
| `OLLAMA_IDLE_LINES` | `true` | AI-generated spontaneous lines |
| `OLLAMA_REPLACE_CHANCE` | `0.30` | Chance that any non-interactive spoken line is AI-generated |
| `OLLAMA_IDLE_CHANCE` | `0.30` | Legacy alias for `OLLAMA_REPLACE_CHANCE` |
| `OLLAMA_MAX_TOKENS_SHORT` | `140` | Max tokens for short lines |
| `OLLAMA_MAX_TOKENS_LONG` | `320` | Max tokens for poems and long bubbles |
| `OLLAMA_KEEP_ALIVE` | `10m` | Keeps the model loaded in Ollama between requests |
| `OLLAMA_WARMUP` | `true` | Pre-load model on startup |

If Ollama is offline, Kinito falls back to the existing scripted dialogue in `content/`.

**What can become AI-generated:** startup/goodbye lines, poems, facts, jokes, stories, hugs, game reactions, reminder/time replies, idle remarks, and similar plain speech.

**What stays scripted:** menu prompts, yes/no questions with buttons, game pickers, credits, reminders input prompts, and other interactive dialog flows (so buttons still work).

### Memory (persistent user facts)

Kinito can remember personal facts across sessions — no database required.

- **Dialog answers** (name, favorite color, food, hobby, etc.) are saved automatically and those questions are not asked again.
- **Chat notes** are extracted in the background when Ollama is available (stable facts the user clearly stated).
- Files live in `GameAssets/UserMedia/`:
  - `memory.json` — structured facts and notes (auto-managed)
  - `notes.txt` — human-readable mirror of chat notes

These files are local only (listed in `.gitignore`) and are not uploaded to Git. You do **not** need to create them manually — Kinito creates `memory.json` and `notes.txt` automatically the first time something is saved (e.g. when you answer a name question or a memory follow-up). After cloning the repo, the `UserMedia/` folder already exists; your personal memory starts empty until you use the app.

Right-click Kinito → **Settings** → **Memories** to hear a summary.  
Right-click Kinito → **Settings** → **Forget** to clear saved memory.

Dialog-based memory works without Ollama. Chat note extraction requires Ollama.

**Memory questions:** Kinito can ask personalized follow-up questions (textbox or Yes/No) during idle roaming or as scripted follow-ups when it already knows facts about you. Answers are saved to `memory.json`. With Ollama running, new questions can be AI-planned; otherwise template follow-ups are used.

### GameAssets folder

The app expects a `GameAssets` folder next to `Kinito.py`:

```
GameAssets/
├── Kinito.png, KinitoNormal.png, KinitoHug.png, Thinking.png, ...   # Sprites
├── Timer.mp3, Woosh.mp3, StartTalking.mp3, ...       # Sounds
├── Programs/balcon.exe                               # Windows TTS (optional fallback: pyttsx3)
├── SecretImages/                                     # Optional images for easter egg
└── UserMedia/                                        # Personal memory files (gitignored)
```

The `UserMedia/` directory is created when Kinito starts. Memory files (`memory.json`, `notes.txt`) appear automatically when you first save a fact — nothing to copy or create by hand after `git clone`.

If a sprite is missing, Kinito falls back to `KinitoNormal.png`.

---

## Troubleshooting

### `python` is not recognized

Python is not on your PATH. Reinstall Python and enable **“Add to PATH”**, or use the full path:

```powershell
C:\Users\YourName\AppData\Local\Programs\Python\Python312\python.exe Kinito.py
```

### `pip install` fails (proxy / 403)

Some corporate networks block PyPI. Try:

```powershell
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

Or install packages one by one. **Minimum to start:** `Pillow`, `pygame`, `pyttsx3`.

### Chat does not work / “can't reach my brain”

1. Make sure Ollama is running (`ollama serve` or the Ollama desktop app)
2. Verify the API: open `http://127.0.0.1:11434` in a browser
3. Pull the model: `ollama pull llama3.2:3b` (or set `OLLAMA_MODEL` to a model you have)
4. Check the console line `ollama: ok` on startup

### No voice / TTS silent

1. Check that `GameAssets/Programs/balcon.exe` exists
2. Ensure `pyttsx3` is installed: `pip install pyttsx3`
3. Check Windows sound output device and volume

### Browser opens in Chrome/Firefox instead of a small window

`pywebview` is not installed in your active environment. Install it:

```powershell
pip install pywebview
```

If that fails, the fallback (`webbrowser.open`) still works — just without the small controlled window.

### Camera does not work

```powershell
pip install opencv-python
```

Close other apps using the webcam. Kinito uses camera index `0` (default webcam).

### Kinito closes immediately / error on start

Run from a terminal to see the error:

```powershell
python Kinito.py
```

Common causes: missing `GameAssets`, missing `Pillow`, or no display (won’t run headless).

### Speech bubble buttons do nothing

The spoken line must contain a **marker substring** registered in `content/dialog_registry.py`. If you add new question text, see **[docs/EXTENDING.md](docs/EXTENDING.md)**.

### My windows minimized — is that a bug?

Usually **no**. Declining certain offers (poem **No**, secret image **Not now**) triggers intentional window minimizing on Windows — a KinitoPET-style easter egg. See [Easter eggs](#easter-eggs-intentional-behavior) above.

---

## For developers

```powershell
pip install -r requirements-dev.txt
python -m pytest tests/ -q    # Run tests
ruff check .                  # Lint
ruff check --fix .            # Auto-fix lint issues
```

Architecture: one `FloatingAssistant` class in `kinito/app.py` combines **mixins** (speech, movement, browser, camera, …). Dialogue text lives in `content/` and is wired through `dialog_registry.py`.

---

## Documentation

| Document | Audience |
|----------|----------|
| **[docs/INSTALL.md](docs/INSTALL.md)** | Complete install guide for beginners |
| **[docs/EXTENDING.md](docs/EXTENDING.md)** | Add questions, sites, sprites, features |
| **[docs/GITHUB.md](docs/GITHUB.md)** | Publish or clone from GitHub |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | Pull requests & community guidelines |

---

## License & attribution

This project is released under the **[MIT License](LICENSE)** — free to use, modify, and share.

### Credits

| What | Who / where |
|------|-------------|
| **Kinito & KinitoPET** | [KinitoPET on Steam](https://store.steampowered.com/app/2075070/KinitoPET/) by **troy_en** |
| **Python template** | [TimTamCoder/KinitoPET-Python-Virtual-Assistant](https://github.com/TimTamCoder/KinitoPET-Python-Virtual-Assistant) by **TimTamCoder** |
| **AI-assisted development** | Parts of this codebase were written and refactored with **[Cursor](https://cursor.com)** (AI-assisted IDE) |

This is a **fan-made** desktop assistant. It is not an official KinitoPET product and is not affiliated with the game's developers or publishers.

If you fork this project or build your own desktop friend from it, **please credit this repository**, [TimTamCoder's template](https://github.com/TimTamCoder/KinitoPET-Python-Virtual-Assistant), and mention **KinitoPET** as inspiration.

**In the app:** right-click Kinito → **Credits** to view attributions and open the links above.

---

**Enjoy your desktop companion!** If something is unclear, open an Issue on GitHub or improve the docs via Pull Request.
