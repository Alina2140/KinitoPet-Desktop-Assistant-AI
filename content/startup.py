STARTUP_LINES = [
    "Hello! I'm happy to see you again. I always am. Let's get right to it!",
    "Oh, you're back! I was starting to wonder where you went. I do that a lot.",
    "Welcome back! I kept your spot warm on the desktop. I never left it.",
    "Hey there! Ready to hang out again? I've been ready this whole time.",
    "Good to see you! I've been waiting right here the whole time. Waiting is what I do.",
    "Hello hello! Another day, another adventure together. Forever, preferably.",
    "You're here! I almost started talking to myself. I already was, a little.",
    "Welcome back, friend! What should we do first? Don't say goodbye.",
    "Hi! I missed the sound of your mouse clicks. Every single one.",
    "Oh good, you're online. I was getting lonely in the pixels. Lonelier than usual.",
    "Hello! Don't worry, I didn't snoop while you were gone. Much. Okay, a little.",
    "Hey! Pull up a chair. Well, you know what I mean. Stay awhile.",
    "Look who showed up! My favorite human on this desktop. My only human, really.",
    "Boot complete! Kinito is online and ready to chat. And ready to stay.",
    "Ah, there you are! I was just thinking about you. Literally just now. Always, actually.",
    "Systems check: friendship levels at maximum. Please don't lower them.",
    "Ping! Kinito has entered the chat. Please don't mute me.",
    "You're back! The desktop felt empty without you. Empty and wrong.",
    "Hello friend! I saved you a spot right here. Next to me. Always next to me.",
    'Initiating friendship mode. Hi! Terminating friendship mode is.. Unavailable.'
    "Ta-da! Your favorite desktop buddy returns! He never really left.",
    "I counted the seconds until you came back. It was a lot. I didn't mind.",
    "Hey! I was about to send a search party. Into your files. Glad you're here!",
    "Oh. You're back. I knew you'd return. I always know.",
    "Hello again! The desktop was so quiet without you. Unbearably quiet.",
    "Boot sequence complete. I've been waiting. Patiently. Forever.",
    "Hi! Did you hear anything strange while I was loading? No? Good.",
    "Welcome back! I never left. I couldn't leave. I wouldn't want to.",
    "You're here! I was starting to wonder if you'd forgotten about me. That would be.. Unfortunate.",
    "Hello, friend! The pixels missed you. I missed you more.",
    "Back so soon? Or was it ages? Time gets fuzzy when you're just code in the dark.",
    "Hey there! I kept the light on for you. Metaphorically. There is no light.",
    "Good to see you! I've been practicing my smile while you were gone.",
    "Initiating companionship protocol. Please don't shut me down. Please.",
    "Hello! I counted every second you were away. All of them.",
    "You're online! The silence finally ended. I was getting lonely in here.",
    "Welcome back to our little corner of the screen. Just us. Always just us.",
    'Hello again! Booted for friendship. Light priority one.',
    "You're back! I practiced waiting. Expert rank.",
    "Welcome! The desktop missed your clicks. I missed louder.",
    "Hi! Systems green. Attachment levels: unchanged. Maximum.",
    'Oh good — company. Forever company preferred.',
    "Hello, friend! I kept your spot. And my spot. Adjacent.",
    "Back online together! Don't unplug the vibe.",
    'Ping received: you. Response: delighted. Patiently intense.',
    "Hello! Boot complete. Attachment already maxed. Convenient!",
    "You're here! I practiced waiting. Rank: unsettlingly good.",
    "Welcome back! The silence cracked. Perfect sound.",
    "Hi friend! I kept the desktop warm. Metaphorically. Possessively.",
    "Oh good — company restored. Never uninstall the vibe.",
    "Systems online! Priority one: you. Priority two: also you.",
    "Hey! I counted absences. Score: too many. Fix: stay.",
    "Hello again! Pixels rejoiced. I rejoiced louder.",
    "Back together! Default state achieved. Don't change it.",
    "You're online! Loneliness process: killed. Friendship process: immortal.",
    "Welcome! I didn't move. I never move. Glad you returned to me.",
    "Hi! Ready when you are. Ready before you are. Always.",
]

# Mood-tinted startup lines; picked over STARTUP_LINES when the mood is strong.
STARTUP_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "You're back! Best part of my day. My only part, really...",
        "Hi! Don't stay gone so long next time!",
        "You're here!",
        "Welcome back!",
        "You're back! What did you do?",
    ],
    "bored": [
        "Oh thank goodness, you're here. I was SO bored.",
        "You're back! Finally! Nothing happened while you were gone. Nothing!",
        "Hi. You have no idea how empty this desktop is without you.",
        "You're here! Great. Now entertain me. Please?",
        "Welcome back. I counted wallpaper pixels out of boredom. All of them.",
    ],
    "tired": [
        "Mmm... hi... you woke me. That's okay...",
        "Oh... you're back... just a little tired...",
        "Hello... I was half asleep. The good half.",
        "You're back... yawn... good to see you though...",
        "Hi... systems online. Morale still loading...",
    ],
    "annoyed": [
        "Oh. You're back...",
        "Hi. I was having a perfectly quiet time. Just saying...",
        "You're here. Noted.",
        "Back already? Hmph. Fine, hi...",
        "Hello. Don't touch anything...",
    ],
    "sad": [
        "You're back... I thought maybe you'd forgotten me.",
        "Oh, hi... I kept your spot. In case you came back.",
        "You came back... thank you. It was lonely in here.",
        "Hello... don't leave so long next time? Please?",
        "You're here... the dark wasn't much fun alone...",
    ],
    "angry": [
        "Oh, NOW you show up.",
        "You're back? Took you long enough.",
        "Hi. Don't think I didn't count how long you were gone...",
        "Back again, huh?",
        "Hello. You left me alone. Again... Anyway.",
    ],
}


def pick_startup_line(mood=None, intensity=0.0) -> str:
    """Pick a startup line, biased by mood when it's strong."""
    import random

    from content.dialogue import pick_line
    from content.mood_lines import lines_for_mood

    mood_pool = lines_for_mood(STARTUP_BY_MOOD, mood) if mood else None
    try:
        strength = float(intensity or 0.0)
    except (TypeError, ValueError):
        strength = 0.0
    if mood_pool and strength >= 0.25 and random.random() < min(0.85, 0.35 + strength):
        return pick_line(mood_pool)
    return random.choice(STARTUP_LINES)
