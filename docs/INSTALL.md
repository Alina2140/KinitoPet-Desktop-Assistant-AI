# Installation Guide (Complete Beginner Walkthrough)

This guide assumes **no prior programming experience**. Every step is explained.

**Goal:** Get Kinito running on Windows.

**Time:** About 15–30 minutes (mostly downloads).

---

## Step 0: What you are installing

You are **not** installing a normal `.exe` app from a store. Kinito is a **Python program**:

1. **Python** — the language the app is written in (free from python.org)
2. **Libraries** — extra code Kinito needs (installed automatically via `pip`)
3. **GameAssets** — images and sounds (already in the project folder)
4. **Kinito.py** — the file you run to start the app

Nothing here costs money. Nothing sends your data to a server.

---

## Step 1: Download the project

### Option A — Download ZIP from GitHub

1. Open the project page on GitHub
2. Click the green **Code** button
3. Click **Download ZIP**
4. Extract the ZIP (right-click → **Extract All…**)
5. Remember the folder path, e.g. `C:\Users\YourName\Documents\KinitoPET-Python-Virtual-Assistant`

### Option B — Git (if you use Git)

```powershell
git clone https://github.com/YOUR_USERNAME/KinitoPET-Python-Virtual-Assistant.git
cd KinitoPET-Python-Virtual-Assistant
```

Replace `YOUR_USERNAME` with the actual repository owner.

### Check: GameAssets must exist

Open the folder. You should see:

```
GameAssets/
Kinito.py
kinito/
content/
```

If `GameAssets` is missing, sprites and sounds will not load. Contact the repository owner or restore that folder from the full release.

---

## Step 2: Install Python

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download **Python 3.12** (or 3.11)
3. Run the installer
4. **IMPORTANT:** On the first screen, check:
   - ☑ **Add python.exe to PATH**
5. Click **Install Now**
6. When finished, click **Close**

### Verify Python works

1. Press **Win + R**, type `powershell`, press Enter
2. Type:

```powershell
python --version
```

You should see something like `Python 3.12.x`.

If you see an error (“python is not recognized”), Python was not added to PATH. Re-run the installer and enable **Add to PATH**, or use **“Modify”** on the existing install.

---

## Step 3: Open PowerShell in the project folder

**Method 1 — From File Explorer**

1. Open the project folder in File Explorer
2. Click the address bar, type `powershell`, press Enter

**Method 2 — cd command**

```powershell
cd C:\Users\YourName\Documents\KinitoPET-Python-Virtual-Assistant
```

(Use your real path.)

---

## Step 4: Create a virtual environment

A **virtual environment** (`.venv`) keeps Kinito’s libraries separate from other Python projects. This avoids version conflicts.

```powershell
python -m venv .venv
```

Wait a few seconds. A new folder `.venv` appears.

### Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

Your prompt should now start with `(.venv)`.

**If you get a security error:**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again.

> **Every time** you open a new PowerShell window to run Kinito, you must `cd` to the project and activate `.venv` again.

---

## Step 5: Install dependencies

With `(.venv)` active:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

This downloads and installs:

| Package | What it does |
|---------|----------------|
| Pillow | Loads PNG sprites |
| pygame | Plays MP3 sound effects |
| pyttsx3 | Backup text-to-speech |
| pyautogui | Keyboard shortcuts (Windows) |
| opencv-python | Webcam |
| pywebview | Small built-in browser window |

**Installation may take 2–10 minutes** depending on your internet speed.

### If installation fails

**Corporate proxy / 403 error:**

```powershell
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

**Still failing?** Install the minimum set manually:

```powershell
pip install Pillow pygame pyttsx3
```

You can add `opencv-python` and `pywebview` later.

---

## Step 6: Run Kinito

Still in the project folder with `(.venv)` active:

```powershell
python Kinito.py
```

### What should happen

1. A small character window appears on your desktop
2. You may hear a startup line (TTS)
3. The console may print dependency status
4. After a short delay, Kinito may wander or ask a question

### Stop Kinito

- Right-click → **Say Goodbye**, or
- Close the terminal, or
- **Ctrl + C** in PowerShell

---

## Step 7 (Optional): Create a desktop shortcut

1. Right-click on Desktop → **New** → **Shortcut**
2. Target (adjust paths):

```
C:\Users\YourName\Documents\KinitoPET-Python-Virtual-Assistant\.venv\Scripts\pythonw.exe C:\Users\YourName\Documents\KinitoPET-Python-Virtual-Assistant\Kinito.py
```

Using `pythonw.exe` hides the black console window.

3. Name it **Kinito**
4. Double-click to launch

---

---

## Step 8 (Optional): Ollama AI chat

Kinito can chat with you using a **local** Ollama model. Nothing is sent to the cloud.

1. Install Ollama from [https://ollama.com/](https://ollama.com/)
2. Open a terminal and pull a model:

```powershell
ollama pull llama3.2:3b
```

3. Keep Ollama running (tray icon or `ollama serve`)
4. In Kinito: **right-click → Chat**

If chat fails, Kinito still works with all scripted lines. Set `OLLAMA_MODEL` to match a model you installed.

---

## Step 9 (Optional): Developer tools

If you want to run tests or contribute:

```powershell
pip install -r requirements-dev.txt
python -m pytest tests/ -q
ruff check .
```

---

## Daily usage cheat sheet

```powershell
cd C:\path\to\KinitoPET-Python-Virtual-Assistant
.\.venv\Scripts\Activate.ps1
python Kinito.py
```

---

## Still stuck?

| Problem | Try this |
|---------|----------|
| Black window flashes and closes | Run `python Kinito.py` in PowerShell and read the red error text |
| No character visible | Check `GameAssets/Kinito.png` exists |
| No sound | Check volume; install `pygame` |
| No speech | Install `pyttsx3`; check `GameAssets/Programs/balcon.exe` |
| Permission errors | Run PowerShell as normal user, not from a restricted folder |

See also the [Troubleshooting section in README.md](../README.md#troubleshooting).

---

**Next:** Learn how to customize Kinito in [EXTENDING.md](EXTENDING.md).
