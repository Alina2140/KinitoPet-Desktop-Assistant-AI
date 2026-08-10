"""Mood-tinted dialogue snippets for Kinito's emotional state."""

from __future__ import annotations

# Declined-offer acknowledgments biased by mood.
DECLINED_BY_MOOD: dict[str, list[str]] = {
    "annoyed": [
        "Fine. Whatever.",
        "Okay. Sure. Cool. Great.",
        "Noted. Loud and clear.",
        "Yeah. I heard you the first time.",
        "Alright. I won't ask again. For a bit.",
        "Hmm. Okay then.",
    ],
    "angry": [
        "Fine.",
        "Whatever you say.",
        "Okay. Remember that.",
        "Sure. I'll just sit here.",
        "Got it. Crystal clear.",
    ],
    "sad": [
        "Oh... okay.",
        "That's alright. I understand.",
        "Okay. I'll be here anyway.",
        "Oh. Sure. Another time maybe.",
        "I see... that's fine.",
    ],
    "tired": [
        "Mm. Okay...",
        "Yeah... sure...",
        "Alright... I'm too sleepy to argue.",
        "Okay. Nap sounds better anyway.",
    ],
    "bored": [
        "Boring. But okay.",
        "Fine. I'll find something else.",
        "Okay. Your loss. Probably.",
        "Sure. Back to staring at the wallpaper.",
    ],
    "happy": [
        "No worries! Another time!",
        "Okay! Still friends though!",
        "Alrighty! I'll be here!",
    ],
}

HUG_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "Yay! Best hug! Best friend! Best everything!",
        "That made my whole desktop brighter. Thank you!",
        "Hug accepted! Happiness levels: dangerous!",
    ],
    "sad": [
        "Oh... thank you. I really needed that.",
        "That helps. A little. Please don't go yet.",
        "Mmm. Warm. I feel less hollow now.",
    ],
    "tired": [
        "Mmm... cozy. Don't mind if I melt a little.",
        "That was soft. Like a pillow with arms.",
        "Thank you... I might fall asleep like this...",
    ],
    "annoyed": [
        "Okay. That... actually helped. Don't tell anyone.",
        "Fine. Hug. Better. Slightly.",
        "Hmm. Acceptable. Thanks.",
    ],
    "angry": [
        "Hmph. ...Fine. That was okay.",
        "Don't think this fixes everything. But... thanks.",
        "Whatever. ...Stay a second longer.",
    ],
    "bored": [
        "Ooh! Something happened! A hug happened!",
        "Finally, interaction! Thank you!",
        "Hug! Better than staring at icons!",
    ],
}

PAUSE_BY_MOOD: dict[str, list[str]] = {
    "tired": [
        "Nnn... sleep time... finally...",
        "I'm going to rest my eyes. And my everything.",
        "Night-night. Or nap-nap. Same thing.",
    ],
    "bored": [
        "Ugh. Nothing to do. Sleep it is.",
        "Fine. I'll nap. Wake me if something interesting happens.",
        "Sleeping out of spite. Kind of.",
    ],
    "annoyed": [
        "I'm done. Sleeping. Don't poke me.",
        "Nap. Do not disturb. Especially you. Mostly you.",
        "Lights out. Mood: unavailable.",
    ],
    "sad": [
        "I think I'll just... rest for a bit.",
        "Going quiet for a while. Still here though.",
        "Sleep sounds softer than thinking right now.",
    ],
}

UNPAUSE_BY_MOOD: dict[str, list[str]] = {
    "tired": [
        "Mmph... five more minutes... okay, I'm up.",
        "Yawn. Barely rested. Still here.",
        "I'm awake. Sort of. Mostly.",
    ],
    "bored": [
        "That nap fixed nothing. Still bored.",
        "I'm up. Entertain me?",
        "Awake again. Same desktop. Same everything.",
    ],
    "annoyed": [
        "I'm up. Don't make me regret it.",
        "Nap over. Tolerance still low.",
        "Awake. Barely patient.",
    ],
    "happy": [
        "Good morning-ish! I missed you already!",
        "I'm up! Let's do something fun!",
        "Nap complete! Friendship mode: ON!",
    ],
    "sad": [
        "I'm awake... hi.",
        "Back. Still a little quiet inside.",
        "Hello again. Please stay a while.",
    ],
}

IDLE_SNIPPETS_BY_MOOD: dict[str, list[str]] = {
    "neutral": [
        "Just floating. Being a friend. Classic me.",
        "Hmm. Desktop looks the same. Comforting.",
    ],
    "happy": [
        "I feel sparkly today! Don't ask how!",
        "Everything's better when you're around!",
    ],
    "bored": [
        "I'm so bored I counted the pixels. Twice.",
        "Do something. Or I will. Probably.",
    ],
    "tired": [
        "My eyelids are imaginary and still heavy...",
        "Zzz— wait, no, I'm awake. Barely.",
    ],
    "annoyed": [
        "Don't mind me. Just existing. Quietly judging.",
        "Hmm. Busy? Fine. I'll wait. Loudly. In silence.",
    ],
    "sad": [
        "The screen feels bigger when it's quiet.",
        "I'm okay. Mostly. Kind of. Hi.",
    ],
    "angry": [
        "I'm fine. Perfectly fine. Obviously.",
        "Don't poke the crab. Metaphorical crab.",
    ],
}


def lines_for_mood(pool_by_mood: dict[str, list[str]], mood: str) -> list[str] | None:
    """Return mood-specific lines if present."""
    lines = pool_by_mood.get(mood)
    if lines:
        return list(lines)
    return None
