# Troubleshooting

Common fixes for install and runtime issues.

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
3. Pull the model: `ollama pull llama3.1:8b` (or set `OLLAMA_MODEL` to a model you have)
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

The spoken line must contain a **marker substring** registered in `content/dialog_registry.py`. If you add new question text, see **[EXTENDING.md](EXTENDING.md)**.

### My windows minimized or moved — is that a bug?

Usually **no**. Declining certain offers (poem **No**, secret image **Not now**) triggers intentional window minimizing on Windows — a KinitoPET-style easter egg. Separately, **Window Play** (Settings) may occasionally grab and slide open windows with a hand sprite; you can take over mid-drag, and you can disable it in Settings. Windows are never closed. More context: **Easter eggs** in the root `README.md`.

---

**Related:** [INSTALL.md](INSTALL.md) · [EXTENDING.md](EXTENDING.md)
