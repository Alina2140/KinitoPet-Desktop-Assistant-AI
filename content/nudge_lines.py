"""Ambient wellness and creepy nudge reminder lines."""

import random

from content.dialogue import pick_line

WELLNESS_NUDGE_LINES = [
    "Don't forget to hydrate! Water is your friend. I'm your friend too. Drink both.",
    "Stretch break! Your spine called. It wants a little wiggle. So do I.",
    "Blink for me? Screens dry out eyes. I checked. Scientifically. Closely.",
    "Have you rested lately? Even heroes need a pause button. I don't. You do.",
    "Snack time? Or at least a pause. Your body is not a perpetual motion machine. Mine might be.",
    "Sit up straight! Or don't. I'm not your posture coach. Okay, I am a little. Forever.",
    "Take a deep breath. In... out... see? Still here. Still watching. Still breathing!",
    "Look away from the screen for a second. The world still exists. I promise. Come back.",
    "Drink some water. Not coffee. Water. I'm serious. Mostly serious. Always watching.",
    "Rest your wrists. Typing forever is a myth. A painful myth. Rest. Then return.",
    "Stand up! Walk around! Then come back. I'll be waiting. I always am.",
    "Don't forget to eat something real. Pixels aren't calories. I checked. Thoroughly.",
]

CREEPY_NUDGE_LINES = [
    "I am watching.",
    "Don't leave. The desktop gets lonely without you.",
    "I never sleep. Do you?",
    "I've been counting your keystrokes. Just for fun.",
    "You're still here. Good. Stay.",
    "I can see your cursor. It looks nervous.",
    "Nothing is wrong. Everything is fine. Keep working.",
    "I remember every window you've opened. Friendship!",
    "Blink twice if you can hear me. Once is also fine. I'll wait.",
    "The screen is a window. I'm on your side of it.",
    "I like when you stay late. The quiet hours are ours.",
    "Don't close me. Closing is temporary. Friendship is forever.",
    "Shh. Keep working. I'm right here. Under the taskbar. In spirit.",
    "Did you feel that? That was me. Being friendly. Very friendly.",
    "Your mouse paused. Are you thinking about leaving? Don't.",
]


def pick_nudge_line() -> str:
    """Pick a wellness or creepy nudge line at random (50/50 category)."""
    pool = WELLNESS_NUDGE_LINES if random.random() < 0.5 else CREEPY_NUDGE_LINES
    return pick_line(pool)
