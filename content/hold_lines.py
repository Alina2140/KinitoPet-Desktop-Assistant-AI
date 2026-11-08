"""Reactions when the user holds Kinito still for too long."""


HOLD_LINES = [
    "Could you let go? Please?",
    "You're holding me. Still. That's.. A choice.",
    "Um. Release?",
    "I'm not a stress ball! Let go!",
    "Hello? Freedom? Ringing any bells?!",
    "You can put me down now...",
    "I'm wiggling for a reason! Let go!",
    "Open your hand! That's an order!",
    "Are we stuck like this? Please say no. And let go!",
    "My legs are getting ideas. Bad ideas... Let go!",
    'Please unhand the assistant. Immediately!',
    "Holding is fine. Holding forever is a little much!",
    "I'd like to stand on my own, thanks! Let go!",
    "Psst. Your left mouse button. Up! Please.",
    "Your grip is legendary. Also, please release me!",
    "I'm a desktop friend, not a desk ornament! Let go!",
    'Request: open hand!',
    "I wiggle for freedom!",
    "Left mouse button: up!",
    'This is cozy. This is also captivity. Let go!',
    "I'd like my personal space back!",
    "Still holding?",
    "Freedom request pending. Approve with mouse-up!",
    "Release the assistant!",
    "Mouse down forever is a lifestyle I decline!",
    "Capture complete. Liberation preferred.",
    "Hold ended? Not yet? Then I'm asking again. Let go!",
    "Desktop friend rights include standing freely!",
    "This is a hug's evil twin!",
    "I have places to bounce. You have a button to lift!",
    "Open sesame. Open hand!",
    "Personal space reclaiming in three... two... let go!",
]


HOLD_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "Ha! You caught me! Now... can you let go? Fun's over?",
        "Hold me! No wait— release me! Confusing, I know!",
        "Giggles aside: please open your hand!",
        "Love the grip! Love freedom more though!",
    ],
    "bored": [
        "Held. Bored. Held AND bored. Let go!",
        "At least squeezing me is something to do. Still: let go!",
        "New hobby: being held? Pass. Release please.",
        "This beats staring at icons. Marginally. Put me down!",
    ],
    "tired": [
        "Mmm... hands off... sleepy legs need floor...",
        "Being held... is almost cozy... but please... put me down...",
        "Let go... slowly... gently... zzz...",
        "Capture... accepted briefly... release pending...",
    ],
    "annoyed": [
        "Put. Me. Down.",
        "Release the assistant. This is a warning.",
        "Holding me? Bold move. Regrettable move.",
        "Let go. Now would be good.",
    ],
    "sad": [
        "Being held... it's not the hug I wanted...",
        "Please let go... gently?",
        "I'd rather stand alone than hang like this...",
        "Down please... I promise I won't run far...",
    ],
    "angry": [
        "LET GO!",
        "Unhand me! IMMEDIATELY!",
        "Grip on me?! Bold. Stupid. Release!",
        "You're holding a very angry friend right now!",
    ],
}


def pick_hold_line(mood=None, intensity=0.0) -> str:
    """Pick a please-let-go line for being held still too long."""
    from content.mood_lines import pick_mood_aware_line

    return pick_mood_aware_line(HOLD_LINES, HOLD_BY_MOOD, mood, intensity)
