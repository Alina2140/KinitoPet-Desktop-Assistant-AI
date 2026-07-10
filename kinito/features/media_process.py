"""Run pywebview for allow-listed video URLs in a separate process."""

import sys

from kinito.window_icon import browser_window_icon_path


def run_video_window(url, x, y, width, height):
    """Open a pywebview window; block navigation to disallowed video URLs."""
    from content.media_validator import is_allowed_video_url

    try:
        import webview
    except ImportError:
        print("pywebview not installed", file=sys.stderr)
        return 1

    if not is_allowed_video_url(url):
        print(f"Video URL not allowed: {url}", file=sys.stderr)
        return 1

    def on_before_load(*args):
        if not args:
            return True
        return is_allowed_video_url(args[0])

    window = webview.create_window(
        title="Kinito's Video",
        url=url,
        width=width,
        height=height,
        x=x,
        y=y,
        resizable=True,
        min_size=(480, 360),
        on_top=True,
    )
    window.events.before_load += on_before_load
    webview.start(debug=False, icon=browser_window_icon_path())
    return 0


def main(argv=None):
    """CLI entry: URL X Y WIDTH HEIGHT."""
    argv = argv or sys.argv[1:]
    if len(argv) != 5:
        print(
            "Usage: python -m kinito.features.media_process URL X Y WIDTH HEIGHT",
            file=sys.stderr,
        )
        return 1

    url, x, y, width, height = argv
    return run_video_window(url, int(x), int(y), int(width), int(height)) or 0


if __name__ == "__main__":
    raise SystemExit(main())
