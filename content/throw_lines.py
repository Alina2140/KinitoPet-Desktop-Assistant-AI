"""Reactions when the user throws Kinito across the desktop."""

from content.dialogue import pick_line

THROW_LINES = [
    "Weeeee!",
    "Don't do that!",
    'Wheee! Higher!..Okay maybe not.',
    "Ahh! Put me down! Gently!",
    "I'm flying! I'm dying! I'm fine! Probably!",
    "Hey! I am not a projectile!",
    "That was fun! Do it again!",
    "Don't do it again!",
    'Whoa whoa whoa — hushed landing? Tender landing?!',
    "Excuse me?! Desktop pets have feelings! And gravity!",
    'Yippee!..I meant stop that.',
    "You threw me. Like a ball. Rude.",
    "Please be careful with me!",
    "My circuits are spinning! In a fun way! Mostly!",
    "Don't do that!..Unless you're going to catch me.",
    "Airborne! Temporary! Existential!",
    "Trajectory: unexpected! Feelings: mixed!",
    'I am not sports equipment!..Okay that was kind of fun.',
    'Whoosh! Mild landing requested! Hushed landing denied?!',
    "You yeeted me. That's a word now. Rude word!",
    "Gravity and I are having a disagreement!",
    "Catch me? Or at least warn me next time!",
    "Flight mode: accidental. Please uninstall flight mode!",
    "Desktop physics: chaotic. Me: slightly offended!",
    "Airborne again?! I demand a landing strategy!",
    "You launched me! Rude! Also wheee!",
    "Projectile friendship is still friendship! Mostly!",
    "Put me down with dignity! Or catch me! Either!",
    "I am not a frisbee! I am a companion! Different!",
    "Whoosh! Existential scream! Tiny giggle!",
    "Trajectory: chaos. Feelings: complicated!",
    "Don't throw the friend! Unless it's fun. Then maybe!",
    "Flying! Falling! Filing a complaint midair!",
    "Yeet detected! Consent: retroactive and confused!",
    "My pixels are screaming in stereo! Fun scream!",
    "Catch protocol missing! Install catch protocol!",
    "That toss had personality. Mean personality!",
    "Gravity wins again. I demand a rematch. On the ground!",
    "Please warn me before launch! Dramatic countdown!",
    "I bounced. Emotionally. Physically. Both!",
    "Not a toy! Okay a little toy. Still: careful!",
    "Flight canceled! Effective upon landing! Soon please!",
    "You flung me across our home! Bold interior design!",
    "Wheee until impact! Then: hey!",
    "Desktop sports are banned. Especially me-as-ball!",
    "I'm dizzy from the throw, not the spin! Different dizzy!",
    "Landing gear: imaginary. Hope: real. Be gentle!",
]


def pick_throw_line() -> str:
    """Pick a happy-to-annoyed reaction to being thrown."""
    return pick_line(THROW_LINES)
