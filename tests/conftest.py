from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_app():
    app = MagicMock()
    app._running = True
    app._browser_active = False
    app._focus_mode = False
    app.talking = False
    app._awaiting_response = False
    app.speak = MagicMock()
    app.speak_brief = MagicMock()
    app.root = MagicMock()
    app.root.after = MagicMock(
        side_effect=lambda delay, fn, *args: fn(*args) if callable(fn) else None
    )
    return app
