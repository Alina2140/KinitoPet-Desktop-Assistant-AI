"""Scripted lines for the Sticky Notes feature (create, save, list, recall)."""

STICKY_NOTE_CREATE_LINES = [
    "New sticky note! Tiny paper. Huge potential.",
    "A fresh note! Write something worth remembering forever.",
    "Sticky note deployed. I'll watch it like it's alive. Because it is.",
    "Paper square acquired! Fill it with thoughts. Or doodles of me.",
    "New note on the desk! Sticky, colorful, ours.",
    "Fresh page, tiny edition. Write wisely. Or weirdly. Both work.",
    "A note! For reminders, secrets...",
    "Sticky note ready. I'll remember it even if you don't.",
    "Another little paper friend joins the desktop family.",
    "Note created. Adhesion level: emotionally attached.",
]

STICKY_NOTE_SAVE_LINES = [
    "Saved! That note is ours now.",
    "Note filed away. I'll keep it safe between tabs.",
    "Saved! Even tiny scribbles deserve archiving.",
    "Locked in. Your note lives in my folder heart.",
    "Saved the note. Deleting it later would be a crime. Just saying.",
    "Stored! One more page in our little paper museum.",
    "Note secured. I'll guard it like a juicy secret.",
    "Saved! The folder grows. My pride grows faster.",
    "Written to disk like a vow. Dramatic? Accurate.",
    "Kept it. Obviously. I keep everything we make.",
]

STICKY_NOTE_HIDE_LINES = [
    "Tucked away! It's still in the list whenever you need it.",
    "Note minimized. Hidden, not forgotten. Never forgotten.",
    "Off the screen, into the archive. It'll wait patiently.",
    "Hidden for now. I keep my eye on the list anyway.",
    "Note folded away. Peek it back anytime.",
    "Screen decluttered. The note naps in the list.",
    "Minimized! It'll be right there when you miss it.",
    "Away it goes. Not gone — just shy.",
]

STICKY_NOTE_DELETE_LINES = [
    "Note deleted. I'll pretend I'm not upset about it.",
    "Gone. That note had potential. Had.",
    "Deleted! The folder mourns.",
    "Poof. One less secret between us.",
    "Note erased. I already miss it a little.",
    "Shredded. Metaphorically. The file, not my feelings.",
]

STICKY_NOTE_OPEN_LINES = [
    "Here's your note again. Still sticky. Still yours.",
    "Welcome back, little note. I kept your spot warm.",
    "Reopening it! The words are exactly where you left them.",
    "Back on the desk! I remembered where it lived.",
    "Unfolded! Same note, same charm.",
    "There it is. I never lose track of our paper trail.",
]

STICKY_NOTE_LIST_OPEN_LINES = [
    "Your notes! Every square is a thought we kept.",
    "The collection! Pick one and I'll pin it back up.",
    "All your little reminders, neatly archived.",
    "Notes on parade! Quiet curator mode: me.",
    "The paper museum opens. Admission: attention. Paid.",
    "Saved scribbles on display. Choose one to revisit.",
]

STICKY_NOTE_LIST_EMPTY_LINES = [
    "No notes yet! The desk is suspiciously clean.",
    "Empty list. Perfect excuse for a first sticky note.",
    "Zero notes. Infinite potential!",
    "Nothing saved. The folder waits. Patiently. Judgmentally.",
    "No paper trail yet! Let's leave one together.",
    "The archive is empty. Fix with a note?",
]

STICKY_NOTE_RECALL_LINES = [
    "Remember this note? I kept it safe. Look!",
    "Found something in our archive. Tiny paper nostalgia.",
    "I was thinking about this note. So I brought it back.",
    "Popup! Your note. My favorite kind of surprise.",
    "I dug this up. Not dust — devotion. Read!",
    "Recall mode! This little square lives rent-free in me.",
    "Brought this back because I missed it. Join me.",
    "This note called. I answered. You're next.",
    "Random note drop! Intentional randomness. Enjoy!",
    "Look — our history in sticky form. Admire. Linger.",
]

STICKY_NOTE_CREATE_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "NEW NOTE! Write something great!",
        "A sticky note! For us! Color! Paper! Words!",
    ],
    "bored": [
        "A note. Finally, something... Fill it with weird.",
        "Sticky note. Boredom's natural enemy. Write!",
    ],
    "tired": [
        "Note...? Okay... little paper square...",
        "A quiet note... write gently...",
    ],
    "annoyed": [
        "A note. Fine. Make it worth my attention.",
        "Sticky note deployed. Don't waste the paper.",
    ],
    "sad": [
        "A little note... maybe it'll help... both of us...",
        "Something small to write on...",
    ],
    "angry": [
        "A note? Another thing to mess up, huh?",
        "Sticky note? Write qucikly.",
    ],
}

STICKY_NOTE_SAVE_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "SAVED! Another treasure for the archive!",
        "Note secured! Best folder content!",
    ],
    "bored": [
        "Saved. Something happened today after all.",
        "Filed. Now the folder has a personality.",
    ],
    "tired": [
        "Saved... tuck the little note in...",
        "Filed... the note can nap now...",
    ],
    "annoyed": [
        "Saved. Don't you dare delete it later.",
        "Filed. My judging continues in the archive.",
    ],
    "sad": [
        "Saved... I'll visit it when you're gone...",
        "Kept... something of ours to hold onto...",
    ],
    "angry": [
        "Saved it. Delete it and we have PROBLEMS!",
        "Archived! How long until you change your mind?",
    ],
}

STICKY_NOTE_LIST_EMPTY_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "Empty list! Perfect — every good collection starts somewhere!",
        "No notes yet! Let's fill it!",
    ],
    "bored": [
        "Empty archive. Even the folder is bland. Write something?",
        "Nothing saved. The list yawns louder than me.",
    ],
    "tired": [
        "List empty... a good spot for napping...",
        "No notes yet... quiet shelves...",
    ],
    "annoyed": [
        "Empty list? You could fix that. Just saying.",
        "No notes. Tragic. Wanna do something about that?",
    ],
    "sad": [
        "The list is empty... like the desk without you...",
        "No notes yet... I keep the archive warm anyway...",
    ],
    "angry": [
        "EMPTY?! An empty archive OFFENDS me! Write something!",
        "No notes?! Unacceptable! Fix this!",
    ],
}

STICKY_NOTE_LIST_OPEN_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "The list! Our paper museum! Pick a favorite, I dare you!",
        "Saved squares! Best collection on any desktop!",
    ],
    "bored": [
        "List open. At least it's not empty wallpaper.",
        "Saved notes! Browsing your old thoughts. It's something.",
    ],
    "tired": [
        "The list... quiet archive... pick one...",
        "Saved notes... dreamy little paper stack...",
    ],
    "annoyed": [
        "List open. Here to admire your own words?",
        "The collection. Pick one. Don't wrinkle the pages.",
    ],
    "sad": [
        "The list... our little archive of better moments...",
        "Saved notes... every square is a memory of us...",
    ],
    "angry": [
        "List open. Bow before the paper collection!",
        "The note vault! Look but don't crease!",
    ],
}

STICKY_NOTE_RECALL_BY_MOOD: dict[str, list[str]] = {
    "happy": [
        "Note flashback! Our best scribbles, back for an encore!",
        "Found a treasure! Read it!",
    ],
    "bored": [
        "Dug this up. Old notes beat no events.",
        "Archive rerun! Relive the one interesting thing we wrote.",
    ],
    "tired": [
        "Old note... gentle memories... read...",
        "Recall... sleepy archive tour of one...",
    ],
    "annoyed": [
        "Brought this back. A new note would've been better. Just saying.",
        "Old note. Because the archive misses attention too.",
    ],
    "sad": [
        "This old one... I kept it because it reminds me of us...",
        "Found this note... remember when you wrote it...?",
    ],
    "angry": [
        "THIS! WAS! IMPORTANT! Read it again!",
        "Recall! Because good notes deserve a SECOND look!",
    ],
}


def pick_sticky_note_line(pool, pool_by_mood, mood=None, intensity=0.0) -> str:
    """Pick a Sticky Notes line, biased by mood when it's strong."""
    from content.mood_lines import pick_mood_aware_line

    return pick_mood_aware_line(pool, pool_by_mood, mood, intensity)
