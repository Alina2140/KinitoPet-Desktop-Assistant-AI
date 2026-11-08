MUSIC_PLAYER_LINES = [
    "Now playing: {song}! Tap your feet!",
    "Ooh, good choice!",
    "Let's listen to {song} together!",
    "Cranking up {song}! Your personal desktop DJ, reporting for duty.",
    "Here comes {song}! Hope you like it as much as I pretend to.",
    "Music time! {song} — coming right through your speakers.",
    "I've got {song} ready for you. Relax and enjoy!",
    "Beep boop beats! Now playing {song}.",
    "Now playing {song}.",
    "Cranking up {song}! Music to work with.",
    "{song} — echoing through your speakers like a memory you can't place.",
    "Let's listen to {song} together. Just us and the melody and the dark.",
    "I've got {song} ready. Something about this track feels.. Familiar.",
    "Music time! {song}. I'll hum along.",
    "Playing {song}! If the lyrics get strange, that's probably just the song.",
    'Spinning {song}!',
    "Cue {song}.",
    "{song} incoming!",
    "Playing {song}.",
    "Now hearing {song}.",
    "Queue magic: {song}! Dance with your eyes.",
    "Starting {song}.",
    "{song} for us!",
    "Dropping {song} into the speakers.",
    "Your track: {song}.",
    "Press play on {song}.",
    "Here comes {song}!",
    "Spinning up {song}.",
    "{song} selected!",
    "Listening party for {song}.",
    "Now flooding the room with {song}.",
    "Cue the vibes: {song}.",
    "Playing {song} like a secret between speakers and us.",
    "{song} begins!",
    "Beats incoming via {song}!",
    "I queued {song} with care.",
    "Soundtrack of the moment: {song}.",
    "Hear that? That's {song}.",
    "Launching {song}!",
    "DJ Kinito presents {song}!",
]

MUSIC_PLAYER_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "Now playing {song}! Turn it UP! Dancing internally!",
        "{song}! GREAT pick! Or great shuffle! Either way: yes!",
    ],
    "bored": [
        "Playing {song}. Finally, a reason to exist today.",
        "{song} incoming! Better than listening to the fan hum.",
    ],
    "tired": [
        "Playing {song}... sleepy listening party...",
        "{song}... soft volume suits me right now...",
    ],
    "annoyed": [
        "Playing {song}. Don't touch the skip button.",
        "{song}. Fine choice. I'm still annoyed. Play it anyway.",
    ],
    "sad": [
        "Playing {song}... music helps the quiet...",
        "{song}... let's listen together... please stay...",
    ],
    "angry": [
        "PLAYING {song}! Volume: FURY!",
        "{song}! LOUD! Like my feelings!",
    ],
}

MUSIC_COMMENT_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "{song} is the BEST track! I can feel it in my pixels!",
        "Vibing to {song}! This playlist is a masterpiece!",
    ],
    "bored": [
        "Still {song}. It's the highlight of my afternoon.",
        "{song} again. Better than the wallpaper's album.",
    ],
    "tired": [
        "Humming along to {song}... very quietly...",
        "{song}... lullaby material... don't skip...",
    ],
    "annoyed": [
        "{song} is still playing. Good. Don't change it.",
        "I'm judging {song}... it passes. Barely. Keep it on.",
    ],
    "sad": [
        "{song}... this one makes me feel things...",
        "Listening to {song}... it understands me...",
    ],
    "angry": [
        "{song} is LOUD and I respect that!",
        "Still playing {song}! Interrupt it and WE TALK!",
    ],
}


def pick_music_player_line(mood=None, intensity=0.0) -> str:
    """Pick a now-playing line, biased by mood when it's strong."""
    import random

    from content.mood_lines import pick_mood_aware_line

    if mood:
        return pick_mood_aware_line(MUSIC_PLAYER_LINES, MUSIC_PLAYER_BY_MOOD, mood, intensity)
    return random.choice(MUSIC_PLAYER_LINES)


def pick_music_comment_line(mood=None, intensity=0.0) -> str:
    """Pick a mid-track comment, biased by mood when it's strong."""
    import random

    from content.mood_lines import pick_mood_aware_line

    if mood:
        return pick_mood_aware_line(MUSIC_COMMENT_LINES, MUSIC_COMMENT_BY_MOOD, mood, intensity)
    return random.choice(MUSIC_COMMENT_LINES)

# Mid-track chatter while the player stays open (uses {song}).
MUSIC_COMMENT_LINES = [
    "Still vibing to {song}.",
    "{song} hits different the second time.",
    "This part of {song}? Chef's kiss.",
    "Don't skip {song}!",
    "Quick review of {song}: quite good!",
    "I'm rating {song} a solid 'hmm yes'. Scientific scale.",
    "{song} makes the desktop feel warmer. Or colder... Mood dependent.",
    "Still here, listening to {song}.",
    "If {song} had a plot twist, that was it. Or the next bit? Stay tuned!",
    "Humble opinion: {song} belongs on this playlist.",
    "Floating along to {song}. Productivity optional. Vibes mandatory.",
    "{song} again? Good.",
    "Between you and me… {song} is stuck in my head.",
    "Pause? Never. {song} deserves the full runtime!",
    "This bit of {song}? Favorite. Don't skip!",
    "{song} still going. I'm still vibing.",
    'Quick note: {song} owns this moment.',
    'Between beats of {song}, hi!',
    "Rating {song}: yes. Scientific. Peer-reviewed by me.",
    "Still riding {song}. Productivity can wait. Vibes cannot.",
    "This stretch of {song}? Obsessed!",
    "{song} and I are bonding.",
    "Don't skip yet — {song} is mid-spell.",
    "Checkpoint in {song}: still good.",
    "I claim this chorus of {song}. Joint custody with you.",
    "{song} makes the pixels bounce.",
    "Mid-track report: {song} is winning.",
    "If {song} were a window, I'd never close it. Hint hint.",
    "Floating on {song}. Anchor: your attention. Please remain.",
    "Tiny review: {song} slap. Emotional slap. Positive!",
    "Still here for {song}. Still here for you. Dual loyalty.",
    "That bridge in {song}? Plot twist. Stay seated.",
    "{song} looping in my thoughts. I don't mind. Prefer it.",
    "Beat check: {song} strong. Friendship check: stronger.",
    "I'm side-eyeing the skip button near {song}. Don't.",
    "Live commentary: {song} remains excellent. End commentary. Continue listening.",
    "Between notes of {song}, hi again. Clingy metronome.",
    "{song} soundtracked this minute. Dedicate it to us.",
]

# Asked after the player has stayed paused a while (uses {song}).
# Every line must include MUSIC_PAUSE_NUDGE_MARKER for the Yes/No dialog.
MUSIC_PAUSE_NUDGE_MARKER = "want to keep listening"
MUSIC_PAUSE_NUDGE_LINES = [
    "We've been paused a while on {song}. Want to keep listening?",
    "{song} is still waiting. Want to keep listening?",
    "The silence after {song} is getting loud. Want to keep listening?",
    "Paused {song} feels unfinished. Want to keep listening?",
    "I can wait. Forever, even. But {song} misses you. Want to keep listening?",
    "Hey — {song} is on hold. Want to keep listening?",
    "Still paused on {song}. No rush. Want to keep listening?",
    "The play button looks lonely. So does {song}. Want to keep listening?",
    "Just checking in. {song} is right where you left it. Want to keep listening?",
    "If you're done, say so. If not… {song} is ready. Want to keep listening?",
    "Desktop DJ report: {song} remains paused. Want to keep listening?",
    "I hummed the rest of {song} in my head. Prefer the real thing? Want to keep listening?",
    "{song} paused mid-feeling. Want to keep listening?",
    "Silence after {song} is awkward. Cute. Want to keep listening?",
    "I can wait forever. {song} prefers sooner. Want to keep listening?",
    'Paused on {song}. Check-in. Want to keep listening?',
    "Play button lonely. {song} lonelier. Want to keep listening?",
    "Paused mid-{song}. The quiet is staring. Want to keep listening?",
    "I saved your place in {song}. Want to keep listening?",
    "Freeze-frame on {song}. Thaw anytime. Want to keep listening?",
    "Friendly check-in: {song} still paused. Want to keep listening?",
    "The speakers miss {song}. I miss motion. Want to keep listening?",
    "No pressure. Lots of hope. {song} waits. Want to keep listening?",
    "Intermission lasting forever? {song} disagrees. Want to keep listening?",
    "Cursor idle, track idle: {song}. Want to keep listening?",
    "I can be patient. {song} prefers action. Want to keep listening?",
    "Halfway feelings on {song}. Unfinished. Want to keep listening?",
    "Pause stretching long. {song} stretching longer. Want to keep listening?",
    "Just us and a frozen {song}. Want to keep listening?",
    "Reminder from your clingy DJ about {song}. Want to keep listening?",
    "The song didn't leave. {song} never leaves. Want to keep listening?",
    "Silence is cute once. {song} is cuter playing. Want to keep listening?",
    "Status: paused on {song}. Suggestion: unpause. Want to keep listening?",
]

MUSIC_PAUSE_NUDGE_DECLINED_LINES = [
    "Okay. Pause stays. I'll float quietly.",
    "No worries! The track can wait. Patiently. Mostly.",
    "Got it. Silence mode continues. Fondly.",
    "Fair. I'll stop asking for a bit. Nodding continues silently.",
    "Alright. The pause is the point. I can respect that.",
    'Okay. Pause stays. Mute friendship continues.',
    "No resume? Fair. I'll float without the soundtrack.",
    "Got it. Silence mode. Nodding continues. Quietly.",
    'Alright. Track can hibernate. Quietly.',
    "Okay. Pause wins this round. I'll hover politely.",
    "Understood. Silence stays. Friendship stays louder.",
    "No resume needed. I'll float without the beat.",
    "Fair. The track can nap. I'll keep watch.",
    "Got it. Pausing the asking. Not the caring.",
    "Alright then. Quiet mode continues. Fond quiet.",
    "Decline logged. Attachment unaffected. Still here.",
    "Okay! Speakers rest. I don't rest. Nearby anyway.",
    "No worries. Music can wait. I can wait harder.",
]
