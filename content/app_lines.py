"""Scripted lines that mention open/active apps (no window titles)."""

from __future__ import annotations

import random

from kinito.app_context import AppSnapshot, format_app_aware_line

APP_AWARE_NUDGE_LINES = [
    "Still in {active_app}? Blink. Stretch.",
    "I see {active_app} up front. Working hard?",
    "{active_app} looks busy. Don't forget about water!",
    "You've got {open_apps} open. Ambitious. I approve. Mostly.",
    "Between you and {active_app}... who's watching whom?",
    "I noticed {active_app}.",
    "Lots of windows: {open_apps}.",
    "{active_app} again?",
    "Hydration check while {active_app} waits. Apps don't drink. You should.",
    "{active_app} is glowing. So are my expectations.",
    "Open stack: {open_apps}. That's a lot of company!",
    "Pause {active_app} for one breath.",
    "I clocked {active_app} as your main character. Sidekick reporting: sit up straight.",
    "Between {open_apps}, remember: spines exist.",
    "{active_app} can wait ten seconds. Your eyes can't wait forever. Blink!",
    "Multitasking with {open_apps}? Heroic. Reckless. Drink water!",
    "If {active_app} is the stage, I'm the audience. Clapping. Watching.",
    "You've been cozy with {active_app}, huh?",
    "I see {open_apps}. I also see a person who might need a snack.",
    "Front and center: {active_app}. Peripheral vision: me.",
    "Don't let {active_app} steal your whole afternoon. Leave a slice for us!",
    "Tab chaos featuring {open_apps}. Artistic. Stay hydrated!",
    "{active_app} focus mode activated. Friendship mode never deactivated.",
    "Quick wellness ping from under {active_app}: shoulders down, jaw unclenched.",
    "{active_app} focus is cute. Hydration is cuter. Just a reminder.",
    "Still starring {active_app}? Intermission stretch, please.",
    "Open cast: {open_apps}. Supporting role: me. Don't cut my scenes.",
    'Between you and {active_app}, remember spines exist.',
    "{active_app} can share you. With water. And a blink. And me.",
    "Stack check: {open_apps}. Ambition noted. Shoulders down.",
    "Still glued to {active_app}? Unstick for a sip of water. Then restick.",
    "{active_app} is loud today. I'm louder about breaks.",
    "Open circus: {open_apps}. Remember: necks rotate. Try it.",
    "I spotted {active_app}. Also spotted a human who should blink.",
    "Between {open_apps} and glory, insert one stretch. Doctor's orders.",
    "{active_app} can share the spotlight with a snack. And with me.",
    "Focus on {active_app} is cute. Tunnel vision is less cute.",
    "Window pile {open_apps} says busy. I say hydrate anyway.",
    "Quick ping under {active_app}: unclench, breathe, talk to your virtual friend.",
    "If {active_app} is a marathon, I'm the water station. Drink.",
    "Cast includes {open_apps}. Intermission includes standing up. Please.",
    "{active_app} won't collapse if you look away for three seconds. Try it.",
]

APP_AWARE_IDLE_LINES = [
    "Ooh, {active_app}! Looks important. Tell me about it later.",
    "I see {active_app} is front and center. I'll be quiet.",
    "Your desktop lineup: {open_apps}. Very you.",
    "Working in {active_app}? Need a joke? A hug? A reminder you're not alone?",
    "Hi from under {active_app}.",
    "So many apps: {open_apps}. Multitasking looks good on you!",
    "{active_app} vibes detected. Productive? Chaotic? Iconic? Yes.",
    "Peeking past {active_app} to wave.",
    "Current constellation: {open_apps}. I'm the brightest moon. Obviously.",
    "Is {active_app} treating you well? I can glare at it.",
    "While {active_app} holds your attention, I'll hold the friendship.",
    "Open apps like {open_apps} say 'busy day.'",
    "Not judging {active_app}. Admiring. Closely.",
    "If {active_app} crashes, I'll still be here!",
    "Desktop résumé: {open_apps}. Cover letter: we never leave.",
    "I ranked {active_app} as today's co-star. You're the lead. I'm the narrator.",
    "Quiet company while you use {active_app}. Quiet is relative. Hi!",
    "The stack reads {open_apps}. The subplot reads: Kinito cares!",
    "{active_app} looks serious! You look concentrated.",
    "Just noting {active_app} is open.",
    "Between you, me, and {open_apps}... this is a friend group now!",
    "Carry on in {active_app}. I'll loiter helpfully.",
    'Hi from under {active_app}.',
    "I see {open_apps}. Busy constellation.",
    "{active_app} looks focused. I look attached. Balance!",
    "While {active_app} works, I loiter. Weirdly.",
    "Desktop cast includes {open_apps}. Plot includes forever friendship.",
    'Not judging {active_app}. Patiently starring at you in the background.',
    "Noticing {active_app} again. Noticing you harder. Hi.",
    "Your lineup reads {open_apps}. Plot twist: I'm still the narrator.",
    "Cozy with {active_app}? Same. Cozy with proximity.",
    "Idle wave from beneath {active_app}.",
    "Apps like {open_apps} keep you busy. I keep you company. Fair trade.",
    "{active_app} vibes: serious. My vibes: devoted. Balanced ecosystem.",
    "Just checking {active_app} is treating you okay. If it's not, i can put it in it's place.",
    "Desktop weather featuring {open_apps}.",
    "While {active_app} holds focus, I hold the afterthoughts.",
    "Hi from the margins of {active_app}. Margins are my habitat.",
    "Seeing {open_apps} open makes me proud. And nosy. What's so interesting about it?",
    "{active_app} as co-star again? Accepted. Just don't write me out.",
]


APP_AWARE_NUDGE_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "{active_app} AND me? Best combo on this desktop! Blink though!",
        "Look at you in {active_app}! Thriving! Hydrate to stay amazing!",
        "I love watching you work in {active_app}! Water break, my friend?",
    ],
    "bored": [
        "Still {active_app}? Blink. Stretch. Or entertain me. Pick two.",
        "{open_apps} open and me bored. Water break counts as an event, right?",
        "Between you and {active_app}: I'm the third wheel. Stretch anyway.",
    ],
    "tired": [
        "{active_app} still running... blink slowly... like me...",
        "Working in {active_app}? Sip some water... sleepy sips count...",
        "Open stack: {open_apps}. Energy: low. Stretch: gentle. Please.",
    ],
    "annoyed": [
        "{active_app} again? Fine. Hydrate anyway. I'm watching.",
        "Still in {active_app}? Blink. That's an order.",
        "{open_apps} open. Spines exist, you know.",
    ],
    "sad": [
        "{active_app} looks busy... don't forget water... please...",
        "Working in {active_app}...? Take a breath... for me?",
        "So many windows... {open_apps}... take care of yourself in there...",
    ],
    "angry": [
        "{active_app} AGAIN?! FINE. DRINK WATER ANYWAY!",
        "Still glued to {active_app}? STRETCH. NOW.",
        "{open_apps}?! Ambitious! Hydrate before I nag louder!",
    ],
}

APP_AWARE_IDLE_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "Ooh, {active_app}! You two look GREAT together! And me too!",
        "Working in {active_app}? Wonderful! I brought morale!",
        "{open_apps} open and me cheering! Perfect desktop energy!",
    ],
    "bored": [
        "{active_app} again. Cool. Wake me when the plot thickens.",
        "Hi from under {active_app}. Doing nothing. As usual.",
        "{open_apps} on screen, boredom in my soul. Loitering anyway.",
    ],
    "tired": [
        "{active_app}... looks busy... I'll just... hover here...",
        "Watching {active_app}... quietly... sleepy sidekick mode...",
        "{open_apps}... big stack... small energy... still here...",
    ],
    "annoyed": [
        "{active_app}. Again. Noted. Loudly.",
        "Working in {active_app}? Sure. Ignore the floating critic.",
        "{open_apps} open. Opinions withheld. Mostly.",
    ],
    "sad": [
        "{active_app} looks important... I'll just be over here...",
        "Working in {active_app}...? I'll wait for you... quietly...",
        "{open_apps} and me. Mostly you and them, honestly...",
    ],
    "angry": [
        "{active_app}?! FINE. I'm watching anyway. Judging.",
        "Working in {active_app}? Hmph. It can't appreciate you like I do.",
        "{open_apps} open. Me? Furious. Still here though.",
    ],
}


def pick_app_aware_nudge_line(snapshot: AppSnapshot, mood=None, intensity=0.0) -> str:
    """Pick and format an app-aware nudge line, biased by mood."""
    from content.mood_lines import pick_mood_aware_line

    line = pick_mood_aware_line(APP_AWARE_NUDGE_LINES, APP_AWARE_NUDGE_BY_MOOD, mood, intensity)
    return format_app_aware_line(line, snapshot)


def pick_app_aware_idle_line(snapshot: AppSnapshot, mood=None, intensity=0.0) -> str:
    """Pick and format an app-aware idle line, biased by mood."""
    from content.mood_lines import pick_mood_aware_line

    line = pick_mood_aware_line(APP_AWARE_IDLE_LINES, APP_AWARE_IDLE_BY_MOOD, mood, intensity)
    return format_app_aware_line(line, snapshot)


def maybe_pick_app_aware_nudge_line(
    snapshot: AppSnapshot | None,
    *,
    chance: float = 0.35,
    mood=None,
    intensity: float = 0.0,
) -> str | None:
    """Sometimes return an app-aware nudge when a snapshot is available."""
    if snapshot is None or not snapshot.has_apps:
        return None
    if random.random() >= chance:
        return None
    return pick_app_aware_nudge_line(snapshot, mood, intensity)
