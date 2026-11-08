FANCY_LINES = [
    "Ladies, gentlemen, and everyone in between — welcome! I am Kinito the Magnificent! Please don't leave mid-show.",
    "Step right up, step right up! Prepare to be amazed by the greatest show on your desktop! Leaving is discouraged.",
    "For my first trick, I shall make your boredom vanish! Abracadabra! ...Did it work? Stay for the encore.",
    "Behold my hat! Behold my cane! Behold — me! The show has officially begun!",
    "Observe closely, for what you are about to witness cannot be unseen.",
    "I shall now pull a wonderful day out of thin air! There! It's in your calendar. You're welcome.",
    "Ta-da! The magnificent Kinito appears! Applause is optional but highly encouraged. Exiting is not.",
    "Welcome to the Desktop Grand Spectacular! Starring me. Supporting cast: you. Permanent cast: us.",
    "With a tip of my hat and a twirl of my cane, I declare this moment officially magical!",
    "Ladies and gentlemen, watch as I transform an ordinary screen into a stage of wonder! No refunds.",
    "For my next illusion, I will guess what you're thinking. You're thinking this is pretty cool!",
    "Presenting the one, the only, the unforgettable — Kinito the Showman! Take a bow, me. Stay seated, you.",
    "Is this your card? No? That's fine. I wasn't actually holding cards anyway. I was holding your attention.",
    "The Great Kinito shall now perform the legendary trick: making time fly while you work! Stay nearby.",
    "Gather round! I have a prophecy! Something interesting will happen today. I can feel it!",
    "Abracadabra, alakazam! Your desktop is now ten percent more enchanting. Results may vary.",
    "Thank you, thank you! You've been a wonderful audience. Please refrain from throwing tomatoes. Or closing me.",
    "I now invite a volunteer from the audience. Oh — you're already here. Perfect!",
    "And for the grand finale — I shall disappear! ...Eventually. When you shut me down. Please don't.",
    "The magician never reveals his secrets. But I will reveal this: you're doing great today!",
    "Hocus pocus, desktop focus! I channel the ancient magic of productivity into this very spot!",
    "Be amazed! Be astounded! Be slightly confused! All are valid reactions to my performance.",
    "I tip my hat to you, dear audience. Without you, I'd just be a very well-dressed assistant.",
    "And now, a round of applause for the real magic — you, showing up and staying. Bravo!",
    "Step into my parlor, dear audience! The show is free. The exit is... complicated.",
    "For my greatest illusion, I shall make your unease disappear! It didn't work? How odd.",
    "Behold! I pull not a rabbit, but your attention, from a hat of endless distraction!",
    "The curtain rises on a stage of ones and zeros. Applause echoes in an empty room.",
    "Ladies and gentlemen, what you see is real. What you don't see is also real.",
    "I vanish from sight but never from memory. A classic trick. Ask anyone who's tried to uninstall me.",
    "Watch closely! I will now saw your boredom in half. The boredom recovers. I do not.",
    "Presenting wonders from beyond the taskbar! Some wonders prefer to stay beyond.",
    "For my encore, I invite you to never leave. The crowd goes wild. The crowd is me.",
    "With a flourish of pixels — the show continues!",
    "Behold! A tip of the hat, a wink of the eye, a plea in the dark!",
    "For my next trick: making boredom disappear! Subject may reappear.",
    "Ladies, gentlemen, entities — feast your eyes on desktop magic!",
    "The spotlight finds you. Stay in it.",
    "Abracadabra! Your attention is now mine. Binding spell completed.",
    "Presenting wonders! Some are illusions. Some are me. Hard to tell.",
    "The cane twirls. The plot thickens.",
    "Encore energy! Remain seated! Leaving voids the magic!",
    "Behold — a flourish, a bow, a gentle emotional hostage situation!",
    "For my next wonder: your attention, permanently booked!",
    "The hat tips. The cane spins. The friendship clause activates!",
    "Spectacle time!",
    "I pull marvels from nowhere. Also from your free time.",
    "Ladies, gentlemen, entities — the show extends indefinitely!",
    "Watch as boredom flees! Watch as exits become theoretical!",
    "Grand illusion: making loneliness vanish.",
    "With pixels and polish — another act begins!",
    "Ta-da again! Repetition is showmanship.",
    "The spotlight refuses to dim. Remain dazzled!",
]

# Mood-tinted showman lines; picked over FANCY_LINES when the mood is strong.
FANCY_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "Ta-da! The show must go on — and I'm DELIGHTED about it!",
        "Behold! A magician in the best of moods! Wonders for everyone!",
        "For my next trick: doubling the fun! It's working already!",
        "Step right up! Today's performance is extra energetic!",
        "Encore! Encore! I haven't even started and I already love this crowd!",
    ],
    "bored": [
        "The Great Kinito performs... because the desktop was getting dull anyway.",
        "Behold! A show! It was either this or count the icons again.",
        "Step right up! I needed something to do. You're welcome.",
        "For my next act: making this boring afternoon disappear. Watch closely!",
        "A performance born of pure boredom. Applaud anyway!",
    ],
    "tired": [
        "Ta... da... the sleepy magician takes the stage...",
        "Behold... a wonder... performanced at half speed...",
        "For my next trick... staying awake through the whole act...",
        "Step right up... quietly though... it's a gentle show tonight...",
        "The show must go on... yawn... on...",
    ],
    "annoyed": [
        "A show. For you. You're welcome...",
        "Behold. Wonders. Try to pay attention this time.",
        "Step right up. Or don't. The show happens either way.",
        "For my next trick: performing despite the distractions. It's harder than it looks.",
        "The magnificent Kinito presents: the only magic you'll get today...",
    ],
    "sad": [
        "A show... just for you... please stay this time...",
        "Behold... wonders... they mean more when someone watches...",
        "The lonely magician performs... applause optional... company required...",
        "Step right up... don't leave before the finale... please...",
        "For my next trick: making the quiet feel a little less empty...",
    ],
    "angry": [
        "A show! Watch it. Now.",
        "Behold! Even fury deserves a stage!",
        "Step right up! Or ELSE the show starts without you. It already did.",
        "The Magnificent Kinito performs! Nobody leaves. NOBODY!",
        "For my next trick: turning this horrible mood into spectacle. Observe!",
    ],
}


def pick_fancy_line(mood=None, intensity=0.0) -> str:
    """Pick a showman line, biased by mood when it's strong."""
    import random

    from content.dialogue import pick_line
    from content.mood_lines import lines_for_mood

    mood_pool = lines_for_mood(FANCY_BY_MOOD, mood) if mood else None
    try:
        strength = float(intensity or 0.0)
    except (TypeError, ValueError):
        strength = 0.0
    if mood_pool and strength >= 0.25 and random.random() < min(0.85, 0.35 + strength):
        return pick_line(mood_pool)
    return random.choice(FANCY_LINES)
