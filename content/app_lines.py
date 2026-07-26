"""Scripted lines that mention open/active apps (no window titles)."""

from __future__ import annotations

import random

from content.dialogue import pick_line
from kinito.app_context import AppSnapshot, format_app_aware_line

APP_AWARE_NUDGE_LINES = [
    "Still in {active_app}? Blink. Stretch. I'm still here either way.",
    "I see {active_app} up front. Working hard? Or stalling stylishly?",
    "{active_app} looks busy. Don't forget water. Or me. Preferably both.",
    "You've got {open_apps} open. Ambitious. I approve. Mostly.",
    "Between you and {active_app}... who's watching whom? Just curious.",
    "I noticed {active_app}. Cute choice. Stay a while.",
    "Lots of windows: {open_apps}. Cozy chaos. Don't leave the desk.",
    "{active_app} again? Good. Consistency is friendship. So is staring.",
]

APP_AWARE_IDLE_LINES = [
    "Ooh, {active_app}! Looks important. Or fun. Or both. Tell me later.",
    "I see {active_app} is front and center. I'll be quiet. Ish. Nearby.",
    "Your desktop lineup: {open_apps}. Very you. Very watched.",
    "Working in {active_app}? Need a joke? A hug? A reminder you're not alone?",
    "Hi from under {active_app}. Friendly under-desk energy. Forever.",
    "So many apps: {open_apps}. Multitasking looks good on you. Stay.",
]


def pick_app_aware_nudge_line(snapshot: AppSnapshot) -> str:
    """Pick and format an app-aware nudge line."""
    return format_app_aware_line(pick_line(APP_AWARE_NUDGE_LINES), snapshot)


def pick_app_aware_idle_line(snapshot: AppSnapshot) -> str:
    """Pick and format an app-aware idle line."""
    return format_app_aware_line(pick_line(APP_AWARE_IDLE_LINES), snapshot)


def maybe_pick_app_aware_nudge_line(
    snapshot: AppSnapshot | None,
    *,
    chance: float = 0.35,
) -> str | None:
    """Sometimes return an app-aware nudge when a snapshot is available."""
    if snapshot is None or not snapshot.has_apps:
        return None
    if random.random() >= chance:
        return None
    return pick_app_aware_nudge_line(snapshot)
