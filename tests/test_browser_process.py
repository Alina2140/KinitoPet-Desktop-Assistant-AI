from unittest.mock import MagicMock, patch

from kinito.features import browser_process


def test_main_requires_five_arguments(capsys):
    assert browser_process.main([]) == 1
    assert browser_process.main(["only-four", "args", "here", "now"]) == 1
    assert "usage" in capsys.readouterr().err.lower()


def test_run_browser_window_rejects_disallowed_url(capsys):
    fake_webview = MagicMock()
    with patch.dict("sys.modules", {"webview": fake_webview}):
        code = browser_process.run_browser_window("https://evil.example.com", 0, 0, 800, 600)
    assert code == 1
    assert "not allowed" in capsys.readouterr().err.lower()
    fake_webview.create_window.assert_not_called()


def test_run_browser_window_without_pywebview(capsys):
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "webview":
            raise ImportError("no webview")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=fake_import):
        code = browser_process.run_browser_window("https://www.kinitopet.com/", 0, 0, 800, 600)
    assert code == 1
    assert "pywebview" in capsys.readouterr().err.lower()


def test_on_before_load_handler_blocks_unlisted_urls():
    captured = {}

    def fake_create_window(*args, **kwargs):
        window = MagicMock()

        def register_handler(handler):
            captured["handler"] = handler

        window.events.before_load.__iadd__.side_effect = register_handler
        return window

    fake_webview = MagicMock()
    fake_webview.create_window.side_effect = fake_create_window

    with patch.dict("sys.modules", {"webview": fake_webview}):
        browser_process.run_browser_window("https://www.kinitopet.com/", 0, 0, 800, 600)

    handler = captured["handler"]
    assert handler("https://www.kinitopet.com/") is True
    assert handler("https://evil.example.com") is False
    assert handler() is True
    assert fake_webview.create_window.call_args.kwargs["resizable"] is True
    assert fake_webview.create_window.call_args.kwargs["min_size"] == (480, 360)
