# Extending & Customizing Kinito

This guide explains how to change Kinito’s personality, add features, and modify behavior **without** rewriting the whole app.

**Prerequisite:** You can open Python files in any text editor (Notepad, VS Code, Cursor, etc.).

---

## How the app is organized

```
User runs Kinito.py
       ↓
FloatingAssistant (kinito/app.py)
       ↓ combines mixins ↓
┌──────────────┬──────────────┬──────────────┐
│ speech.py    │ movement.py  │ features/*   │
│ bubbles, TTS │ drag, idle   │ browser, hug │
└──────────────┴──────────────┴──────────────┘
       ↓ reads text from ↓
content/dialogue.py  +  content/dialog_registry.py
```

**Golden rule:** Put **words** in `content/`. Put **behavior** in `kinito/features/` or `dialog_registry.py`.

---

## 1. Change existing dialogue (easiest)

All spoken lines live in `content/`. Edit these files freely:

| File | Contents |
|------|----------|
| `content/dialogue.py` | Questions, button labels, yes/no replies |
| `content/startup.py` | Lines when Kinito starts |
| `content/goodbye_lines.py` | Farewell lines |
| `content/facts.py` | Fun facts |
| `content/poems.py` | Poems (see structure below) |
| `content/stories.py` | Short idle stories |
| `content/wisdom.py` | Quotes while “reading” |
| `dialogue.py` → `JOKES` | Corny jokes |
| `content/hug_lines.py` | Hug reactions |
| `content/camera_lines.py` | Lines while camera is open |
| `content/browser_lines.py` | Browser open lines |

### Example: add a new fun fact

Open `content/facts.py` and add a string to the `FACTS` list:

```python
FACTS = [
    "Did you know that octopuses have three hearts?",
    # ... existing facts ...
    "Your new fact goes here!",
]
```

Save the file and restart Kinito. No other changes needed.

### Example: change startup greeting

Open `content/startup.py`, edit any line in `STARTUP_LINES`, save, restart.

---

## 2. Add a new random question

Random questions come from `content/questions.py`, which pulls prompts from `dialogue.py`. Each question must connect to the **dialog registry** so buttons appear.

### Step A — Define the question in `dialogue.py`

```python
# Near other questions:
PIZZA_QUESTION = "Do you like pineapple on pizza?"

PIZZA_YES_LINES = [
    "A person of culture! Sweet and savory harmony!",
    "Controversial but valid. I respect your bravery.",
]
PIZZA_NO_LINES = [
    "That's okay! More pizza for the rest of us.",
    "A classic choice. No judgment here!",
]
```

### Step B — Register the dialog in `dialog_registry.py`

Add a `DialogSpec` to the `DIALOG_SPECS` tuple (order matters for overlapping markers — put specific ones first):

```python
DialogSpec(
    dlg.PIZZA_QUESTION,
    DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
    _yes_no_lines(dlg.PIZZA_YES_LINES, dlg.PIZZA_NO_LINES),
),
```

`_yes_no_lines` is a helper already in the file — it speaks a random line from the yes/no pools when the user clicks.

### Step C — Add to the random question pool

Open `content/questions.py`:

```python
from content.dialogue import (
    # ... existing imports ...
    PIZZA_QUESTION,
)

QUESTIONS = [
    # ... existing questions ...
    PIZZA_QUESTION,
]
```

### Step D — Test

```powershell
python -m pytest tests/test_questions_coverage.py -q
```

Restart Kinito. Eventually he will ask your new question.

---

## 3. Questions with text box answers

For “What’s your favorite X?” style prompts:

**In `dialogue.py`:**

```python
PIZZA_TOPPING_QUESTION = "What's your favorite pizza topping?"
PIZZA_TOPPING_RESPONSES = [
    "Ooh, {response}! That sounds delicious on a pizza.",
    "{response}? Bold choice. I'd order that in a heartbeat.",
]
```

**In `dialog_registry.py`:**

```python
DialogSpec(
    dlg.PIZZA_TOPPING_QUESTION,
    DialogUI("textbox", textbox_prompt=dlg.PIZZA_TOPPING_QUESTION),
    _text_format(dlg.PIZZA_TOPPING_RESPONSES),
),
```

The `{response}` placeholder is replaced with whatever the user types.

---

## 4. Multi-variant questions (camera, browser, hug)

Some features use **several phrasings** of the same question. They share a **marker** substring that the registry detects.

**In `dialogue.py`:**

```python
CAMERA_QUESTION_MARKER = "open the camera"

CAMERA_QUESTIONS = [
    "Hey! Can I open the camera?",
    "Mind if I open the camera for a bit?",
]
```

**Critical rule:** Every string in `CAMERA_QUESTIONS` must contain `CAMERA_QUESTION_MARKER` (case-insensitive).

The registry entry uses the marker, not the full question:

```python
DialogSpec(
    dlg.CAMERA_QUESTION_MARKER,
    DialogUI("buttons", buttons=(dlg.BUTTON_YES, dlg.BUTTON_NO)),
    _yes_no(lambda a: a.root.after(0, a.open_camera), dlg.CAMERA_DECLINED_LINES),
),
```

When adding variants, always include the marker text.

---

## 5. Add a right-click menu item

### Step A — Button label in `dialogue.py`

```python
MENU_OPTIONS = [
    # ... existing options ...
    "Tell Me a Secret",
]

BUTTON_TELL_SECRET = "Tell Me a Secret"
```

Keep `MENU_OPTIONS` and `BUTTON_*` constants in sync.

### Step B — Handler in `dialog_registry.py`

In `_handle_menu`:

```python
def _handle_menu(app, response: str) -> None:
    actions = {
        # ... existing actions ...
        dlg.BUTTON_TELL_SECRET: lambda a: a.speak("I hid a secret in the code. You'll never find it. ...Or will you?"),
    }
```

The menu `DialogSpec` already exists — it uses `MENU_PROMPT` and `MENU_OPTIONS`.

### Step C — Implement a method (optional)

For complex actions, add a method to a mixin in `kinito/features/` and call it from the handler:

```python
dlg.BUTTON_TELL_SECRET: lambda a: a.tell_secret(),
```

---

## 6. Add safe websites

Open `content/allowed_sites.py`:

```python
ALLOWED_SITES = {
    "animals": [
        # ... existing sites ...
    ],
    "knowledge": [
        {
            "title": "Wikipedia — Main Page",
            "url": "https://en.wikipedia.org/wiki/Main_Page",
        },
    ],
}
```

**Rules enforced by `site_validator.py`:**

- Must be **HTTPS**
- Must be on the whitelist (exact URL or matching hostname)
- No raw IP addresses

After adding sites, verify:

```powershell
python -m pytest tests/test_site_validator.py -q
```

Users pick categories via the browser menu — categories are the keys in `ALLOWED_SITES` (`animals`, `knowledge`, `games`, `horror`).

To add a **new category**:

1. Add a key to `ALLOWED_SITES`
2. Add a button constant in `dialogue.py` (e.g. `BUTTON_CATEGORY_SCIENCE = "Science"`)
3. Add the button to the browser category `DialogUI` in `dialog_registry.py`
4. Map the button in `_handle_browser_category`

---

## 7. Change sprites and sounds

### Sprites (PNG)

Place files in `GameAssets/`. Paths are defined in `kinito/assets.py`:

| Constant | Default file |
|----------|--------------|
| `sprite_path_normal` | `KinitoNormal.png` |
| `sprite_path_moving` | `Kinito.png` |
| `sprite_path_thinking` | `Thinking.png` |
| `sprite_path_hug` | `KinitoHug.png` |
| `sprite_path_hug2` | `KinitoHug2.png` |
| `sprite_path_sleep` | `Sleep.png` |

Replace a PNG with the **same filename**, or change the path in `assets.py`.

Recommended: keep transparent backgrounds (white is treated as transparent in the app).

If a file is missing, Kinito falls back to `KinitoNormal.png`.

### Sound effects (MP3)

Also in `GameAssets/`. Used paths in `assets.py`:

- `Woosh.mp3` — drag start
- `Bomp.mp3` — drag release
- `Surf.mp3` — movement
- `StartTalking.mp3` / `StopTalking.mp3` — bubble open/close
- `Timer.mp3` — reminder finished

---

## 8. Poems with music or whisper

`content/poems.py` uses dictionaries:

```python
POEMS = [
    {
        "text": "Your poem text here...",
        "whisper": False,      # True = quiet voice
        "play_music": True,    # True = plays NewBeginningsPoemEdit.mp3 softly
    },
]
```

---

## 9. Secret images easter egg

When Kinito offers to show a generated image and you accept, he opens a random file from:

```
GameAssets/SecretImages/
```

Supported formats: `.jpg`, `.jpeg`, `.png`

Add your own images there.

---

## 10. Adjust behavior constants

| What | File | Constant |
|------|------|----------|
| How often Kinito asks questions | `kinito/movement.py` | `QUESTION_CHANCE` (0.0–1.0) |
| Browser window size | `kinito/features/browser.py` | `BROWSER_WIDTH`, `BROWSER_HEIGHT` |
| Hug duration | `kinito/features/hug.py` | `HUG_DURATION_MS` |
| Speech bubble max width | `kinito/speech.py` | `BUBBLE_MAX_WIDTH` |
| MP3 search folders | `kinito/features/music.py` | `_music_search_roots()` |

---

## 11. Add a new feature (advanced)

Example: a “dance” feature.

1. Create `kinito/features/dance.py`:

```python
import random
from content.dance_lines import DANCE_LINES

class DanceMixin:
    def do_dance(self):
        self.speak(random.choice(DANCE_LINES))
        # play_mp3, change sprites, etc.
```

2. Create `content/dance_lines.py` with `DANCE_LINES = [...]`

3. Import and add `DanceMixin` to the class in `kinito/app.py`:

```python
class FloatingAssistant(
    SpeechMixin,
    MovementMixin,
    # ...
    DanceMixin,
):
```

4. Wire it to a menu button or dialog handler (see sections 2 and 5).

---

## 12. Dialog registry reference

### Helper factories (in `dialog_registry.py`)

| Helper | Use case |
|--------|----------|
| `_yes_no(yes_fn, no_lines)` | Yes runs a function; No speaks declined lines |
| `_yes_no_lines(yes_lines, no_lines)` | Yes/No both speak random lines |
| `_good_bad(good_lines, bad_lines)` | Good / Bad buttons |
| `_sure_decline(yes_fn, declined_lines)` | Sure / Not now |
| `_okay_not_now(yes_fn, declined_lines)` | Okay / Not now |
| `_text_format(response_lines)` | Text box → formatted reply |
| `_button_map({...})` | Custom button → action map |

### How matching works

When Kinito speaks, the speech bubble title is set to the spoken text. `find_dialog_spec(text)` loops through `DIALOG_SPECS` and returns the **first** spec whose `marker` appears as a substring in the text (case-insensitive).

---

## 13. Run tests after changes

Always run tests after editing content or dialogs:

```powershell
pip install -r requirements-dev.txt
python -m pytest tests/ -q
ruff check .
```

Key test files:

| Tests | Validates |
|-------|-----------|
| `test_questions_coverage.py` | Every question matches a dialog |
| `test_dialogue.py` | Markers present in question variants |
| `test_site_validator.py` | URL whitelist rules |
| `test_dialog_handlers.py` | Menu and button wiring |

---

## 14. Common mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Question not in `QUESTIONS` | Kinito never asks it | Add to `questions.py` |
| Missing marker in variant | Buttons don’t appear | Include marker substring in every variant |
| Dialog not in `DIALOG_SPECS` | No buttons for new question | Add `DialogSpec` |
| `{response}` typo in template | Crash or ugly output | Match placeholder name exactly |
| HTTP instead of HTTPS URL | Site blocked | Use `https://` only |
| Forgot to restart Kinito | Changes not visible | Close and run `python Kinito.py` again |

---

## Need more help?

- Read the code comments in `content/dialog_registry.py`
- Look at an existing feature (e.g. hug or camera) and copy the pattern
- Open a GitHub Issue with what you tried

Happy customizing!
