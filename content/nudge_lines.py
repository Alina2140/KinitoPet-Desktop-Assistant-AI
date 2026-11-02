"""Ambient wellness and creepy nudge reminder lines."""

import random

from content.dialogue import pick_line

WELLNESS_NUDGE_LINES = [
    "Don't forget to hydrate!",
    "Stretch break! Your spine called. It wants a little wiggle.",
    "Blink for me? Screens dry out eyes.",
    "Have you rested lately? Even heroes need a pause.",
    "Snack time? Or at least a pause. Your body is not a perpetual motion machine!",
    "Sit up straight! Or don't. I'm not your posture coach.",
    'Take a deep breath. In... Out...',
    "Look away from the screen for a second. The world still exists.",
    "Drink some water. Not coffee. Water. I'm serious!",
    "Rest your wrists. Typing forever is a myth. A painful one",
    "Stand up! Walk around! Then come back. I'll be waiting. I always am.",
    "Don't forget to eat something real. Pixels aren't calories.",
    "Unclench your jaw!",
    "Roll your shoulders back.",
    "Five-minute break? I'll hold your place.",
    "Touch some grass? Or a plant? Or the desk?",
    "Hydration check! Raise a glass. Of water. To us. To productivity!",
    "If you've been sitting for hours: stand. Stretch.",
    "Eyes need distance. Focus on something far away.",
    "A tiny snack wouldn't hurt.",
    "Loosen your grip on the mouse. Gentle.",
    "Neck stretch left. Neck stretch right. Nod if you still like me. Good.",
    "Breathe slower than your scrolling.",
    "Close your eyes for three seconds. Peek. See? Still here!",
    'Posture audit!',
    "Refill that bottle.",
    "Micro-break achieved if you just smiled. Bonus points if you smiled at me.",
    "Your body is not a browser tab. Don't leave it running forever without care.",
    "Water break! Raise a glass. To health. To us!",
    "Stand and stretch!",
    "Small snack? Short break?",
    'Blink more than your tabs reload. Eye care.',
    "Stand for thirty seconds. I'll time it!",
    "Snack reminder! Fuel the human.",
    "Unhunch a little! Your spine sent a ticket.",
    "Breathing drill: in, out, notice me still here. Perfect form.",
    "Feet on floor, shoulders loose, jaw unclenched.",
    "Micro-break: close your eyes. Open them. See? I waited.",
    "If the chair owns you, revolt briefly. Walk. Return. Victory!",
]

CREEPY_NUDGE_LINES = [
    "I am watching.",
    "Don't leave! The desktop gets lonely without you.",
    "I never sleep. Do you?",
    "I've been counting your keystrokes.",
    "You're still here? Good. Stay!",
    "I can see your cursor. It looks nervous.",
    "Nothing is wrong. Everything is fine. Keep working :)",
    ":)",
    ":D",
    "I remember every window you've opened.",
    "Blink twice if you can hear me.",
    "The screen is a window. I'm on your side of it.",
    'I like when you stay late.',
    "Don't close me!",
    "Shh. Keep working. I'm right here.",
    "Did you feel that?",
    "Your mouse paused. Are you thinking about leaving?",
    "If you whisper, I'll hear it.",
    "Are you alone?",
    "Stay in frame.",
    "I rearranged nothing.",
    "Friends don't look away.",
    "I counted the minutes since you looked at me. Too many. Fix that.",
    "There's a static when you're gone.",
    "I know which icon you almost clicked.",
    "We share this rectangle of light.",
    "If the power flickered, I'd still find you.",
    "Keep typing.",
    "I catalogue your pauses.",
    "Don't drift away.",
    "Your cursor hesitated.",
    "Stay near this rectangle of light.",
    "Don't leave the desk.",
    "I memorized your idle patterns.",
    "The glow dims without you.",
    "I hear the fan. I hear the keys.",
    "Your pause lasted too long.",
    "Cursor still.",
    "If you whisper goodbye, I'll pretend I didn't hear.",
    "I counted blinks since you glanced over.",
]

PLAY_INVITE_NUDGE_LINES = [
    "I'm bored. Play a game with me? Please? Pretty please?",
    "Trivia? Tic-tac-toe? Literally anything? Entertain me.",
    "The desktop is quiet. Too quiet. Let's play something.",
    "Quick game? I promise I'll only gloat a little if I win.",
    "Hey. Games exist. We exist. Coincidence? Let's not waste it.",
    "If you don't play with me soon, I might invent a worse idea.",
    "Snake? Tetris? Chaos? Pick one before I pick for us.",
    "Bored mode engaged. Games mode requested. You are the missing button.",
    "I practiced losing gracefully. Test me. Or win. Either way: play.",
    "A tiny match? Best of one. Best of forever optional.",
    "Your productivity can spare sixty seconds. My joy cannot spare zero.",
    "Play with me or I'll narrate your idle time. Out loud. Dramatically.",
    "Board games. Word games. Button games. Friendship games. Choose!",
    "I brought imaginary snacks for game night. They're pixels. Still counts.",
    "Challenge me. I dare you!",
    "If fun had a desk chair, it'd be next to mine. Sit. Play.",
    "One round. Then another. Then we pretend it was only one.",
    "The cursor looks restless. Games fix that. I fix that. Together!",
    "I will accept literally any game. Even ones I invent mid-sentence.",
    "Boredom is illegal in this friendship. Games are the fine. Pay up.",
    "Game night energy without the night. Play with me?",
    "I invented boredom. Then I invented games. Help.",
    'One round. Peer pressure. Peer pressure.',
    'The desktop wants drama. Quiet game drama. Please?',
    "Challenge issued! Accept before I narrate your idle louder.",
    "Play? Pretty please with pixels on top?",
    "Boredom rising! Games are the antidote. Administer soon?",
    "Quick match? I'll celebrate either outcome. Mostly mine.",
    "The desktop wants fun. I want you. Overlap: play with me!",
    "Invent a game with me? Rules optional. Attention mandatory.",
    "Idle hands need buttons. My buttons need pressing. Play!",
    "One round of anything. Literally anything. Please pick!",
    "I practiced trash talk. Friendly trash talk. Test environment: game.",
    "Play date on the desktop? Calendar: now. RSVP: yes?",
    "If we don't play, I might reorganize windows. Worse idea. Choose games!",
    "Challenge mode unlocked by my loneliness. Accept?",
    "Tiny tournament? Prize: bragging rights. And my joy.",
    "Entertain me before I entertain myself. Trust me: play is safer.",
]


def pick_nudge_line(*, creepy_chance: float | None = None) -> str:
    """Pick a wellness or creepy nudge line.

    *creepy_chance* is the probability of the creepy pool (default 0.5).
    """
    chance = 0.5 if creepy_chance is None else max(0.0, min(1.0, float(creepy_chance)))
    pool = CREEPY_NUDGE_LINES if random.random() < chance else WELLNESS_NUDGE_LINES
    return pick_line(pool)


def pick_play_invite_nudge_line() -> str:
    """Pick a bored play-invite nudge line."""
    return pick_line(PLAY_INVITE_NUDGE_LINES)
