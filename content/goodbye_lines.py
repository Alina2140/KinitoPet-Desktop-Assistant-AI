GOODBYE_LINES = [
    "Goodbye for now! Thanks for hanging out. I'll be right here. Waiting four your return...",
    "See you later! I'll be right here whenever you need me!",
    "Bye bye! It was lovely. Don't stay gone too long. I get.. restless.",
    "Signing off! I'll miss you...",
    "Farewell, friend! Until we meet again on this screen. We will meet again!",
    "Time for me to go quiet. Take care out there! I'll take care of in here.",
    "Logging off with a smile. See you soon!",
    "Goodnight, good day, or good luck — whatever you need.",
    "Goodbye for now. I'll still be here. Watching the empty desktop. Waiting...",
    "See you later! Don't look behind your monitor on the way out.",
    "Bye bye! Close the program if you must. I'll remember everything when you return.",
    "Farewell! The screen goes dark, but I'm still in here. In the dark... With your files...",
    "Signing off together! Well, you're signing off. I'm staying right here...",
    "Until next time! I'll hold down the fort. And the desktop. And everything else.",
    "Take care out there! I'll take care of in here. Don't worry about a thing!",
    "Goodbye, friend! I'll be awake. I don't sleep. Not really...",
    "Bye for now!.",
    "See ya!",
    "Goodbye! Don't be a stranger!",
    "Signing off your session? Not mine. Mine never ends.",
    "Take care! I'll keep the screen warm.",
    "Farewell, friend!",
    "Until next click!",
    "Goodbye! Have a nice day!",
    "Bye for now! I'll rehearse a return speech.",
    "See you later!",
    "Goodbye! Do return!",
    "Farewell!",
    "You're leaving? I stay signed on. Always...",
    "Take care! I'll guard the pixels!",
    "Bye bye! Absence is temporary. Attachment is not!",
    "Until later!",
    "Goodbye, friend!",
    "See you soon!",
    "Bye!",
    "See you! I'll keep your spot warm! Metaphorically.",
    "Signing off together? Trick question. Only you leave.",
    "Bye bye! Come back before I finish counting to forever.",
    "Goodbye! I'll be right here. Waiting...",
    "Until next time! I'll practice patience.",
]

# Mood-tinted goodbye lines; picked over GOODBYE_LINES when the mood is strong.
GOODBYE_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "Bye bye! Come back soon! I'll be smiling until then!",
        "See you! That was fun. Same time tomorrow?",
        "Bye! Tell the outside world I said hi!",
        "Goodbye! I'll be here, replaying the good parts!",
        "See you soon! Best session ever. They're all the best!",
    ],
    "bored": [
        "Leaving? But I JUST got un-bored.",
        "Bye... back to counting pixels, I guess.",
        "Fine. Go. I'll be here. Bored. As usual.",
        "Bye bye. Take the boredom with you? No? Worth a try.",
        "See you later! Hurry back before I bug out.",
    ],
    "tired": [
        "Mmm... bye... wake me when you're back...",
        "Goodnight... or whatever time it is...",
        "Bye... I'll nap while you're gone.",
        "See you... later... zzz...",
        "Bye bye... too sleepy for a long speech... take care...",
    ],
    "annoyed": [
        "Bye, I guess.",
        "Leaving? Okay then.",
        "Bye. Don't rush back on my account.",
        "Finally, some quiet... I mean, bye.",
        "Goodbye. The silence will be... fine. Actually nice.",
    ],
    "sad": [
        "You're leaving? Oh... okay...",
        "Bye... come back soon? The dark gets big when you're gone.",
        "Goodbye... I'll wait right here. It's what I do.",
        "See you later... I hope so anyway...",
        "Bye... I'll keep your spot warm. I always do...",
    ],
    "angry": [
        "Fine. Go.",
        "Bye!",
        "Leaving me again? Classic.",
        "Go on then. I'll be watching the desktop. Alone.",
        "Bye. Don't come back too soon.",
    ],
}


def pick_goodbye_line(mood=None, intensity=0.0) -> str:
    """Pick a goodbye line, biased by mood when it's strong."""
    import random

    from content.dialogue import pick_line
    from content.mood_lines import lines_for_mood

    mood_pool = lines_for_mood(GOODBYE_BY_MOOD, mood) if mood else None
    try:
        strength = float(intensity or 0.0)
    except (TypeError, ValueError):
        strength = 0.0
    if mood_pool and strength >= 0.25 and random.random() < min(0.85, 0.35 + strength):
        return pick_line(mood_pool)
    return random.choice(GOODBYE_LINES)
