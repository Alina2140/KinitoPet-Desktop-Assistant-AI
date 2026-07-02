# Publishing on GitHub (Step-by-Step)

This guide covers:

1. **Publishing** your copy of Kinito to GitHub (for the project owner)
2. **Downloading** and using the project (for everyone else)

No paid account required. GitHub free tier is enough for public repositories.

---

## Part 1 — Create a GitHub account

1. Go to [https://github.com/signup](https://github.com/signup)
2. Follow the steps (email, password, username)
3. Verify your email

---

## Part 2 — Install Git (one-time)

Git tracks file changes and uploads them to GitHub.

1. Download **Git for Windows**: [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Run the installer — default options are fine
3. Verify in PowerShell:

```powershell
git --version
```

---

## Part 3 — Prepare the project locally

Open PowerShell in your project folder:

```powershell
cd C:\path\to\KinitoPET-Python-Virtual-Assistant
```

### Check what will be uploaded

```powershell
git status
```

If Git is not initialized yet:

```powershell
git init
```

### Important: do NOT upload these

The `.gitignore` file already excludes:

- `.venv/` — your local Python environment (huge, machine-specific)
- `__pycache__/` — Python cache
- `.pytest_cache/`, `.ruff_cache/` — tool caches

**Do upload:**

- All `.py` files
- `GameAssets/` — sprites and sounds (required for users!)
- `requirements.txt`, `README.md`, `LICENSE`, `docs/`
- `tests/`

### First commit

```powershell
git add .
git status
```

Review the list. Make sure `.venv` is **not** listed.

```powershell
git commit -m "Initial public release of KinitoPET Python Virtual Assistant"
```

---

## Part 4 — Create a repository on GitHub

1. Log in to GitHub
2. Click **+** (top right) → **New repository**
3. Fill in:
   - **Repository name:** `KinitoPET-Python-Virtual-Assistant` (or your choice)
   - **Description:** `Free open-source KinitoPET desktop companion for Windows`
   - **Public** — so anyone can download for free
   - **Do NOT** check “Add a README” (you already have one)
4. Click **Create repository**

GitHub shows commands — use the “push an existing repository” section:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/KinitoPET-Python-Virtual-Assistant.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

**First push:** GitHub may ask you to log in (browser window or personal access token).

---

## Part 5 — Make the repo welcoming

After upload, on GitHub:

### Add topics (helps people find it)

Repository → ⚙ **Settings** or edit repository → **Topics**:

```
kinitopet, desktop-pet, python, virtual-assistant, tkinter, windows
```

### Add a description

Short tagline under the repo name:

> Free KinitoPET-inspired desktop companion for Windows — talks, wanders, browses safe sites, and keeps you company.

### Pin the README

GitHub automatically shows `README.md` on the main page. Verify:

- Quick start works
- Links to `docs/INSTALL.md` work

### Optional: GitHub Releases

For non-technical users who don’t want Git:

1. Repository → **Releases** → **Create a new release**
2. Tag: `v1.0.0`
3. Title: `v1.0.0 — First public release`
4. Upload a **ZIP** of the project (include `GameAssets`!)
5. Publish

Users can download the ZIP from Releases instead of cloning.

---

## Part 6 — Updating the project later

After you change files locally:

```powershell
git add .
git commit -m "Describe what you changed"
git push
```

---

## Part 7 — For users downloading your project

Share this link:

```
https://github.com/YOUR_USERNAME/KinitoPET-Python-Virtual-Assistant
```

### Download options

| Method | Best for |
|--------|----------|
| **Download ZIP** (Code → Download ZIP) | Beginners |
| **git clone** | Developers who want updates |
| **Releases ZIP** | Stable version snapshots |

### Clone with Git

```powershell
git clone https://github.com/YOUR_USERNAME/KinitoPET-Python-Virtual-Assistant.git
cd KinitoPET-Python-Virtual-Assistant
```

Then follow [INSTALL.md](INSTALL.md).

---

## Part 8 — License & legal (important for public release)

This repository includes an **[MIT License](../LICENSE)**:

- Anyone can use, modify, and share the code
- No warranty
- Must include the license text when redistributing

The README asks for **attribution** — good practice, not a legal requirement beyond the MIT terms.

**KinitoPET character:** This is a **fan project**. State clearly that it is not official. The README already mentions [kinitopet.com](https://www.kinitopet.com/).

**Third-party assets:** Ensure you have the right to distribute sprites/sounds in `GameAssets/`. If some assets are not yours, document that in the README or replace them before publishing.

---

## Part 9 — Optional: GitHub Actions (CI)

Automatically run tests on every push. Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: python -m pytest tests/ -q
      - run: ruff check .
```

This is optional but builds trust for contributors.

---

## Part 10 — Troubleshooting Git

| Problem | Solution |
|---------|----------|
| `git: command not found` | Install Git for Windows, restart PowerShell |
| `Permission denied (publickey)` | Use HTTPS URL, or set up SSH keys |
| `failed to push` | Run `git pull --rebase origin main` first |
| Uploaded `.venv` by accident | Add to `.gitignore`, run `git rm -r --cached .venv`, commit, push |
| Large file rejected | GitHub limit is 100 MB per file; use Releases for big assets |

---

## Checklist before going public

- [ ] `GameAssets/` is included and complete
- [ ] `README.md` instructions tested on a clean PC
- [ ] `LICENSE` file present
- [ ] `.gitignore` excludes `.venv`
- [ ] No passwords, API keys, or personal paths in code
- [ ] Attribution / fan-project disclaimer in README
- [ ] Tests pass: `python -m pytest tests/ -q`

---

**You’re ready to share Kinito with the world!**
