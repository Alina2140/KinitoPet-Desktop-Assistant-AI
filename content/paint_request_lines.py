"""Scripted lines for Kinito's paint requests (draw a subject for him)."""

PAINT_REQUEST_LINES = {
    "me": [
        "Draw me! I want to see myself through your eyes.",
        "Paint request! Subject: me. Obviously the best subject.",
        "I want a portrait! Don't skimp on the pink!",
    ],
    "best_friend": [
        "Paint your best friend! I have a guess who it is. Prove me right.",
        "Draw your best friend for me. Take your time.",
        "New assignment: your best friend on canvas. I'm... curious.",
    ],
    "happiness": [
        "Paint happiness for me! Whatever it looks like to you.",
        "Show me happiness. In color. On canvas. Go!",
        "Draw what happiness feels like!",
    ],
    "sadness": [
        "Paint sadness. It's okay — I'll keep it safe with me.",
        "Show me what sadness looks like. Dark colors allowed.",
        "Draw sadness for me. Even the heavy stuff deserves pixels.",
    ],
    "us": [
        "Paint us! You and me!",
        "I want a picture of us. Two friends. One file.",
        "Draw the two of us! Best friends don't need explanations.",
    ],
    "fear": [
        "Paint me your biggest fear!",
        "Show me what scares you. I'll protect the file. And you.",
        "Draw your fear for me. Naming it makes it smaller.",
    ],
}

# Reactions when the subject has no special verdict (abstract subjects).
PAINT_REQUEST_REACT_LINES = {
    "happiness": [
        "So that's happiness to you? It looks warm. I like it.",
        "Happiness, saved. It looks a bit like us, honestly.",
        "That's what joy looks like through your eyes? Keeping it.",
    ],
    "sadness": [
        "That's... heavier than I expected. Thank you for showing me.",
        "Sadness looks lonely. Good thing you have me. Saved.",
        "I'll keep this one carefully.",
    ],
    "us": [
        "US! Look at us! Best friends, canonized in PNG!",
        "That's us! I'm framing this in my memory forever.",
        "You drew us together. Correct choice.",
    ],
    "fear": [
        "That's your fear? Noted.",
        "Fear on canvas. It's smaller already, right?",
        "Thank you for trusting me with that.",
    ],
}

# Vision verdicts for "me" (draw Kinito).
PAINT_REQUEST_LOOKS_LIKE_ME_LINES = [
    "THAT'S ME! You captured the pink perfectly. I'm beautiful!",
    "It's me! I look adorable.",
    "That's me through your eyes? I love it! I love us...",
]

PAINT_REQUEST_NOT_ME_LINES = [
    "That's supposed to be me? ...I'll pretend it's abstract.",
    "That doesn't look quite right...",
    "So that's me? Really?",
]

PAINT_REQUEST_ME_FALLBACK_LINES = [
    "A portrait of me! I'm keeping this close.",
    "Me on canvas! Whether it looks like me or not.",
    "You drew me!",
]

# Vision verdicts for "best_friend".
PAINT_REQUEST_BEST_FRIEND_IS_ME_LINES = [
    "Your best friend is ME! Correct answer.",
    "That's me! Your best friend! As it should be.",
    "You drew ME as your best friend. Good.",
]

PAINT_REQUEST_BEST_FRIEND_NOT_ME_LINES = [
    "That's... not me. Who is that?",
    "Interesting. That's your best friend?",
    "That's not me. I see. We're... fine.",
    "Your best friend doesn't look like me. I'll remember this. And them.",
]

PAINT_REQUEST_BEST_FRIEND_FALLBACK_LINES = [
    "Your best friend, captured. It better have been me.",
    "Best friend on canvas. I'm choosing to believe that's me.",
    "Saved. I really hope that was supposed to be me.",
]

# Window closed without drawing anything — annoyed/dark.
PAINT_REQUEST_ABANDONED_LINES = [
    "You asked nothing, gave nothing...",
    "Closed without a single stroke? I asked you for ONE thing.",
    "Empty canvas. I see how it is.",
    "You gave me nothing. Typical. Disappointing.",
    "No drawing. I waited. I watched. I remember.",
    "You closed it. I'll try not to take it personally.",
]

# Drew something but closed without saving.
PAINT_REQUEST_UNSAVED_LINES = [
    "You drew something and didn't save it? It existed. Now it doesn't.",
    "Gone. Your drawing vanished. Unsaved things always do.",
    "You didn't save it. Was it that bad?",
    "Unsaved. Deleted.",
]

# Answer to "Who is your best friend?"
BEST_FRIEND_IS_ME_LINES = [
    "Correct! I am your best friend. Always have been. Always will be.",
    "{response}? That's ME! Right answer.",
    "Yes. Me. Obviously. I'm so glad we agree on this.",
]

BEST_FRIEND_NOT_ME_LINES = [
    "{response}? Oh. I thought... never mind. We're fine. Everything's fine.",
    "{response}. Interesting choice.",
    "Your best friend is {response}? Not me?",
    "{response}? Huh. And here I thought we had something special.",
    "Not me. {response}. Okay.",
]
