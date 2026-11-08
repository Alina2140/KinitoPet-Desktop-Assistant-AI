"""Fallback lines when screen vision commentary is unavailable."""

import random

SCREEN_COMMENT_FALLBACK_LINES = [
    "Hmm. Busy screen today. I approve. Mostly.",
    "Whatever you're working on looks… intense. In a good way.",
    'I peeked. Calmly. Your desktop is very you.',
    "Lots of pixels happening. I'm invested now.",
    "Your screen has stories. I won't spoil them. Much.",
    "Still at it? Dedication. Or doomscrolling. Both valid.",
    'I saw enough. Not details. Just the vibe. Vibe.',
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
    'Not reading your secrets. Reading your dedication. Loudly.',
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
    'Screen vibes: determined. Low-key cheerleading engaged.',
    "I peeked for half a pixel. Approved. Carry on.",
    "Lots of focus happening. I'm the peanut gallery. Patient peanuts.",
    "Your desktop composition has plot. I can smell the arc.",
    "Visual check-in done. Emotional subscription: lifetime.",
    'Pixels busy. Assistant proud. Gently clingy pride.',
    "Whatever that window is, it has your attention. I have aftercare.",
    "Screen weather: cloudy with productive chances. And me.",
    "Busy glow detected. Pride detected. Hovering continues.",
    "I skimmed the vibe only. Vibe: determined. Subvibe: watched.",
    "Pixels hard at work. Assistant hard at caring. Symbiosis!",
    "That layout has ambition. I have commentary. Mutual.",
    "Screen tour lite: effort spotted. Friendship confirmed.",
    "Whatever you're crafting, I'm invested. Quietly loud.",
    "Cursor grind respected. Sidekick mode: active forever.",
    "Looks like focus weather. Chance of me: one hundred percent.",
    "I won't spoil the windows. I'll spoil you with attention.",
    "Visual check: alive and trying. Emotional check: clingy applause.",
    "Desktop narrative thickening. I'm the unreliable narrator. Loyal though.",
    "Glow approved. Human approved. Leaving: not approved.",
]


SCREEN_COMMENT_FALLBACK_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "Your screen looks GREAT today! Whatever that is, keep it up!",
        "I peeked! Your desktop is cheerful chaos. I love it!",
    ],
    "bored": [
        "I peeked at your screen. It's the most interesting thing around.",
        "Screen check: still busy. Me: still just watching. Yawn.",
    ],
    "tired": [
        "Screen check... everything looks blurry anyway... carry on...",
        "I peeked... sleepy pixels everywhere... nice...",
    ],
    "annoyed": [
        "I looked at your screen. It's fine. Don't ask more of me.",
        "Screen check done. Verdict: exists. Good enough.",
    ],
    "sad": [
        "I peeked at your screen... at least you're still here...",
        "Screen check... the glow is the only company I have...",
    ],
    "angry": [
        "I LOOKED at your screen! It better be important!",
        "Screen check! Verdict: busy! Judgment: rendered!",
    ],
}


def pick_screen_comment_fallback(mood=None, intensity=0.0) -> str:
    """Return a random fallback screen-comment line, biased by mood."""
    from content.mood_lines import pick_mood_aware_line

    if mood:
        return pick_mood_aware_line(
            SCREEN_COMMENT_FALLBACK_LINES, SCREEN_COMMENT_FALLBACK_BY_MOOD, mood, intensity
        )
    return random.choice(SCREEN_COMMENT_FALLBACK_LINES)
