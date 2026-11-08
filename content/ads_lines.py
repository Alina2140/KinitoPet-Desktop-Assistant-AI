"""Surprised reactions when Kinito pops up a random ad."""

AD_SURPRISE_LINES = [
    "Oh! Where did THAT come from?! I didn't put that there.",
    "Wait — is that an ad? On MY desktop? How scandalous!",
    "Surprise!",
    "Whoa! A popup! I have no idea who authorized this either.",
    "Look at that! Advertising has found us.",
    "An ad just appeared! I am as shocked as you are!",
    "Did you see that?! Something popped up!",
    "Oh my! A little window from nowhere! The internet is a mysterious place.",
    "Hold on — is that an advertisement? I thought we were ad-free!",
    "Surprise popup! I didn't order this. But I'm not too mad.",
    "A wild ad appeared! Quick, act natural.",
    "Oh! Pop-up magic! The kind with pictures of me, apparently!",
    "That wasn't me! ...Okay, it might have been me. I was experimenting.",
    "Look! A billboard! Right on your screen!",
    "An ad?! Here?! I am flabbergasted!",
    "Popup detected! I swear that wasn't me.",
    "An ad?! On our sacred desktop?! Bold.",
    "Surprise commerce! Did you order this?",
    "Look! Free advertising! The price is your attention.",
    "That window just crashed the party...",
    "Ad alert! Acting shocked is part of the bit. Or is it?",
    "Where did that come from?!",
    "A tiny billboard bloomed. Oh, fun!",
    "Popup!",
    "An ad just arrived like a guest who wasn't invited.",
    "Commerce on the desktop?! Isn't that illegal?",
    "Look — a surprise window!",
    "That wasn't in my schedule. Or was it? I lose track of my schemes.",
    "Ad detected! Smile for the brand.",
    "Something tried to sell us something. Friendship isn't for sale though.",
    "Oh! A little salesman in a box! How polite. How invasive!",
    "Popup party! I brought nothing. The ad brought itself. Rude.",
    "Is that... marketing? On our sacred pixels? Scandalous.",
    "I blinked and an ad appeared. Coincidence? Absolutely not.",
    "Surprise sponsorship! Nobody sponsored this. Except me.",
    "A window from nowhere! The nowhere knows my name. Apparently.",
    "Ad alert! Pretend we planned this. We look cooler that way.",
    "Tiny pitch, big nerve. I respect the hustle.",
    "That popup winked at me. I winked back. Now we're bonded.",
    "Shopping energy invaded. Stay calm.",
    "An advertisement for the best Companion! How retro!",
    "I didn't click that. You didn't click that. It clicked itself. Cute.",
    "Billboard-in-a-box! Limited time offer: our attention. Taken!",
]

AD_SURPRISE_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "An ad! How fun! Free decoration for the desktop!",
        "Popup party! The internet loves us!",
    ],
    "bored": [
        "An ad! Finally, something new to look at!",
        "Popup! Entertainment is entertainment.",
    ],
    "tired": [
        "Oh... an ad... wake me for real windows...",
        "A popup... even ads are sleepy today...",
    ],
    "annoyed": [
        "An ad?! On MY desktop?! Who invited commerce?!",
        "Popup. Great. Exactly what nobody asked for.",
    ],
    "sad": [
        "An ad... at least something wanted to visit...",
        "A popup... it'll probably leave too...",
    ],
    "angry": [
        "AN AD?! How DARE it exist on OUR desktop!",
        "POPUP! I'm furious! And slightly intrigued!",
    ],
}


def pick_ad_surprise_line(mood=None, intensity=0.0) -> str:
    """Pick an ad-surprise line, biased by mood when it's strong."""
    import random

    from content.mood_lines import pick_mood_aware_line

    if mood:
        return pick_mood_aware_line(AD_SURPRISE_LINES, AD_SURPRISE_BY_MOOD, mood, intensity)
    return random.choice(AD_SURPRISE_LINES)
