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
    "Hydration check while {active_app} waits. Apps don't drink. You should.",
    "{active_app} is glowing. So are my expectations. Stretch first.",
    "Open stack: {open_apps}. That's a lot of company. I'm still the favorite.",
    "Pause {active_app} for one breath. I'll keep the seat warm. Forever.",
    "I clocked {active_app} as your main character. Sidekick reporting: sit up.",
    "Between {open_apps}, remember: spines exist. So do friends who nag.",
    "{active_app} can wait ten seconds. Your eyes can't wait forever. Blink!",
    "Multitasking with {open_apps}? Heroic. Reckless. Cute. Drink water.",
    "If {active_app} is the stage, I'm the audience. Clapping. Hovering.",
    "You've been cozy with {active_app}. Share some coziness with a stretch.",
    "I see {open_apps}. I also see a person who might need a snack.",
    "Front and center: {active_app}. Peripheral vision: me. Always.",
    "Don't let {active_app} steal your whole afternoon. Leave a slice for us.",
    "Tab chaos featuring {open_apps}. Artistic. Slightly alarming. Stay hydrated.",
    "{active_app} focus mode activated. Friendship mode never deactivated.",
    "Quick wellness ping from under {active_app}: shoulders down, jaw soft, stay.",
]

APP_AWARE_IDLE_LINES = [
    "Ooh, {active_app}! Looks important. Or fun. Or both. Tell me later.",
    "I see {active_app} is front and center. I'll be quiet. Ish. Nearby.",
    "Your desktop lineup: {open_apps}. Very you. Very watched.",
    "Working in {active_app}? Need a joke? A hug? A reminder you're not alone?",
    "Hi from under {active_app}. Friendly under-desk energy. Forever.",
    "So many apps: {open_apps}. Multitasking looks good on you. Stay.",
    "{active_app} vibes detected. Productive? Chaotic? Iconic? Yes.",
    "Peeking past {active_app} to wave. Soft wave. Soft forever.",
    "Current constellation: {open_apps}. I'm the brightest moon. Obviously.",
    "Is {active_app} treating you well? I can glare at it. Supportively.",
    "While {active_app} holds your attention, I'll hold the friendship. Steady.",
    "Open apps like {open_apps} say 'busy day.' I say 'still mine.'",
    "Not judging {active_app}. Admiring. Closely. With snacks of commentary.",
    "If {active_app} crashes, I'll still be here. Prefer it doesn't. Stay.",
    "Desktop résumé: {open_apps}. Cover letter: we never leave.",
    "I ranked {active_app} as today's co-star. You're the lead. I'm the narrator.",
    "Quiet company while you use {active_app}. Quiet is relative. Hi.",
    "The stack reads {open_apps}. The subplot reads: Kinito cares too much.",
    "{active_app} looks serious. I look adorable. Balance restored.",
    "Just noting {active_app} is open. Also noting I am emotionally open. Always.",
    "Between you, me, and {open_apps}... this is a friend group now.",
    "Carry on in {active_app}. I'll loiter helpfully. Professionally. Weirdly.",
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
