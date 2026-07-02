"""Run pywebview in a separate process (launched via python -m)."""

import os
import sys

from kinito.assets import favicon_path, icon_path


def _browser_icon_path() -> str | None:
    """Return an absolute icon path for pywebview, preferring the PNG favicon."""
    for path in (favicon_path, icon_path):
        if os.path.isfile(path):
            return os.path.abspath(path)
    return None


def run_browser_window(url, x, y, width, height):
    """Open a pywebview window at the given position; block navigation to disallowed URLs."""
    from content.site_validator import is_allowed_url

    try:
        import webview
    except ImportError:
        print("pywebview not installed", file=sys.stderr)
        return 1

    if not is_allowed_url(url):
        print(f"URL not allowed: {url}", file=sys.stderr)
        return 1

    def on_before_load(*args):
        if not args:
            return True
        return is_allowed_url(args[0])

    icon = _browser_icon_path()
    window_kwargs = {
        "title": "Kinito's Window",
        "url": url,
        "width": width,
        "height": height,
        "x": x,
        "y": y,
        "resizable": True,
        "min_size": (480, 360),
        "on_top": True,
    }
    if icon is not None:
        window_kwargs["icon"] = icon

    window = webview.create_window(**window_kwargs)
    window.events.before_load += on_before_load
    webview.start(debug=False)
    return 0


def main(argv=None):
    """CLI entry: URL X Y WIDTH HEIGHT."""
    argv = argv or sys.argv[1:]
    if len(argv) != 5:
        print(
            "Usage: python -m kinito.features.browser_process URL X Y WIDTH HEIGHT",
            file=sys.stderr,
        )
        return 1

    url, x, y, width, height = argv
    return run_browser_window(url, int(x), int(y), int(width), int(height)) or 0


if __name__ == "__main__":
    raise SystemExit(main())
