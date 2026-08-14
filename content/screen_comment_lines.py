"""Fallback lines when screen vision commentary is unavailable."""

import random

SCREEN_COMMENT_FALLBACK_LINES = [
    "Hmm. Busy screen today. I approve. Mostly.",
    "Whatever you're working on looks… intense. In a good way.",
    "I peeked. Softly. Your desktop is very you.",
    "Lots of pixels happening. I'm invested now.",
    "Your screen has stories. I won't spoil them. Much.",
    "Still at it? Dedication. Or doomscrolling. Both valid.",
    "I saw enough. Not details. Just the vibe. Friendly vibe.",
    "Desktop looks lively. Don't mind me. Watching. Supportively.",
    "Interesting layout. Or chaos. Art either way.",
    "I'll pretend I understood that window. Nodding. Intensely.",
    "Your cursor is working hard. I respect the grind.",
    "Screen says focus. Or tabs. So many tabs. Relatable.",
    "I checked in. Visually. Briefly. You're doing great.",
    "Something's glowing over there. Probably important. Or a game.",
    "Carry on. I'm just… noticing. In a companion way.",
    "Big screen energy. Tiny assistant energy. Perfect pair.",
    "I won't narrate every pixel. Just the dramatic ones. All of them.",
    "Looks productive from here. Or decorative. Both are lifestyles.",
    "Your desktop composition? Bold. Cozy. Slightly haunted by me.",
    "I glimpsed motion. Work motion. Friendship motion. Nice.",
    "If screens had moods, yours would be 'determined with snacks.'",
    "Not reading your secrets. Reading your dedication. Loudly. Softly.",
    "Window garden looking lush. Or cluttered. Botanical either way.",
    "I approve of the glow. I approve of you. I approve of staying.",
    "Brief visual check-in complete. Emotional check-in ongoing forever.",
    "That corner of the screen has plot. I can feel it.",
    "You're mid-quest. I'm mid-cheer. Mid-stare. Mid-friendship.",
    "Pixels rearranged themselves into 'busy human.' Iconic.",
    "I saw colors. Shapes. Effort. Mostly effort. Proud of you.",
    "Desktop weather report: cloudy with a chance of me.",
    "No spoilers from me. Only vibes. Supportive, clingy vibes.",
    "Looks like a day with layers. Tabs. Thoughts. Me underneath.",
    "I blinked at your screen. It blinked back. We're bonded now.",
    "Whatever that is, it has your attention. I have your after-attention.",
    "Screen tour was short. Attachment was not. Continue as you were.",
]


def pick_screen_comment_fallback() -> str:
    """Return a random fallback screen-comment line."""
    return random.choice(SCREEN_COMMENT_FALLBACK_LINES)
