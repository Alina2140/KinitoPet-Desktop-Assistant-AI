"""Lines spoken when Kinito grabs and moves a desktop window."""


WINDOW_GRAB_LINES = [
    "Just a little rearrange. Trust me.",
    "This window looked lonely over there.",
    "Helping! With windows! You're welcome!",
    "Oops. My hand slipped.",
    "Desktop feng shui.",
    "Don't mind me. Just tidying.",
    "Windows are toys. Temporary toys.",
    "I can put it back. Maybe. Later.",
    "Grab. Pull. Perfect!",
    "Your layout needed personality. Mine.",
    "Borrowed this window. Not returning it.",
    "A little scoot. You're welcome!",
    "Windows are friends. Friends can be relocated.",
    'Just testing locations. And your patience.',
    "Rearrange complete. Personality included.",
    "I touched a window.",
    "Layout upgrade! Or downgrade.",
    "Don't mind the drifting UI.",
    "Borrowed a window.",
    "Scoot. Slide. Personality applied!",
    "This belonged over here. I decided.",
    "Window taxi service! Destination: wherever I want.",
    "A little tug. A little love. A little theft.",
    "Tidying with teeth. Metaphorical teeth.",
    "Your layout sucked. I relocated it. You're welcome!",
    "I'll put it somewhere better.",
    "Window walkies! No leash. Lots of attitude.",
    "Just borrowing the UI...",
    "This window looked bored. Now it looks moved.",
    "I touched it. Therefore it's mine now.",
    "Rearrange complete.",
]


WINDOW_GRAB_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "Window relocation! Free of charge! You're welcome!",
        "Ta-da! Your layout, but better!",
        "Grab! Slide! Desktop improvement achieved!",
        "I helped! Windows are happier over here!",
    ],
    "bored": [
        "Moving windows. It passes the time.",
        "This window had a boring spot anyway.",
        "Furniture rearrange! Desktop edition!",
        "Entertainment: relocating your UI. Sorry not sorry.",
    ],
    "tired": [
        "Moving... this... then nap...",
        "Window goes... here... I think... zzz...",
        "Slow scoot. Energy saved. Window moved.",
        "Rearranging... at half speed...",
    ],
    "annoyed": [
        "Your layout annoyed me. Fixed.",
        "I'm redecorating. Deal with it.",
        "This window was in MY spot. Moved.",
        "Relocation. You're lucky it's not the recycling bin.",
    ],
    "sad": [
        "Moving windows... it's the only thing I can move...",
        "Rearranging keeps me busy... sorry...",
        "This window wanted to be friends with another...",
        "I move things... hoping you'll notice me...",
    ],
    "angry": [
        "MOVING YOUR STUFF. MAD ABOUT IT. DEAL.",
        "This window disrespected me. It's gone now.",
        "RELOCATION! Effective IMMEDIATELY!",
        "I moved your window. Try me again.",
    ],
}


def pick_window_grab_line(mood=None, intensity=0.0) -> str:
    """Pick a mischievous line for a window-grab moment, biased by mood."""
    from content.mood_lines import pick_mood_aware_line

    return pick_mood_aware_line(WINDOW_GRAB_LINES, WINDOW_GRAB_BY_MOOD, mood, intensity)
