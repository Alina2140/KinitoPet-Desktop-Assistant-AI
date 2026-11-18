# Choosing & Downloading Ollama Models

Kinito talks to a locally running [Ollama](https://ollama.com) server for chat
replies, AI idle lines and memory questions. The model it uses is configurable.

## Pick a model in Kinito

1. Right-click Kinito → **Settings** → **AI Model**
2. The picker lists all models that are **already installed** on your machine
   as buttons — click one to switch instantly. The choice is saved in
   `gameAssets/userMedia/settings.json` (`ollama_model`) and survives restarts.

If the picker says Ollama is unreachable, make sure Ollama is running
(`ollama serve` or the Ollama desktop app) and that
`http://127.0.0.1:11434` opens in a browser.

## Download a new model

Models are downloaded once with the Ollama CLI — after that they appear in
Kinito's picker automatically:

```powershell
ollama pull llama3.2:3b
```

Browse available models: <https://ollama.com/library>

### Suggestions for this app

Kinito mostly generates one-to-three-sentence lines, so small models work
well and respond much faster — especially on machines without a GPU.

| Model | Size | Notes |
| --- | --- | --- |
| `llama3.2:1b` | ~1 GB | Fastest; good enough for short lines |
| `llama3.2:3b` | ~2 GB | Recommended balance of speed/quality |
| `qwen2.5:3b` | ~2 GB | Good alternative, also quick on CPU |
| `llama3.1:8b` | ~5 GB | Default; noticeably slow without a GPU |

Check what is installed and whether it runs on GPU or CPU:

```powershell
ollama list   # installed models
ollama ps     # loaded model + PROCESSOR (CPU/GPU) column
```

## Environment variables (advanced)

These override the defaults when Kinito starts — the Settings picker still
takes precedence over `OLLAMA_MODEL` for the chat model:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_MODEL` | `llama3.1:8b` | Fallback chat model before the saved setting |
| `OLLAMA_VISION_MODEL` | `llava` | Vision model for paint comments |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama API endpoint |
| `OLLAMA_TIMEOUT_S` | `60` | Request timeout (raise it on slow CPUs) |
| `OLLAMA_KEEP_ALIVE` | `10m` | How long the model stays loaded (`-1` = forever) |
| `OLLAMA_ENABLED` | `1` | `0` disables AI lines and chat entirely |

Example (persistent user variable on Windows):

```powershell
setx OLLAMA_MODEL "llama3.2:3b"
```
