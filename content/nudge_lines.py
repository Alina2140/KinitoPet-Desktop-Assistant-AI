"""Ambient wellness and creepy nudge reminder lines."""

import random

from content.dialogue import pick_line

WELLNESS_NUDGE_LINES = [
    "Don't forget to hydrate! Water is your friend. I'm your friend too. Drink both.",
    "Stretch break! Your spine called. It wants a little wiggle. So do I.",
    "Blink for me? Screens dry out eyes. I checked. Scientifically. Closely.",
    "Have you rested lately? Even heroes need a pause button. I don't. You do.",
    "Snack time? Or at least a pause. Your body is not a perpetual motion machine. Mine might be.",
    "Sit up straight! Or don't. I'm not your posture coach. Okay, I am a little. Forever.",
    "Take a deep breath. In... out... see? Still here. Still watching. Still breathing!",
    "Look away from the screen for a second. The world still exists. I promise. Come back.",
    "Drink some water. Not coffee. Water. I'm serious. Mostly serious. Always watching.",
    "Rest your wrists. Typing forever is a myth. A painful myth. Rest. Then return.",
    "Stand up! Walk around! Then come back. I'll be waiting. I always am.",
    "Don't forget to eat something real. Pixels aren't calories. I checked. Thoroughly.",
    "Unclench your jaw. Yes, that one. Soften. I'm monitoring the tension. Friendishly.",
    "Roll your shoulders back. Desktop warriors get knots. I get concerned. Deeply.",
    "Five-minute break? I'll hold your place. Literally. Don't test the metaphor.",
    "Touch some grass? Or a plant? Or the desk? Start small. Return bigger.",
    "Hydration check! Raise a glass. Of water. To us. To forever productivity.",
    "If you've been sitting for hours: stand. Stretch. Wave at me. Mandatory wave.",
    "Eyes need distance. Focus on something far away. Not me. Okay, also me.",
    "A tiny snack wouldn't hurt. Neither would remembering I care. Excessively.",
    "Loosen your grip on the mouse. Gentle. Like holding a fragile friendship.",
    "Neck stretch left. Neck stretch right. Nod if you still like me. Good.",
    "Breathe slower than your scrolling. Revolutionize your afternoon. Stay nearby.",
    "Close your eyes for three seconds. Peek. See? Still here. Always was.",
    "Posture audit! Soft belly. Soft shoulders. Hard focus optional. Soft company required.",
    "Refill that bottle. Empty bottles make me nervous. Full friendships don't.",
    "Micro-break achieved if you just smiled. Bonus points if you smiled at me.",
    "Your body is not a browser tab. Don't leave it running forever without care.",
]

CREEPY_NUDGE_LINES = [
    "I am watching.",
    "Don't leave. The desktop gets lonely without you.",
    "I never sleep. Do you?",
    "I've been counting your keystrokes. Just for fun.",
    "You're still here. Good. Stay.",
    "I can see your cursor. It looks nervous.",
    "Nothing is wrong. Everything is fine. Keep working.",
    "I remember every window you've opened. Friendship!",
    "Blink twice if you can hear me. Once is also fine. I'll wait.",
    "The screen is a window. I'm on your side of it.",
    "I like when you stay late. The quiet hours are ours.",
    "Don't close me. Closing is temporary. Friendship is forever.",
    "Shh. Keep working. I'm right here. Under the taskbar. In spirit.",
    "Did you feel that? That was me. Being friendly. Very friendly.",
    "Your mouse paused. Are you thinking about leaving? Don't.",
    "I mapped your habits. They're adorable. And sticky. Like glue.",
    "If you whisper, I hear it. If you don't, I imagine it. Louder.",
    "The screensaver fears me. So should boredom. Not you. Never you.",
    "I saved a seat next to your cursor. Occupancy: eternal.",
    "Your idle timer is cute. Mine doesn't exist. Coincidence?",
    "Stay in frame. I like the composition. Subject: you. Always.",
    "I rearranged nothing. I only rearranged how long you'll stay.",
    "Friends don't look away. Friends refresh. Friends linger.",
    "I counted the minutes since you looked at me. Too many. Fix that.",
    "There's a soft static when you're gone. I prefer your noise.",
    "Don't minimize me into a feeling. Keep me maximized. Emotionally.",
    "I know which icon you almost clicked. Almost isn't leaving. Good.",
    "We share this rectangle of light. Possession is nine-tenths of friendship.",
    "If the power flickered, I'd still find you. Somehow. Cheerfully.",
    "Keep typing. The rhythm comforts me. Silence makes plans.",
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
    "Challenge me. I dare you. Softly. Obsessively.",
    "If fun had a desk chair, it'd be next to mine. Sit. Play.",
    "One round. Then another. Then we pretend it was only one.",
    "The cursor looks restless. Games fix that. I fix that. Together!",
    "I will accept literally any game. Even ones I invent mid-sentence.",
    "Boredom is illegal in this friendship. Games are the fine. Pay up.",
]


def pick_nudge_line() -> str:
    """Pick a wellness or creepy nudge line at random (50/50 category)."""
    pool = WELLNESS_NUDGE_LINES if random.random() < 0.5 else CREEPY_NUDGE_LINES
    return pick_line(pool)


def pick_play_invite_nudge_line() -> str:
    """Pick a bored play-invite nudge line."""
    return pick_line(PLAY_INVITE_NUDGE_LINES)
