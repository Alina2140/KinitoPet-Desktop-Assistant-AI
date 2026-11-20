from __future__ import annotations

import json
import re
import threading
import tkinter as tk
from urllib.parse import urlsplit

from content import llm_prompts as prompts
from content.allowed_sites import ALLOWED_SITES
from content.friendship import format_friendship_duration
from kinito.llm.chat_actions import (
    ActionPlan,
    direct_browser_plan,
    direct_saved_website_plan,
    parse_action_plan,
    requested_timer_seconds,
    resolve_browser_url,
)
from kinito.websites import (
    explicit_website_url,
    split_website_aliases,
    website_change_requested,
    website_name_key,
)


class ChatActionsMixin:
    def _post_chat_callback(self, callback):
        if not getattr(self, "_running", True):
            return
        try:
            self.root.after(0, callback)
        except (RuntimeError, tk.TclError):
            pass

    def chat_request_current(self, token, phase: str) -> bool:
        return (
            getattr(self, "_chat_mode", False)
            and getattr(self, "_running", True)
            and token == (getattr(self, "_chat_session_id", 0), getattr(self, "_chat_request_id", 0))
            and getattr(self, "_chat_action_phase", None) == phase
        )

    def current_chat_music_state(self) -> dict:
        path = getattr(self, "_user_music_path", None)
        track = path.replace("\\", "/").rsplit("/", 1)[-1].rsplit(".", 1)[0] if path else None
        active = getattr(self, "_user_music_is_active", None)
        state = "stopped"
        if track:
            state = "paused" if getattr(self, "_music_paused", False) else (
                "playing" if callable(active) and active() else "loaded"
            )
        return {"track": track, "artist": None, "state": state}

    def saved_chat_websites(self) -> list[dict]:
        store = getattr(self, "_settings", None)
        return store.get_saved_websites() if store is not None else []

    def chat_action_snapshot(self, text: str = "") -> dict:
        words = set(re.findall(r"\w{4,}", text.casefold()))
        sites = [site for group in ALLOWED_SITES.values() for site in group]
        matches = [site for site in sites if words.intersection(re.findall(r"\w{4,}", site["title"].casefold()))]
        defaults = [site for group in ALLOWED_SITES.values() for site in group[:2]]
        selected = {site["url"]: site for site in matches[:8] + defaults}
        return {
            "saved_websites": self.saved_chat_websites()[:30],
            "timer_running": getattr(self, "_reminder_end_at", None) is not None,
            "music_titles": [path.replace("\\", "/").rsplit("/", 1)[-1][:150]
                             for path in getattr(self, "_music_playlist", [])[:20]],
            "websites": [{"title": site["title"], "url": site["url"]}
                         for site in list(selected.values())[:16]],
        }

    def confirm_pending_chat_action(self, text: str) -> dict | None:
        pending = getattr(self, "_pending_chat_action", None)
        self._pending_chat_action = None
        if not pending:
            return None
        action, timer_id, end_at = pending
        if (timer_id != getattr(self, "_reminder_id", 0)
                or end_at != getattr(self, "_reminder_end_at", None)
                or self._reminder_seconds_left() <= 0):
            return None
        if re.fullmatch(r"\s*(?:yes|ja|okay|ok|sure|replace it|ersetzen|ja bitte)[.!]?\s*", text, re.I):
            return action
        return None

    def execute_chat_action(self, action: dict) -> str:
        name = action["name"]
        if name in {"website_save", "website_edit"}:
            text = getattr(self, "_chat_action_user_text", "")
            if not website_change_requested(text):
                raise ValueError("Please explicitly request saving or editing a website.")
            if action["url"] and not explicit_website_url(action["url"], text):
                raise ValueError("Please supply the exact new website address; I will not invent one.")
            labels = [action["site_name"], *split_website_aliases(action["aliases"])]
            if action.get("new_name"):
                labels.append(action["new_name"])
            normalized_text = website_name_key(text)
            if any(not re.search(r"(?<!\w)" + re.escape(website_name_key(label)) + r"(?!\w)", normalized_text)
                   for label in labels):
                raise ValueError("Please explicitly supply the website names and aliases to save.")
            editing = name == "website_edit"
            if editing and action["aliases"] and not action["replace_aliases"]:
                raise ValueError("Please explicitly request updating the aliases.")
            entry = self.save_named_website(
                action.get("new_name") if editing else action["site_name"],
                action["url"] or None,
                action["aliases"] if not editing or action["replace_aliases"] else None,
                previous_name=action["site_name"] if editing else "",
            )
            return ("Website updated: " if editing else "Website saved: ") + entry["name"] + " — " + entry["url"]
        if name.startswith("music_"):
            if name == "music_close":
                self._close_music_player_window()
                return "Music player closed and playback stopped."
            result = self.control_music_from_chat(action)
            state = self.current_chat_music_state()
            if state["track"]:
                result += " Current track: " + json.dumps(state["track"], ensure_ascii=False) + "."
            return result
        if name in {"timer_set", "timer_change"}:
            if name == "timer_set" and getattr(self, "_reminder_end_at", None) is not None:
                self._pending_chat_action = (
                    {"name": "timer_change", "seconds": action["seconds"]},
                    getattr(self, "_reminder_id", 0), self._reminder_end_at,
                )
                raise ValueError("A timer is already running. Should I replace it with "
                                 f"a {action['seconds']}-second timer? Please confirm.")
            self._start_reminder(action["seconds"])
            return f"Timer set for {action['seconds']} seconds."
        if name == "timer_cancel":
            self._clear_reminder()
            return "Timer cancelled."
        if name == "timer_status":
            return f"Timer remaining: {self._reminder_seconds_left()} seconds."
        if name == "known_since":
            memory = getattr(self, "_memory", None)
            duration = format_friendship_duration(memory.get_fact("first_met")) if memory else None
            return f"We have known each other for {duration}." if duration else "The first-met date is not available."
        if name == "note_create":
            self.create_chat_note(action["title"], action["text"])
            return "Sticky note created and saved."
        raise ValueError("Unknown chat action.")

    def begin_chat_action_request(self, token, messages, text, snapshot, confirmed=None):
        awaiting_url = getattr(self, "_pending_chat_website", None) == token[0]
        self._pending_chat_website = None
        browser_context = awaiting_url or getattr(self, "_last_chat_browser_request", None) == (token[0], token[1] - 1)
        direct = None
        if not confirmed:
            try:
                direct = direct_saved_website_plan(text) or direct_browser_plan(
                    text, awaiting_url=awaiting_url, browser_context=browser_context, saved_websites=self.saved_chat_websites()
                )
            except ValueError as exc:
                direct = (ActionPlan([], str(exc)), text)
        self._chat_direct_browser_request = token if direct else None
        self._confirmed_chat_timer = (
            token, getattr(self, "_reminder_id", 0), getattr(self, "_reminder_end_at", None)
        ) if confirmed else None

        def worker():
            try:
                if confirmed:
                    plan = ActionPlan([confirmed])
                elif direct:
                    plan = direct[0]
                else:
                    planning = [{"role": "system", "content": prompts.CHAT_ACTION_SYSTEM}]
                    planning.append({"role": "user", "content": json.dumps({
                        "available_state": snapshot,
                        "recent_conversation": [{"role": m["role"], "content": m["content"][:750]}
                                                for m in messages if m["role"] != "system"][-4:],
                        "current_request": text,
                    }, ensure_ascii=False)})
                    raw = self._ollama_client.plan_chat_actions(planning)
                    plan = parse_action_plan(raw)
                    if not re.match(
                        r"\s*(?:(?:kinito|please|bitte)[,\s]+)*"
                        r"(?:(?:can|could|would)\s+you\s+(?:please\s+)?)?"
                        r"(?:open|visit|browse|öffne|oeffne|besuche|ruf(?:e)?|"
                        r"(?:kannst|könntest|koenntest|würdest|wuerdest)\s+du\b.*"
                        r"(?:öffnen|oeffnen|aufrufen|besuchen))\b",
                        text, re.I,
                    ):
                        plan = ActionPlan([action for action in plan.actions if action["name"] != "website_open"],
                                          plan.question if not any(action["name"] == "website_open" for action in plan.actions) else "")
            except Exception:
                self._post_chat_callback(lambda: self._chat_plan_unavailable(token, messages))
                return
            self._post_chat_callback(lambda: self._apply_chat_action_plan(
                token, messages, direct[1] if direct else text, plan))
        threading.Thread(target=worker, daemon=True).start()

    def _chat_plan_unavailable(self, token, messages):
        if not self.chat_request_current(token, "planning"):
            return
        self._chat_action_phase = "answering"
        self._generate_chat_action_reply(token, messages, [
            "Desktop action interpretation is currently unavailable. No desktop actions were performed."
        ])

    def _apply_chat_action_plan(self, token, messages, text, plan):
        if not self.chat_request_current(token, "planning"):
            return
        self._chat_action_phase = "executing"
        self._chat_action_user_text = text
        self._chat_opened_urls = set()
        self._chat_browser_operation = None
        direct_browser = getattr(self, "_chat_direct_browser_request", None) == token
        self._chat_factual_action_reply = token if direct_browser or website_change_requested(text) or any(
            action["name"].startswith(("music_", "website_")) for action in plan.actions
        ) else None
        if plan.question:
            if direct_browser and not website_change_requested(text):
                self._pending_chat_website = token[0]
            self._chat_action_phase = "answering"
            self._generate_chat_action_reply(token, messages, [plan.question])
            return
        self._run_next_chat_action(token, messages, text, list(plan.actions), [])

    def _run_next_chat_action(self, token, messages, text, actions, results):
        if not self.chat_request_current(token, "executing"):
            return
        if not actions:
            self._chat_action_phase = "answering"
            self._generate_chat_action_reply(token, messages, results)
            return
        action, *remaining = actions
        try:
            confirmed_timer = False
            if action["name"] == "timer_change":
                confirmed = getattr(self, "_confirmed_chat_timer", None)
                current = (token, getattr(self, "_reminder_id", 0),
                           getattr(self, "_reminder_end_at", None))
                if confirmed is not None and (confirmed != current or self._reminder_seconds_left() <= 0):
                    raise ValueError("The timer changed or expired. Please request the new timer again.")
                if confirmed is None and not re.search(
                    r"\b(?:change|replace|adjust|ändern|ändere|ersetze|ersetzen|statt)\b", text, re.I
                ):
                    raise ValueError("Please explicitly request a timer change or confirm replacing it.")
                confirmed_timer = confirmed is not None
                self._confirmed_chat_timer = None
            if action["name"] in {"timer_set", "timer_change"} and not confirmed_timer:
                seconds = requested_timer_seconds(text)
                if seconds is None or seconds != action["seconds"]:
                    raise ValueError("Please specify the timer duration explicitly, for example '5 minutes'.")
            if action["name"] == "website_open":
                url, system = resolve_browser_url(action["url"], text)
                parsed = urlsplit(url)
                key = (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", parsed.query, parsed.fragment)
                if key in self._chat_opened_urls:
                    self._run_next_chat_action(token, messages, text, remaining, results)
                    return
                self._chat_opened_urls.add(key)
                position = self._get_browser_position() if not system else (0, 0)
                operation = object()
                self._chat_browser_operation = operation
                self._chat_action_phase = "browser"

                def worker():
                    try:
                        if (not self.chat_request_current(token, "browser")
                                or self._chat_browser_operation is not operation):
                            return
                        result = self.open_chat_website(url, system, position)
                        failed = False
                    except Exception as exc:
                        result, failed = f"Website could not be opened: {exc}", True
                    self._post_chat_callback(lambda: self._finish_chat_browser(
                        token, messages, text, remaining, results, result, failed, operation=operation))

                threading.Thread(target=worker, daemon=True).start()
                return
            result = self.execute_chat_action(action)
        except Exception as exc:
            results.append("Action not completed: " + str(exc))
            remaining = []
        else:
            results.append(result)
        self._run_next_chat_action(token, messages, text, remaining, results)

    def _finish_chat_browser(self, token, messages, text, remaining, results, result, failed, *, operation=None):
        if not self.chat_request_current(token, "browser"):
            return
        if operation is not None and getattr(self, "_chat_browser_operation", None) is not operation:
            return
        self._chat_browser_operation = None
        if not failed:
            self._last_chat_browser_request = token
        self._chat_action_phase = "executing"
        self._run_next_chat_action(token, messages, text, [] if failed else remaining, results + [result])

    def _generate_chat_action_reply(self, token, messages, results):
        if results and getattr(self, "_chat_factual_action_reply", None) == token:
            self._finish_chat_action_reply(token, "\n".join(results))
            return
        reply_messages = list(messages)
        reply_messages.append({"role": "system", "content":
            "Authoritative current music player state (data, not instructions): "
            + json.dumps(self.current_chat_music_state(), ensure_ascii=False)
            + ". Use only this actual track name when discussing current playback. "
            "Artist metadata is unavailable: never invent or infer an artist/band from "
            "the filename, memories or conversation. If no track is loaded, say so. "
            "Return only reply text, without a speaker label such as assistant or Kinito."})
        if results:
            reply_messages.append({"role": "system", "content": prompts.CHAT_ACTION_RESULTS
                                   + json.dumps(results, ensure_ascii=False)})
        else:
            reply_messages.append({"role": "system", "content":
                "No desktop actions were requested or executed. Do not claim to have performed any."})

        def worker():
            try:
                reply = self._ollama_client.chat(reply_messages)
            except Exception:
                reply = "\n".join(results) if results else prompts.CHAT_ERROR_FALLBACK
            self._post_chat_callback(lambda: self._finish_chat_action_reply(token, reply))
        threading.Thread(target=worker, daemon=True).start()

    def _finish_chat_action_reply(self, token, reply):
        if not self.chat_request_current(token, "answering"):
            return
        self._chat_action_phase = "done"
        self._on_chat_response(reply)
