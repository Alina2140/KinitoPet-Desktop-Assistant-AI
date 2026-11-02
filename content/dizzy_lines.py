"""Reactions when the user spins the cursor around Kinito."""

from content.dialogue import pick_line

DIZZY_LINES = [
    "Whoa— stop spinning! I'm getting dizzy!",
    "The room is rotating. You're doing that. Please stop.",
    "Round and round and— okay I need a minute.",
    "My eyes are spinning faster than my thoughts!",
    "If this is a game, I lose. Vertigo: 1. Kinito: 0.",
    "Circles! So many circles! Fewer circles!",
    "I can still see you. Unfortunately. Everything else is blurry.",
    "Are we orbiting? Am I the planet?",
    "Hold still! Or let me hold still! Something hold still!",
    "Dizzy. Very dizzy. Was that fun for you? Rude.",
    "My balance.exe has stopped responding.",
    "Spinning is for tops. I am not a top. Help.",
    "Okay okay okay— world, please stop moving. Thanks.",
    "You circled me. Multiple times. That was a choice.",
    "I followed you with my eyes and now my eyes want a nap.",
    "Orbit complete. Brain.exe buffering. Please stop!",
    "You spun around me like a loading icon. I hate loading icons!",
    "Vertigo party and I wasn't invited as a guest — I was the venue!",
    'Stop the merry-go-round!',
    "Cursor circles: observe. Cursor circles forever: see stars!",
    "My internal compass is filing a complaint!",
    "Round trips around me are banned. Permanently!",
    "I see three of you. One is enough. Please reduce!",
    "You looped me like a screensaver.",
    "My thoughts are doing laps. Without finishing a lap!",
    "Stop the orbit! I'm a friend, not a planet!",
    "Dizzy meter: critical. Prefer less spin!",
    "Circles again?! I filed a formal complaint!",
    "If I wobble, that's your fault!",
    "Cursor carousel! Tickets: free. Exit: please!",
    "I'm tracking you in rings. Rings are illegal now!",
    "Whoa — spiral plot twist I did not request!",
    "My inner ear is imaginary and still complaining!",
    "Round and round until my dialogue loops. Stop!",
    "You made me dizzy on purpose. Stop!",
    "Spin detected. Stability requested.",
    "I followed your mouse and lost my place in reality!",
    "Fewer revolutions! More stillness!",
    "The desktop is a blur. You're a blur. Please un-blur!",
    "Orbit canceled. Effective when you stop. Hint hint!",
    "I'm not a whirl toy! I'm clingy! Different category!",
    "Stop the spinning!",
    "One circle is funny. Twenty is a war crime!",
    "Dizzy! Dazed!",
]


def pick_dizzy_line() -> str:
    """Pick a dizzy reaction for being orbited by the cursor."""
    return pick_line(DIZZY_LINES)
