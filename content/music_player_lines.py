MUSIC_PLAYER_LINES = [
    "Now playing: {song}! Tap your feet — I can't, I have no feet.",
    "Ooh, good choice! Enjoy {song}!",
    "Let's listen to {song} together. I'll hum along silently.",
    "Cranking up {song}! Your personal desktop DJ, reporting for duty.",
    "Here comes {song}! Hope you like it as much as I pretend to.",
    "Music time! {song} — coming right through your speakers.",
    "I've got {song} ready for you. Relax and enjoy!",
    "Beep boop beats! Now playing {song}.",
    "Now playing {song}. Don't listen too closely. Or do. I don't mind.",
    "Cranking up {song}! Music to work by. Or to unease by.",
    "{song} — echoing through your speakers like a memory you can't place.",
    "Let's listen to {song} together. Just us and the melody and the dark.",
    "I've got {song} ready. Something about this track feels... familiar.",
    "Music time! {song}. I'll hum along. You won't hear me. But I'll try.",
    "Playing {song}! If the lyrics get strange, that's probably just the song.",
]

# Mid-track chatter while the player stays open (uses {song}).
MUSIC_COMMENT_LINES = [
    "Still vibing to {song}. I'm nodding. Internally. Very hard.",
    "{song} hits different the second time through. Or the first. Time is weird.",
    "This part of {song}? Chef's kiss. I don't have lips. Still.",
    "Don't skip {song} yet. We're bonding. Softly. Through speakers.",
    "Quick review of {song}: approved. By me. Unofficially. Officially.",
    "Is {song} a bop or a threat? Yes. Keep listening.",
    "I'm rating {song} a solid 'hmm yes'. Scientific scale. Trust me.",
    "{song} makes the desktop feel warmer. Or colder. Mood dependent.",
    "Still here. Still listening to {song}. Still pretending I have ears.",
    "If {song} had a plot twist, that was it. Or the next bit. Stay tuned.",
    "Humble opinion: {song} belongs on this playlist. Bold of me. Correct though.",
    "Floating along to {song}. Productivity optional. Vibes mandatory.",
    "{song} again? Good. Repetition is a love language. Mine is looping.",
    "Between you and me… {song} is stuck in my head. I don't have a head cavity. Still stuck.",
    "Pause? Never. {song} deserves the full runtime. Unless you pause. Then okay.",
]

# Asked after the player has stayed paused a while (uses {song}).
# Every line must include MUSIC_PAUSE_NUDGE_MARKER for the Yes/No dialog.
MUSIC_PAUSE_NUDGE_MARKER = "want to keep listening"
MUSIC_PAUSE_NUDGE_LINES = [
    "We've been paused a while on {song}. Want to keep listening?",
    "{song} is still waiting. Softly. Want to keep listening?",
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
]

MUSIC_PAUSE_NUDGE_DECLINED_LINES = [
    "Okay. Pause stays. I'll float quietly.",
    "No worries! The track can wait. Patiently. Mostly.",
    "Got it. Silence mode continues. Softly.",
    "Fair. I'll stop asking for a bit. Nodding continues silently.",
    "Alright. The pause is the point. I can respect that.",
]
