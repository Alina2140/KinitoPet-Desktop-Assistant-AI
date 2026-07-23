"""Sandboxed in-app browser via pywebview or system default browser."""

import importlib.util
import random
import subprocess
import sys
import threading
import time
import webbrowser

from content import dialogue as dlg
from content.browser_lines import BROWSER_LINES, HORROR_BROWSER_LINES
from content.site_validator import is_allowed_url, pick_random_site
from kinito.assets import kinito_pet_url, list_image_files, websites_directory


class BrowserMixin:
    """Open allow-listed websites in a side window next to Kinito."""

    BROWSER_WIDTH = 1000
    BROWSER_HEIGHT = 800
    BROWSER_MIN_WIDTH = 480
    BROWSER_MIN_HEIGHT = 360
    WEBSITE_SURPRISE_CHANCE = 0.05

    def _has_pywebview(self):
        """Return True if the pywebview package is installed."""
        return importlib.util.find_spec("webview") is not None

    def offer_browser_visit(self):
        """Ask the user whether they want to browse a website together."""
        if self._is_busy_with_speech():
            return
        self.speak(dlg.pick_line(dlg.BROWSER_QUESTIONS), 45, True)

    def ask_browser_category(self):
        """Prompt the user to pick a site category (animals, games, horror, etc.)."""
        if self._is_busy_with_speech():
            return
        self.speak(dlg.BROWSER_CATEGORY_QUESTION, 45, True)

    def _get_browser_position(self):
        """Compute window coordinates beside Kinito for the browser popup."""
        self.root.update_idletasks()
        kinito_x = self.root.winfo_rootx()
        kinito_y = self.root.winfo_rooty()
        kinito_w = max(self.root.winfo_width(), 1)
        gap = 10
        x = kinito_x + kinito_w + gap
        y = kinito_y
        min_x, min_y, max_x, max_y = self.get_screen_bounds(self.BROWSER_WIDTH, self.BROWSER_HEIGHT)
        x = max(min_x, min(int(x), max_x))
        y = max(min_y, min(int(y), max_y))
        return x, y

    def open_allowed_site(self, category):
        """Pick a random allowed site in *category* and launch the browser."""
        if self._browser_active:
            return

        site = pick_random_site(category)
        if not site or not is_allowed_url(site["url"]):
            self.speak(dlg.pick_line(dlg.BROWSER_ERROR_LINES))
            return

        self._browser_category = category
        x, y = self._get_browser_position()

        if category == "horror":
            browse_line = random.choice(HORROR_BROWSER_LINES)
        else:
            browse_line = random.choice(BROWSER_LINES)

        surprise = self._roll_browser_surprise()
        if surprise == "kinitopet":
            site = {"title": "KinitoPET — Official Site", "url": kinito_pet_url}
            threading.Thread(
                target=self._launch_browser,
                args=(site["url"], x, y, browse_line),
                daemon=True,
            ).start()
            return

        if surprise == "fake_image":
            image_path = self._pick_website_image()
            if image_path is not None:
                intro = f"{browse_line} I found a page that looks... familiar."
                threading.Thread(
                    target=self._launch_fake_website,
                    args=(image_path, x, y, intro),
                    daemon=True,
                ).start()
                return

        threading.Thread(
            target=self._launch_browser,
            args=(site["url"], x, y, browse_line),
            daemon=True,
        ).start()

    def _roll_browser_surprise(self):
        """Return 'kinitopet', 'fake_image', or None for a rare browsing twist."""
        if random.random() >= self.WEBSITE_SURPRISE_CHANCE:
            return None
        if random.random() < 0.5:
            return "kinitopet"
        if self._pick_website_image() is not None:
            return "fake_image"
        return "kinitopet"

    def _pick_website_image(self):
        """Return a random screenshot from GameAssets/websites/, if any exist."""
        images = list_image_files(websites_directory)
        if not images:
            return None
        return random.choice(images)

    def _launch_fake_website(self, image_path, x, y, intro):
        """Speak the intro, then show a static website screenshot."""
        self.speak(intro, show_bubble=True, wait_for_tts=True)
        if not self._running:
            return
        self._browser_active = True
        self.root.after(
            0,
            lambda: self._open_fake_website_window(image_path, x, y),
        )
        threading.Thread(
            target=self._wait_for_fake_website,
            args=(self._browser_category,),
            daemon=True,
        ).start()

    def _open_fake_website_window(self, image_path, x, y):
        """Display a website screenshot in a browser-sized popup."""
        self.show_popup_image(
            image_path,
            width=self.BROWSER_WIDTH,
            height=self.BROWSER_HEIGHT,
            x=x,
            y=y,
            title="Kinito's Window",
            on_close=self._finish_fake_website,
        )

    def _finish_fake_website(self):
        """Mark the fake browser session as closed."""
        self._browser_active = False

    def _wait_for_fake_website(self, category):
        """Wait until the fake website window closes, then speak a closing line."""
        while self._browser_active and self._running:
            time.sleep(0.2)
        if not self._running:
            return
        while self.talking and self._running:
            time.sleep(0.1)
        if not self._running:
            return
        if category == "horror":
            line = dlg.pick_line(dlg.BROWSER_HORROR_CLOSE_LINES)
        else:
            line = dlg.pick_line(dlg.BROWSER_CLOSE_LINES)
        self.speak(line)

    def _launch_browser(self, url, x, y, intro):
        """Speak the intro, then open the URL in pywebview or the default browser."""
        self.speak(intro, show_bubble=True, wait_for_tts=True)
        if not self._running:
            return
        if self._has_pywebview():
            self._start_browser_process(url, x, y)
        else:
            webbrowser.open(url)

    def _start_browser_process(self, url, x, y):
        """Spawn a child process running browser_process with the target URL."""
        try:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "kinito.features.browser_process",
                    url,
                    str(x),
                    str(y),
                    str(self.BROWSER_WIDTH),
                    str(self.BROWSER_HEIGHT),
                ],
                stderr=subprocess.PIPE,
                text=True,
            )
        except OSError:
            self._browser_active = False
            self._browser_process = None
            self.speak(dlg.pick_line(dlg.BROWSER_ERROR_LINES))
            return

        self._browser_process = process
        self._browser_active = True
        threading.Thread(
            target=self._wait_for_browser_process,
            args=(self._browser_category,),
            daemon=True,
        ).start()

    def _wait_for_browser_process(self, category):
        """Wait for the browser subprocess and speak a closing line."""
        process = self._browser_process
        if process is None:
            return

        stderr = process.stderr.read() if process.stderr is not None else ""
        exit_code = process.wait()
        self._browser_active = False
        self._browser_process = None

        if not self._running:
            return

        if exit_code != 0:
            if "pywebview not installed" in stderr:
                self.speak(
                    "I'd love to browse with you, but I need pywebview installed. "
                    "Try: pip install pywebview"
                )
            else:
                if stderr.strip():
                    print(f"Browser process failed: {stderr.strip()}", flush=True)
                self.speak(dlg.pick_line(dlg.BROWSER_ERROR_LINES))
            return

        while self.talking and self._running:
            time.sleep(0.1)
        if not self._running:
            return

        if category == "horror":
            line = dlg.pick_line(dlg.BROWSER_HORROR_CLOSE_LINES)
        else:
            line = dlg.pick_line(dlg.BROWSER_CLOSE_LINES)
        self.speak(line)

    def close_browser(self):
        """Terminate the browser subprocess if it is still running."""
        process = getattr(self, "_browser_process", None)
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
        self._browser_active = False
        self._browser_process = None
