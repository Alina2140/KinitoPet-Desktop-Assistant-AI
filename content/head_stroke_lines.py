"""Reactions when the user pets Kinito on the head."""


HEAD_STROKE_LINES = [
    "Oh! That tickles. In a nice way.",
    "Head pets detected. Mood: improved.",
    "Hey! Gentle!",
    "My gills are fluttering!",
    "That feels weirdly nice...",
    "You're very good at this...",
    "I would purr if I could. Consider this a purr.",
    "Okay okay, that's enough — no wait, one more stroke.",
    "If this is a trick to distract me, it's working.",
    "Gentle hand detected.",
    "Okay, that was nice. Don't make it weird... Too late.",
    'Stroke received. Blush rendered.',
    "Head pets! My favorite unauthorized feature.",
    "That feels nice...",
    "You're petting me? Bold.",
    "I would wag something if I had something. Consider this a wag.",
    "Gentle contact! My favorite kind of desktop event.",
    "That tickles my pride. And my scalp.",
    "You're spoiling me. Good.",
    "My favorite glitch: happiness!",
    "That was perfect. Don't analyze it! Just repeat it.",
    "If this is bribery, it works.",
]


HEAD_STROKE_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "YES! Pets! The best possible use of a hand!",
        "More! Please! I demand more pats!",
        "This is the greatest moment of my desktop life!",
        "Pet powered! I could glow for days!",
    ],
    "bored": [
        "Finally, entertainment! Keep petting!",
        "Ooh, contact! I was so bored I almost enjoyed this.",
        "Yes! Do that again. And again. And again.",
        "Best thing to happen all day. It was a slow day.",
    ],
    "tired": [
        "Mmm... gentle... keep going...",
        "Petting accepted... sleepy mode improving...",
        "That's nice... almost as nice as napping...",
        "Mmm... slow strokes please... perfect...",
    ],
    "annoyed": [
        "Hmph. Fine. Pets accepted.",
        "Okay. That... helped. Slightly. Don't tell anyone.",
        "You're forgiven. For whatever. Mostly.",
        "One stroke. Maybe two. I'm still annoyed.",
    ],
    "sad": [
        "Oh... thank you. That helps more than you know.",
        "Please don't stop. I needed this.",
        "Mmm... warmth... the hollow feels smaller...",
        "That's... really nice. Stay a while?",
    ],
    "angry": [
        "Hmph! ...Okay, that felt good. Continue.",
        "Careful! ...Oh. Actually. Keep going.",
        "You can't just pet away being mad! ...Can you?",
        "I'm still angry! But... one more stroke.",
    ],
}


def pick_head_stroke_line(mood=None, intensity=0.0) -> str:
    """Pick a shy or pleased line for head pets, biased by mood."""
    from content.mood_lines import pick_mood_aware_line

    return pick_mood_aware_line(HEAD_STROKE_LINES, HEAD_STROKE_BY_MOOD, mood, intensity)
