# Contributing

Thank you for helping improve KinitoPET! This project is free and open for everyone to use, modify, and share.

## Quick links

| Guide | What it covers |
|-------|----------------|
| [Installation (beginner)](docs/INSTALL.md) | Python, venv, dependencies, first run |
| [Extending Kinito](docs/EXTENDING.md) | Dialogs, websites, text, sprites, features |
| [Publishing on GitHub](docs/GITHUB.md) | Uploading and sharing the project |
| [README](README.md) | Overview, features, controls |

## Before you open a pull request

1. Install dev dependencies: `pip install -r requirements-dev.txt`
2. Run tests: `python -m pytest tests/ -q`
3. Run the linter: `ruff check .`
4. Describe **what** you changed and **why** in your PR

## What we welcome

- New dialogue lines, jokes, facts, stories, poems
- Bug fixes and clearer error messages
- Documentation improvements (especially for beginners)
- Safe website additions to the whitelist
- Tests for new behavior

## What needs extra care

- **Browser whitelist** (`content/allowed_sites.py`) — only family-friendly HTTPS sites
- **Dialog markers** — every question variant must contain its marker substring (see [EXTENDING.md](docs/EXTENDING.md))
- **Windows-only features** — document if something only works on Windows (e.g. the minimize easter egg)

## Attribution

If you fork this project or use it as a base for your own desktop friend, please credit the original KinitoPET Python Virtual Assistant project and link back to this repository.

## Code of conduct

Be kind. This is a fun desktop companion project — keep contributions welcoming and respectful.
