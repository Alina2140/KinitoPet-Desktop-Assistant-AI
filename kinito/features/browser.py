"""Sandboxed in-app browser via pywebview or system default browser."""

import importlib.util
import random
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser

from PIL import Image, ImageTk

from content import dialogue as dlg
from content import llm_prompts as prompts
from content.browser_lines import BROWSER_LINES, CATEGORY_BROWSER_LINES
from content.site_validator import is_allowed_url, pick_random_site
from kinito.assets import kinito_pet_url, list_image_files, websites_directory
from kinito.tk_toplevels import (
    create_staged_toplevel,
    pin_assistant_screen_position,
    reveal_staged_toplevel,
    schedule_assistant_position_restore,
)
from kinito.window_icon import apply_window_icon


class BrowserMixin:
    """Open allow-listed websites in a side window next to Kinito."""

    BROWSER_WIDTH = 1000
    BROWSER_HEIGHT = 800
    BROWSER_MIN_WIDTH = 480
    BROWSER_MIN_HEIGHT = 360
    WEBSITE_SURPRISE_CHANCE = 0.05
    GENERAL_BROWSER_LINE_CHANCE = 0.3
    BROWSER_OPEN_DEADLINE_S = 10.0
    CATEGORY_CLOSE_LINES = {
        "animals": dlg.BROWSER_ANIMALS_CLOSE_LINES,
        "knowledge": dlg.BROWSER_KNOWLEDGE_CLOSE_LINES,
        "games": dlg.BROWSER_GAMES_CLOSE_LINES,
        "horror": dlg.BROWSER_HORROR_CLOSE_LINES,
    }

    def _browser_line_pool(self, category, category_pools, general_pool):
        """Return the category's pool, or sometimes the general one (horror always stays spooky)."""
        pool = category_pools.get(category)
        if not pool:
            return general_pool
        if category != "horror" and random.random() < self.GENERAL_BROWSER_LINE_CHANCE:
            return general_pool
        return pool

    def _browser_close_line(self, category):
        """Pick a closing line that fits the category of the site that was open."""
        pool = self._browser_line_pool(
            category, self.CATEGORY_CLOSE_LINES, dlg.BROWSER_CLOSE_LINES
        )
        mood = self.get_mood() if hasattr(self, "get_mood") else None
        intensity = self.get_mood_intensity() if hasattr(self, "get_mood_intensity") else 0.0
        from content.mood_lines import pick_mood_aware_line

        return pick_mood_aware_line(pool, dlg.BROWSER_CLOSE_BY_MOOD, mood, intensity)

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

        browse_line = random.choice(
            self._browser_line_pool(category, CATEGORY_BROWSER_LINES, BROWSER_LINES)
        )

        surprise = self._roll_browser_surprise()
        if surprise == "kinitopet":
            site = {"title": "KinitoPET — Official Site", "url": kinito_pet_url}
            threading.Thread(
                target=self._launch_browser,
                args=(site["url"], x, y, browse_line, category),
                daemon=True,
            ).start()
            return

        if surprise == "fake_image":
            image_path = self._pick_website_image()
            if image_path is not None:
                intro = f"{browse_line} I found a page that looks... familiar."
                threading.Thread(
                    target=self._launch_fake_website,
                    args=(image_path, x, y, intro, category),
                    daemon=True,
                ).start()
                return

        threading.Thread(
            target=self._launch_browser,
            args=(site["url"], x, y, browse_line, category),
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
        """Return a random screenshot from gameAssets/websites/, if any exist."""
        images = list_image_files(websites_directory)
        if not images:
            return None
        return random.choice(images)

    def _run_on_ui(self, fn):
        """Run *fn* on the Tk main thread (immediately when already there)."""
        if threading.current_thread() is threading.main_thread():
            fn()
            return
        schedule = getattr(self, "_call_on_ui", None)
        if callable(schedule):
            schedule(fn)
            return
        try:
            self.root.after(0, fn)
        except Exception:
            pass

    def _speak_browser_intro(self, intro, deadline, category=None):
        """Speak *intro*, preferring an AI-generated line, bounded by *deadline*.

        The Ollama request runs on a daemon thread so a slow model can never
        push the browser open past the deadline; on timeout the scripted
        line is used instead. While generation runs, the thinking sprite is
        shown on the UI thread.
        """
        spoken = intro
        gen = getattr(self, "generate_line_sync", None)
        should_replace = getattr(self, "_should_ai_replace", None)
        will_generate = (
            callable(gen)
            and callable(should_replace)
            and not getattr(self, "_ai_generating", False)
            and should_replace(intro)
        )
        if will_generate:
            ai_hint = prompts.build_browse_website_prompt(category)
            show_thinking = getattr(self, "_show_ai_thinking_sprite", None)
            if callable(show_thinking):
                self._run_on_ui(show_thinking)
            done = threading.Event()
            box = {}

            def gen_worker():
                try:
                    box["line"] = gen(intro, ai_hint=ai_hint)
                finally:
                    done.set()

            threading.Thread(target=gen_worker, daemon=True).start()
            done.wait(timeout=max(0.0, deadline - time.monotonic()))
            spoken = box.get("line") or intro
            clear_thinking = getattr(self, "_clear_ai_generating", None)
            if callable(clear_thinking):
                self._run_on_ui(clear_thinking)
        self.speak(
            spoken,
            show_bubble=True,
            wait_for_tts=True,
            max_wait_s=max(0.0, deadline - time.monotonic()),
        )

    def _launch_fake_website(self, image_path, x, y, intro, category=None):
        """Speak the intro, then show a static website screenshot."""
        deadline = time.monotonic() + self.BROWSER_OPEN_DEADLINE_S
        self._speak_browser_intro(intro, deadline, category)
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
        """Display a website screenshot in a scrollable browser-sized window."""
        try:
            img = Image.open(image_path)
        except OSError:
            self._finish_fake_website()
            return

        # Fit the screenshot to the window width; scroll handles the height.
        width = self.BROWSER_WIDTH
        scale = width / max(img.width, 1)
        scaled_h = max(1, int(img.height * scale))
        if img.size != (width, scaled_h):
            img = img.resize((width, scaled_h), Image.Resampling.LANCZOS)

        pin = getattr(self, "_pin_assistant_screen_position", None)
        pinned = pin() if callable(pin) else pin_assistant_screen_position(self)
        popup = create_staged_toplevel(self.root)
        popup.title("Kinito's Window")
        apply_window_icon(popup)
        try:
            popup.wm_attributes("-toolwindow", True)
        except tk.TclError:
            pass

        canvas = tk.Canvas(popup, bd=0, highlightthickness=0, bg="white")
        canvas.pack(side="left", fill="both", expand=True)
        if scaled_h > self.BROWSER_HEIGHT:
            scrollbar = tk.Scrollbar(popup, orient="vertical", command=canvas.yview)
            scrollbar.pack(side="right", fill="y")
            canvas.configure(yscrollcommand=scrollbar.set)

        tk_img = ImageTk.PhotoImage(img)
        canvas.create_image(0, 0, anchor="nw", image=tk_img)
        canvas.image = tk_img
        canvas.configure(scrollregion=(0, 0, width, scaled_h))

        def _on_mousewheel(event):
            canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        def _handle_close():
            self._finish_fake_website()
            try:
                popup.destroy()
            except tk.TclError:
                pass

        popup.protocol("WM_DELETE_WINDOW", _handle_close)
        reveal_staged_toplevel(
            popup,
            geometry=f"{width}x{self.BROWSER_HEIGHT}+{int(x)}+{int(y)}",
            noactivate=True,
        )
        schedule_assistant_position_restore(self, *pinned)

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
        self.speak(self._browser_close_line(category))

    def _launch_browser(self, url, x, y, intro, category=None):
        """Speak the intro, then open the URL in pywebview or the default browser."""
        deadline = time.monotonic() + self.BROWSER_OPEN_DEADLINE_S
        self._speak_browser_intro(intro, deadline, category)
        if not self._running:
            return
        if not getattr(self, "_browser_use_system", True) and self._has_pywebview():
            self._start_browser_process(url, x, y)
            return
        try:
            opened = webbrowser.open(url)
        except webbrowser.Error:
            opened = False
        if not opened:
            self.speak(dlg.pick_line(dlg.BROWSER_ERROR_LINES))

    def toggle_browser_mode(self):
        self._browser_use_system = not getattr(self, "_browser_use_system", True)
        if hasattr(self, "_persist_settings"):
            self._persist_settings()
        self.speak(
            dlg.BROWSER_SYSTEM_SELECTED
            if self._browser_use_system
            else dlg.BROWSER_KINITO_SELECTED,
            skip_ai=True,
        )

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

        self.speak(self._browser_close_line(category))

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
