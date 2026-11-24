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
from kinito.websites import find_saved_website, normalize_saved_websites, split_website_aliases
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

    def save_named_website(self, name, url, aliases, *, previous_name=""):
        store = getattr(self, "_settings", None)
        if store is None:
            raise ValueError("Website settings are unavailable.")
        sites = store.get_saved_websites()
        previous = find_saved_website(previous_name, sites) if previous_name else None
        if previous_name and previous is None:
            raise ValueError("That saved website does not exist. Please check its name.")
        entry = {
            "name": name or (previous["name"] if previous else ""),
            "url": url if url is not None else (previous["url"] if previous else ""),
            "aliases": (previous["aliases"] if previous else []) if aliases is None else (
                split_website_aliases(aliases) if isinstance(aliases, str) else aliases
            ),
        }
        updated = [entry if site is previous else site for site in sites] if previous else [*sites, entry]
        cleaned = normalize_saved_websites(updated)
        store.set_saved_websites(cleaned)
        refresh = getattr(self, "_refresh_saved_websites", None)
        if callable(refresh):
            try:
                refresh()
            except tk.TclError:
                pass
        return find_saved_website(entry["name"], cleaned)

    def delete_named_website(self, name):
        store = getattr(self, "_settings", None)
        if store is None:
            raise ValueError("Website settings are unavailable.")
        sites = store.get_saved_websites()
        entry = find_saved_website(name, sites)
        if entry is None:
            raise ValueError("That saved website does not exist. Please check its name.")
        store.set_saved_websites([site for site in sites if site is not entry])
        refresh = getattr(self, "_refresh_saved_websites", None)
        if callable(refresh):
            try:
                refresh()
            except tk.TclError:
                pass

    def open_saved_website_settings(self):
        if hasattr(self, "close_speech_bubble"):
            try:
                self.close_speech_bubble()
            except Exception:
                pass
        existing = getattr(self, "_saved_websites_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.lift()
                    return existing
            except tk.TclError:
                pass
        window = tk.Toplevel(self.root)
        self._saved_websites_window = window
        window.title("Saved Websites")
        apply_window_icon(window)
        window.wm_attributes("-topmost", True)
        window.geometry("560x430")
        bg = "#e6ded5"
        window.configure(bg=bg)
        tk.Label(window, text="Save a name and optional aliases to open websites from chat.", wraplength=520, bg=bg).pack(pady=8)
        listing = tk.Listbox(window, exportselection=False, height=7)
        listing.pack(fill="both", expand=True, padx=12)
        fields = {}
        for key, title in (("name", "Name"), ("url", "URL"), ("aliases", "Aliases (comma-separated)")):
            row = tk.Frame(window, bg=bg)
            row.pack(fill="x", padx=12, pady=3)
            tk.Label(row, text=title, width=23, anchor="w", bg=bg).pack(side="left")
            fields[key] = tk.StringVar(window)
            tk.Entry(row, textvariable=fields[key]).pack(side="left", fill="x", expand=True)
        status = tk.Label(window, text="", wraplength=520, anchor="w", bg=bg)
        status.pack(fill="x", padx=12)
        editing = ""
        entries = []

        def refresh():
            nonlocal entries
            if not window.winfo_exists():
                return
            entries = self._settings.get_saved_websites()
            listing.delete(0, tk.END)
            for site in entries:
                listing.insert(tk.END, site["name"] + (" — " + ", ".join(site["aliases"]) if site["aliases"] else ""))

        def select(_event=None):
            nonlocal editing
            selected = listing.curselection()
            if not selected:
                return
            site = entries[selected[0]]
            editing = site["name"]
            for key in fields:
                fields[key].set(", ".join(site[key]) if key == "aliases" else site[key])
            status.configure(text="Editing " + editing, fg="black")

        def new():
            nonlocal editing
            editing = ""
            listing.selection_clear(0, tk.END)
            for value in fields.values():
                value.set("")
            status.configure(text="New website", fg="black")

        def save():
            nonlocal editing
            try:
                entry = self.save_named_website(
                    fields["name"].get(), fields["url"].get(), fields["aliases"].get(), previous_name=editing
                )
            except (ValueError, OSError) as exc:
                status.configure(text=str(exc), fg="#b91c1c")
                return
            editing = entry["name"]
            status.configure(text="Saved " + editing, fg="#166534")

        def delete():
            if not editing:
                status.configure(text="Select a saved website to delete.", fg="#b91c1c")
                return
            name = editing
            try:
                self.delete_named_website(name)
            except (ValueError, OSError) as exc:
                status.configure(text=str(exc), fg="#b91c1c")
                return
            new()
            status.configure(text="Deleted " + name, fg="#166534")

        buttons = tk.Frame(window, bg=bg)
        buttons.pack(pady=8)
        tk.Button(buttons, text="New", command=new).pack(side="left", padx=6)
        tk.Button(buttons, text="Save", command=save).pack(side="left", padx=6)
        tk.Button(buttons, text="Delete", command=delete).pack(side="left", padx=6)
        tk.Button(buttons, text="Close", command=window.destroy).pack(side="left", padx=6)
        listing.bind("<<ListboxSelect>>", select)
        self._refresh_saved_websites = refresh
        refresh()
        return window

    def open_chat_website(self, url, force_system, position):
        if not force_system and not is_allowed_url(url):
            raise ValueError("This address is not approved for the embedded browser.")
        if force_system or getattr(self, "_browser_use_system", True) or not self._has_pywebview():
            try:
                opened = webbrowser.open(url)
            except webbrowser.Error as exc:
                raise OSError("The system browser could not be started.") from exc
            if not opened:
                raise OSError("The system browser did not accept the address.")
            return f"Address sent to the system browser: {url}"
        if getattr(self, "_browser_active", False):
            raise ValueError("Kinito's browser is already open. Please close it first.")
        self._start_browser_process(url, *position, silent=True)
        return f"Kinito's browser launch requested for: {url}"

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

    def _start_browser_process(self, url, x, y, *, silent=False):
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
            if silent:
                raise
            self.speak(dlg.pick_line(dlg.BROWSER_ERROR_LINES))
            return

        self._browser_process = process
        self._browser_active = True
        threading.Thread(
            target=self._wait_for_browser_process,
            args=(getattr(self, "_browser_category", None), silent),
            daemon=True,
        ).start()

    def _wait_for_browser_process(self, category, silent=False):
        """Wait for the browser subprocess and speak a closing line."""
        process = self._browser_process
        if process is None:
            return

        stderr = process.stderr.read() if process.stderr is not None else ""
        exit_code = process.wait()
        self._browser_active = False
        self._browser_process = None

        if silent or not self._running or getattr(self, "_chat_mode", False):
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
