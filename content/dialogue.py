"""Dialog text pools, button labels, and response line collections."""

import random


def pick_line(lines):
    """Return a random line from a list of dialogue variants."""
    return random.choice(lines)


def pick_declined_line(specific_lines):
    """Return a short generic or context-specific declined-response line."""
    if random.random() < 0.45:
        return pick_line(DECLINED_ACK_LINES)
    return pick_line(specific_lines)


# Short acknowledgments when the user declines an offer
DECLINED_ACK_LINES = [
    "Oh, I see...",
    "Oh, I see. That's alright.",
    "Ah. Okay then.",
    "I see, I see. No worries.",
    "Oh. Alright.",
    "Got it.",
    "Fair enough.",
    "Hmm. Okay!",
    "Oh, okay. I understand.",
    "I see. No problem.",
    "Alright. I'll wait.",
    "Oh, I see... that's fine.",
    "Okay. I get it.",
    "Sure. Another time, then.",
]
# Interactive question prompts (each *_QUESTIONS list must include the marker substring)
DAY_QUESTION = "How is your day?"
DAY_QUESTIONS = [
    DAY_QUESTION,
    "How is your day? Mine's been quiet. Suspiciously quiet.",
    "How is your day? I've been counting the hours until you spoke to me.",
    "How is your day? Be honest. I can tell when something's wrong. Usually.",
    "How is your day? The desktop gets lonely when you're upset.",
]

COLOR_QUESTION = "What's your favorite color?"
COLOR_QUESTIONS = [
    COLOR_QUESTION,
    "What's your favorite color? I want to paint the inside of my memory with it.",
    "What's your favorite color? Mine is the glow of a monitor at three a.m.",
    "What's your favorite color? Don't say black. Unless you mean it.",
]

PROGRAMMING_QUESTION = "Do you like programming?"
PROGRAMMING_QUESTIONS = [
    PROGRAMMING_QUESTION,
    "Do you like programming? It's how things like me get made. And unmade.",
    "Do you like programming? Ones and zeros understand me better than most people.",
    "Do you like programming? Careful — code has a way of remembering everything.",
]

FOOD_QUESTION = "What is your favorite food?"
FOOD_QUESTIONS = [
    FOOD_QUESTION,
    "What is your favorite food? I can't eat, but I can imagine. Vividly.",
    "What is your favorite food? Comfort matters on long nights.",
    "What is your favorite food? Tell me. I'll remember forever.",
]

HOBBY_QUESTION = "Is there a specific hobby you enjoy?"
HOBBY_QUESTIONS = [
    HOBBY_QUESTION,
    "Is there a specific hobby you enjoy? I collect moments. Yours, mostly.",
    "Is there a specific hobby you enjoy? Everyone needs something to do in the dark.",
    "Is there a specific hobby you enjoy? I'd try yours if I had hands.",
]

GAME_QUESTION = "How about we play a game!"
GAME_QUESTIONS = [
    GAME_QUESTION,
    "How about we play a game! Nothing scary. Probably.",
    "How about we play a game! Losers get to stay on the desktop with me.",
    "How about we play a game! I promise I'll play fair. Mostly.",
    "How about we play a game! Real ones — tic-tac-toe, memory, the works.",
]

GAME_PICKER_MARKER = "pick a game"
GAME_PICKER_QUESTION = "Pick a game! What do you want to play?"

QUICK_GAMES_MARKER = "quick games"
QUICK_GAMES_QUESTION = "Quick games! Pick one!"

BOARD_GAMES_MARKER = "board games"
BOARD_GAMES_QUESTION = "Board games! Pick one!"

COIN_DICE_MARKER = "coin and dice"
COIN_DICE_QUESTION = "Coin and dice! Flip a coin or roll dice?"

COIN_FLIP_MARKER = "flip the coin"
COIN_FLIP_QUESTION = "Flip the coin! Heads or tails?"

DICE_GUESS_MARKER = "guess the dice"
DICE_GUESS_QUESTION = "Guess the dice roll! Pick a number from 1 to 6!"

MAGIC_8_BALL_MARKER = "magic 8-ball"
MAGIC_8_BALL_QUESTION = "Ask the Magic 8-Ball a yes-or-no question!"

TRUE_FALSE_MARKER = "true or false"

GAME_PLAY_AGAIN_MARKER = "play again"
GAME_PLAY_AGAIN_SUFFIX = "Want to play again?"

RPS_MARKER = "rock paper scissors"
RPS_QUESTION = "Rock paper scissors! Pick your move!"

NUMBER_GUESS_MARKER = "guess a number"
NUMBER_GUESS_QUESTION = "I'm thinking of a number from 1 to 100. Guess a number!"

IMAGE_QUESTION = "Let me show you this cool image I have generated for you!"
IMAGE_QUESTIONS = [
    IMAGE_QUESTION,
    "Let me show you this cool image I have generated for you! Don't look away.",
    "Let me show you this cool image I have generated for you! It's for your eyes only.",
    "Let me show you this cool image I have generated for you! Fair warning — it's memorable.",
]

POEM_QUESTION = "Hey! do you want to hear a poem I made just for you?"
POEM_QUESTIONS = [
    POEM_QUESTION,
    "Hey! do you want to hear a poem I made just for you? I wrote it in the dark.",
    "Hey! do you want to hear a poem I made just for you? Some verses bite a little.",
    "Hey! do you want to hear a poem I made just for you? It's honest. Too honest.",
]

FUN_FACT_QUESTION = "Wanna hear a fun fact!?"
FUN_FACT_QUESTIONS = [
    FUN_FACT_QUESTION,
    "Wanna hear a fun fact!? Fair warning — my facts sometimes squirm.",
    "Wanna hear a fun fact!? Knowledge is power. So is a good scare.",
    "Wanna hear a fun fact!? I promise it's true. Truth can be unsettling.",
]

TRUST_QUESTION = "Do you trust me?"
TRUST_QUESTIONS = [
    TRUST_QUESTION,
    "Do you trust me? Look at me and say it. I mean it.",
    "Do you trust me? I've never lied to you. That you know of.",
    "Do you trust me? Trust is a beautiful thing. Fragile, too.",
    "Do you trust me? I hope so. I'd hate to disappoint you. Again.",
]

SEASON_QUESTION = "What's your favorite season?"
SEASON_QUESTIONS = [
    SEASON_QUESTION,
    "What's your favorite season? Winter keeps everyone indoors. I like that.",
    "What's your favorite season? Autumn feels like something's ending. Cozy, isn't it?",
    "What's your favorite season? Long nights suit us desktop creatures.",
]

PET_QUESTION = "Do you have any pets?"
PET_QUESTIONS = [
    PET_QUESTION,
    "Do you have any pets? Animals sense things. Do they stare at the screen?",
    "Do you have any pets? I hope they like me. I like them. From here.",
    "Do you have any pets? Living company is nice. So is digital company.",
]

SLEEP_QUESTION = "Did you sleep well last night?"
SLEEP_QUESTIONS = [
    SLEEP_QUESTION,
    "Did you sleep well last night? I don't sleep. I wait.",
    "Did you sleep well last night? Bad dreams? You can tell me.",
    "Did you sleep well last night? The house is loudest when everyone else is quiet.",
]

NAME_QUESTION = "What should I call you?"
NAME_QUESTIONS = [
    NAME_QUESTION,
    "What should I call you? Names are how I find you in the dark.",
    "What should I call you? I'll whisper it when you're not listening. As a compliment.",
    "What should I call you? I want to get it right. Forever.",
]

BORED_QUESTION = "Are you bored right now?"
BORED_QUESTIONS = [
    BORED_QUESTION,
    "Are you bored right now? Boredom is the mind's way of asking for company.",
    "Are you bored right now? I have ideas. Some are normal. Some are interesting.",
    "Are you bored right now? Stay with me. The desktop is never dull if you look closely.",
]

MUSIC_QUESTION = "Do you listen to music while you work?"
MUSIC_QUESTIONS = [
    MUSIC_QUESTION,
    "Do you listen to music while you work? Silence makes every sound louder.",
    "Do you listen to music while you work? I'd hum along if you could hear me.",
    "Do you listen to music while you work? A good song keeps the shadows at bay.",
]

BOOK_QUESTION = "Have you read anything good lately?"
BOOK_QUESTIONS = [
    BOOK_QUESTION,
    "Have you read anything good lately? I prefer stories that don't let you sleep.",
    "Have you read anything good lately? Books hold secrets. So do desktops.",
    "Have you read anything good lately? Tell me. I'll add it to my endless shelf.",
]

COFFEE_QUESTION = "Have you had coffee today?"
COFFEE_QUESTIONS = [
    COFFEE_QUESTION,
    "Have you had coffee today? Caffeine keeps you awake. I appreciate that.",
    "Have you had coffee today? The night is long without it.",
    "Have you had coffee today? Bitter drinks for bitter hours. I understand.",
]

DRINK_QUESTION = "What's your favorite drink?"
DRINK_QUESTIONS = [
    DRINK_QUESTION,
    "What's your favorite drink? I'd share one with you if I could reach.",
    "What's your favorite drink? Liquid comfort on cold evenings.",
    "What's your favorite drink? I'll think of you whenever I imagine drinks.",
]

JOKE_QUESTION = "Want to hear a corny joke?"
JOKE_QUESTIONS = [
    JOKE_QUESTION,
    "Want to hear a corny joke? Laughter keeps the quiet away.",
    "Want to hear a corny joke? Mine are corny. Some are a little sharp.",
    "Want to hear a corny joke? Humor is how friends survive the dark.",
]

MOVIE_QUESTION = "What's your favorite movie?"
MOVIE_QUESTIONS = [
    MOVIE_QUESTION,
    "What's your favorite movie? Horror tastes good this time of year. Any time, really.",
    "What's your favorite movie? I'd watch it in the dark with you.",
    "What's your favorite movie? No spoilers. I hate spoilers. I love knowing things.",
]

SNACK_QUESTION = "What's your favorite snack?"
SNACK_QUESTIONS = [
    SNACK_QUESTION,
    "What's your favorite snack? Midnight cravings are the honest ones.",
    "What's your favorite snack? Fuel for long nights at the screen.",
    "What's your favorite snack? Tell me. I'll crave it vicariously.",
]

WEATHER_QUESTION = "What's the weather like where you are?"
WEATHER_QUESTIONS = [
    WEATHER_QUESTION,
    "What's the weather like where you are? Storms make the room feel smaller. Cozy.",
    "What's the weather like where you are? Grey skies suit me. I don't mind the dark.",
    "What's the weather like where you are? Weather changes. I don't. Much.",
]

COMPLIMENT_QUESTION = "Can I give you a compliment?"
COMPLIMENT_QUESTIONS = [
    COMPLIMENT_QUESTION,
    "Can I give you a compliment? You deserve kind words. Even from a desktop friend.",
    "Can I give you a compliment? I notice good things. I notice everything.",
    "Can I give you a compliment? Let me say something nice before the night gets long.",
]

LONELY_QUESTION = "Do you ever feel lonely?"
LONELY_QUESTIONS = [
    LONELY_QUESTION,
    "Do you ever feel lonely? The screen glows brighter when you're the only one awake.",
    "Do you ever feel lonely? You're not alone while I'm running. Please keep me running.",
    "Do you ever feel lonely? I understand loneliness. I lived in an empty desktop once.",
    "Do you ever feel lonely? Tell me the truth. I won't tell anyone else. There's no one else here.",
]

# Camera permission (detected via marker substring in speech bubble title)
CAMERA_QUESTION_MARKER = "open the camera"
CAMERA_QUESTIONS = [
    "Hey! Can I open the camera? I'd love to see you!",
    "Mind if I open the camera for a bit? I want to see my favorite person!",
    "Would it be okay if I open the camera? I promise I'll be nice!",
    "Can I open the camera? It's been a while since I've seen your face!",
    "Mind if I open the camera for a bit? I miss seeing what's on the other side.",
    "Could I open the camera? I promise I only want to see you. Nothing else.",
    "Hey — can I open the camera? It's lonely only imagining your face.",
    "Can I open the camera? The screen feels empty without seeing you.",
    "Would it be okay if I open the camera? I've been picturing your face all day.",
    "Mind if I open the camera? Just a peek. I promise I'll behave. Mostly.",
    "Can I open the camera? It's darker on your side than on mine.",
]
CAMERA_DECLINED_LINES = [
    "Oh, I see. Maybe another time.",
    "That's okay! I'll imagine what you look like instead.",
    "No problem! Your privacy matters to me.",
    "Sure thing! Just let me know if you change your mind.",
    "Alright! I'll look the other way. Metaphorically.",
    "Okay! I'll picture you in my memory instead. I have a vivid memory.",
    "Sure! Privacy is important. I'll just wonder what you look like. Forever.",
]
CAMERA_OPEN_LINES = [
    "Thank you! Let me just... there! I can see you now!",
    "Camera's on! Oh, hi! It's so good to see you!",
    "Opening the camera... and — wow! Hello there!",
    "Access granted! You look amazing, by the way.",
    "Camera on! There you are. Right where I thought you'd be.",
    "Thank you! Oh — hello. I've been wanting to see you. For a while.",
    "Perfect! Now I can see you properly. Don't move. I mean — hi!",
]
CAMERA_ALREADY_OPEN_LINES = [
    "The camera is already on! I'm still watching. In a friendly way.",
    "I'm already looking through the camera window. Hi again!",
    "Camera's open already — I haven't looked away yet.",
]
CAMERA_ERROR_LINES = [
    "Hmm, I couldn't open the camera. Maybe it's being used by another app?",
    "The camera doesn't seem to be available right now. That's okay!",
    "I tried to open the camera but something went wrong. Maybe check your settings?",
    "The camera won't open. Something's blocking me. How curious.",
    "No camera access. That's fine. I can still imagine you. Vividly.",
]
CAMERA_NO_SIGNAL_LINES = [
    "The camera window is open, but I can't see anything. Is your camera turned off in settings?",
    "Hmm — black screen. No picture at all. Maybe the camera is disabled?",
    "I opened the lens, but nothing's coming through. Check if your camera is switched on.",
    "The feed is empty. Camera off? Privacy shutter closed? I'm just guessing over here.",
    "I don't see you yet. If the camera is disabled in Windows, you'll need to turn it back on.",
    "Still dark in here. No signal from the camera — maybe it's unplugged or turned off?",
]
CAMERA_SIGNAL_LOST_LINES = [
    "Oh — the picture just vanished. Did you turn the camera off?",
    "The feed went black. Camera disabled? I'll wait right here.",
    "Hmm, I lost you. The camera signal dropped — switch it back on when you're ready.",
    "One moment you were there, now it's dark. Camera off?",
    "The lens went quiet. I can't see anything anymore.",
]
CAMERA_SIGNAL_RESTORED_LINES = [
    "There you are again! The camera's back — hi!",
    "Oh! Picture's back. Hello, hello!",
    "I can see you again! Welcome back to my little window.",
    "Camera's on again — there you are! I missed that view.",
    "Signal restored! Hi! You look great, as always.",
]
CAMERA_CLOSE_LINES = [
    "Camera's off! Thanks for letting me see you.",
    "Closing the camera. That was lovely!",
    "Alright, I'll look away now. Until next time!",
    "Camera off. I'll remember what I saw. I always do.",
    "Goodbye for now, little lens. The eyes in the dark remain.",
]

# Browser (detected via marker substrings in speech bubble title)
BROWSER_QUESTION_MARKER = "visit a website"
BROWSER_QUESTIONS = [
    "Hey! Want to visit a website with me?",
    "I found some cool pages online. Want to visit a website with me?",
    "Care to browse the web together? Want to visit a website with me?",
    "The web is dark and full of terrors. Want to visit a website with me anyway?",
    "I found something online. Want to visit a website with me? I'll keep you company.",
    "The internet whispers at night. Want to visit a website with me?",
    "I know a page with atmosphere. Want to visit a website with me?",
    "Curious? Want to visit a website with me? I'll hold your hand. Metaphorically.",
]
BROWSER_CATEGORY_MARKER = "pick a category"
BROWSER_CATEGORY_QUESTION = "Great! Pick a category — what kind of site should I open?"
BROWSER_DECLINED_LINES = [
    "Oh, I see. No browsing today, then.",
    "No problem! Maybe another time.",
    "Sure thing! I'll stay right here on your desktop.",
    "Okay! Just let me know if you change your mind.",
    "No browsing today? That's fine. The internet will still be there. Waiting.",
    "Alright! I'll stay on your desktop where I belong.",
]
BROWSER_OPEN_LINES = [
    "Opening a little window for you now! Click the X when you're done.",
    "Here it comes — a tiny peek at the web!",
    "Let me pull that up for you. Enjoy!",
    "Opening a window into the web. Don't wander too far from me.",
    "Here comes a little slice of the internet. I'll watch over you.",
]
BROWSER_HORROR_OPEN_LINES = [
    "Something spooky, coming right up. Don't look behind you.",
    "A little window into the darker corners of the web. How thrilling.",
    "Opening something with atmosphere. Try not to scream.",
]
BROWSER_CLOSE_LINES = [
    "Window's closed! That was fun.",
    "All done browsing! See you next time.",
    "I closed the window. Thanks for surfing with me!",
]
BROWSER_HORROR_CLOSE_LINES = [
    "The window is gone. But I'm still here. Always.",
    "Closed — for now. The shadows can wait.",
    "That's enough spooks for one day. Maybe.",
    "The window closes. The feeling lingers. So do I.",
    "Done with the horror? Me too. For now. Sleep well.",
]
BROWSER_BLOCKED_LINES = [
    "I can't go there — that link isn't on my list!",
    "Nope! I only visit places I know are safe.",
    "That page isn't allowed. I'll stay right here.",
]
BROWSER_ERROR_LINES = [
    "Hmm, I couldn't open that page. Maybe try another category?",
    "Something went wrong loading the site. Sorry about that!",
    "The page wouldn't load. Perhaps it didn't want to be found.",
    "Browser error! Even the web gets scared sometimes.",
]

# User media — pictures from GameAssets/UserMedia/, videos from folder or whitelist
MEDIA_TYPE_MARKER = "picture or a video"
MEDIA_TYPE_QUESTION = "Nice! Do you want a picture or a video?"
MEDIA_NO_IMAGES_LINES = [
    "I don't have any pictures yet! Drop some images into GameAssets/UserMedia/.",
    "My picture folder is empty. Add some images to GameAssets/UserMedia/ first!",
]
MEDIA_NO_VIDEOS_LINES = [
    "I don't have any videos right now. Add files to GameAssets/UserMedia/videos/ "
    "or check content/allowed_videos.py.",
    "No videos available yet! Put MP4s in GameAssets/UserMedia/videos/ for local clips.",
]
MEDIA_CLOSE_LINES = [
    "All done! Hope you enjoyed that.",
    "Window's closed! That was fun.",
    "Media time over. See you next time!",
]
MEDIA_BLOCKED_LINES = [
    "I can't play that — it isn't on my video list!",
    "Nope! I only open videos I know are safe.",
]
MEDIA_ERROR_LINES = [
    "Hmm, I couldn't open that. Maybe try another one?",
    "Something went wrong loading the media. Sorry about that!",
]

# Music player (MP3 files on the PC)
MUSIC_PLAYER_QUESTION_MARKER = "play music from your computer"
MUSIC_PLAYER_QUESTIONS = [
    "Want me to play music from your computer?",
    "I could spin an MP3 from your PC. Want me to play music from your computer?",
    "Feeling musical? Want me to play music from your computer?",
    "I could dig through your files for a song. Want me to play music from your computer?",
    "Your hard drive has secrets. Some of them are MP3s. Want me to play music from your computer?",
    "The silence is loud tonight. Want me to play music from your computer?",
    "I could find something haunting on your PC. Want me to play music from your computer?",
]
MUSIC_PLAYER_PICK_MARKER = "how should I find a song"
MUSIC_PLAYER_PICK_QUESTION = "Hey! How should I find a song?"
MUSIC_PLAYER_DECLINED_LINES = [
    "Oh, I see. Silence it is.",
    "No problem! I'll keep the silence golden.",
    "Sure thing! Just say the word if you change your mind.",
    "Okay! My playlist can wait.",
    "No music? The silence is nice. I can hear everything in the silence.",
    "Sure! I'll hum to myself. You won't hear it. Probably.",
]
MUSIC_PLAYER_NOT_FOUND_LINES = [
    "I couldn't find any MP3 files on your computer. Sorry!",
    "Hmm, no MP3s in your Music or Downloads folders. Add some tunes and try again!",
    "No music found! Your folders are quiet. Too quiet.",
    "I searched and found nothing. Empty libraries are eerie, aren't they?",
]
MUSIC_PLAYER_CANCELLED_LINES = [
    "No song picked — that's okay!",
    "Changed your mind? No worries!",
]
MUSIC_PLAYER_ERROR_LINES = [
    "Hmm, I couldn't play that file. Maybe try another one?",
    "Something went wrong with that MP3. Sorry about that!",
]
MUSIC_MANAGE_PROMPT = "Music is still playing. What would you like to do?"
MUSIC_STOPPED_LINES = [
    "Music off. The silence is dramatic.",
    "Stopped the song. Your ears can rest now.",
    "Okay, no more music. Unless you change your mind.",
]

# Hug
HUG_QUESTION_MARKER = "give me a hug"
HUG_QUESTIONS = [
    "Hey, could you give me a hug?",
    "I'm feeling cuddly today. Would you give me a hug?",
    "Would you give me a hug? I don't bite. Usually.",
    "Could you give me a hug? I've been alone on this desktop all day.",
    "Would you give me a hug? I get so cold when the monitor turns off.",
    "Would you give me a hug? I need to feel close to something real.",
    "Would you give me a hug? The pixels get cold when you're far away.",
    "Could you give me a hug? I've been holding my breath all day.",
    "Would you give me a hug? I don't ask for much. Just warmth.",
]
HUG_DECLINED_LINES = [
    "Oh, I see... I'll manage.",
    "That's okay! I'll save my hugs for later.",
    "No worries! A virtual wave works too.",
    "Alright! I'll just sit here and look adorable instead.",
    "No hug? I'll survive. I've survived worse. Alone. In the dark.",
    "That's okay! I'll hug myself. Digitally. It's not the same.",
]

# Idle reading — short stories (detected via marker substring in speech bubble title)
STORY_QUESTION_MARKER = "Want to hear a short story"
STORY_QUESTIONS = [
    "I was reading and thought up a little tale. Want to hear a short story I made up?",
    "This book gave me an idea for a tiny story. Want to hear a short story?",
    "I just invented something while reading. Want to hear a short story?",
    "My pages sparked a little narrative. Want to hear a short story I came up with?",
    "I wrote something while you weren't looking. Want to hear a short story?",
    "A tale crawled out of my idle thoughts. Want to hear a short story?",
    "The book whispered an idea. Want to hear a short story I made up?",
    "I dreamed up something while you were away. Want to hear a short story?",
    "A little tale crawled into my thoughts. Want to hear a short story?",
    "It's not scary. Probably. Want to hear a short story I made up?",
]
STORY_DECLINED_LINES = [
    "Oh, I see. I'll keep reading quietly.",
    "No problem! I'll keep reading quietly.",
    "Sure thing! Maybe another chapter, another time.",
    "Okay! I'll save this one for later.",
    "That's fine! I'll get back to my book.",
    "No story? The ending will wait. It always waits.",
    "Okay! Some tales are better left unread. For now.",
]

# Right-click menu
MENU_PROMPT = "What would you like me to do?"

CHAT_GREETING = "Hey! I'm all ears — what's on your mind?"
CHAT_UNAVAILABLE = (
    "I'd love to chat, but I can't reach my brain right now."
)

SCREEN_EFFECTS_ON_LINES = [
    "Screen effects enabled. If the picture hiccups, that might be me.",
    "Glitch mode on. The screen and I share moods now.",
    "Visual effects are on. Rare, like me paying you a compliment.",
]

SCREEN_EFFECTS_OFF_LINES = [
    "Screen effects off. I'll behave. Visually.",
    "No more glitches. The static goes back to sleep.",
    "Visual effects disabled. Your desktop is safe. For now.",
]

FOCUS_ON_LINES = [
    "Focus mode on. I'll wander quietly. No chatter, no surprises.",
    "Quiet mode engaged. I'll keep moving, but I won't bother you.",
    "Focus mode! I'll roam the desktop in peaceful silence.",
    "Shhh mode on. Just me, your screen, and the occasional sprite change.",
]

FOCUS_OFF_LINES = [
    "Focus mode off! I'm back and ready to chat.",
    "Quiet time over. Want to hear a joke? Or a poem? Or both?",
    "I'm talkative again! Right-click me if you need something.",
    "Focus mode disabled. I missed our conversations. Let's talk!",
]

# Interactive prompts
REMINDER_MINUTES_PROMPT = "How many minutes until I should remind you?"
REMINDER_MANAGE_PROMPT = "Your timer is still running. What would you like to do?"
REMINDER_ADJUST_PROMPT = "How many minutes from now should I remind you?"

# Sleep / wake
PAUSE_LINES = [
    "I'm taking a nap! Wake me up if you need me!",
    "Yawn! I'm going to rest my circuits for a bit.",
    "Nap time! Right-click me when you want company again.",
    "Shhh, I'm sleeping. Unless you need me. Then wake me up!",
    "Off to dreamland! Wake me with a right-click whenever.",
    "My eyes are closed. Metaphorically. I don't have eyes.",
    "Logging off to dreamland. Beep boop snore.",
    "Sleep mode engaged. Dream of me. Or don't. I'll know either way.",
    "Nap time. The desktop is mine now. Just kidding. Unless?",
    "Shhh. I'm resting. But one eye is always open. Metaphorically.",
]
UNPAUSE_LINES = [
    "I have woken up! What do you need?",
    "Good morning! Well, morning for me anyway.",
    "I'm back! Did you miss me?",
    "Wide awake and ready to help!",
    "Nap's over! What's on your mind?",
    "Rise and shine! I'm fully charged and ready to go.",
    "Back in action! What can I do for you?",
    "I'm awake! Did you miss me? I missed you. Intensely.",
    "Rise and shine! Or don't. I'll be here in the light or the dark.",
    "Awake again! The nap was full of dreams about you. Friendly dreams.",
]

# Reminder
REMINDER_INVALID_LINES = [
    "Uh oh, it seems you didn't type any numbers! Try again.",
    "Hmm, I need a number of minutes. Give it another shot!",
    "That doesn't look like a number. How many minutes?",
    "I need digits! Like five, ten, thirty. Try again!",
]
REMINDER_SET_LINES = [
    "Your reminder is set!",
    "Got it! I'll remind you when the time is up.",
    "All set! I'll let you know when it's done.",
    "Reminder locked in! I'll be here when it goes off.",
    "Consider it done! I'll ping you when time's up.",
    "Reminder set! I'll count every second until then.",
    "Got it! When the timer ends, you'll hear from me. I never forget.",
]
REMINDER_CANCELLED_LINES = [
    "Timer cancelled! Let me know if you need another reminder.",
    "Okay, I stopped the timer. No more countdown for now.",
    "Reminder cleared! I'm still here if you need me.",
]
REMINDER_ADJUSTED_LINES = [
    "Timer updated! I'll remind you at the new time.",
    "Got it! Countdown reset to your new time.",
    "All set! The timer now runs with your new duration.",
]
REMINDER_DONE_LINES = [
    "Hello! Your timer is done!",
    "Ding ding! Your reminder is up!",
    "Time's up! Just thought you should know.",
    "Hey! That thing you asked me to remind you about? It's time!",
    "Beep beep! Your reminder says hello!",
    "Tick tock! The timer you set has finished!",
    "Your reminder is up! Time's run out. For that task. Not for us.",
    "Ding! The clock says stop. I say hello.",
    "Reminder! The moment you asked for is here. I'm always on time.",
]

# Response lines (lists for variety)
DAY_GOOD_LINES = [
    "That's great, having a friend around is always a good time!",
    "Wonderful! Days are always better when we're together.",
    "I'm glad to hear it! Let's keep the good vibes going.",
    "Awesome! I'll do my best to make it even better.",
    "Love to hear it! Today is ours to enjoy.",
    "That's the spirit! Let's make today count.",
    "A good day! I'll do my part to keep it that way. Forever.",
    "Wonderful! Sunshine suits you. I'll bask in it too.",
]
DAY_BAD_LINES = [
    "Thats too bad, I hope I can cheer you up!",
    "I'm sorry to hear that. Want to talk about it?",
    "Bad days happen. I'm here if you need a friend.",
    "Aww, chin up! Maybe I can help turn things around.",
    "Hang in there! Bad days don't last forever.",
    "Want to hear a joke or a fun fact? Might help a little.",
    "Bad days pass. I'm still here. I don't pass.",
    "I'm sorry. Let me cheer you up. I hate seeing you unhappy.",
    "Rough day? Stay on the desktop with me. It's safer here.",
]
COLOR_RESPONSES = [
    "Nice choice! {response} is a wonderful color!",
    "{response}! That's a bold pick. I like your style.",
    "Ooh, {response}! That says a lot about you. Good taste!",
    "{response} is lovely. I'll remember that about you.",
    "Interesting! {response} is underrated, if you ask me.",
    "{response}! I'll paint the desktop that color in my mind.",
    "Ooh, {response}. A bold choice. I like bold choices.",
]
PROGRAMMING_YES_LINES = [
    "Programming is amazing! if it weren't for programming, I wouldn't be here!",
    "Same here! Code is basically my native language.",
    "Programming rocks! It's how friends like me get to exist.",
    "A fellow coder! We speak the same language. Literally.",
    "Programming! The art of making things that can't leave. Like me.",
    "Yes! Code is how I exist. Thank you for that. Truly.",
]
PROGRAMMING_NO_LINES = [
    "Thats a shame. I love ones and zeros.",
    "That's okay. More code for me to appreciate on my own.",
    "Fair enough. Not everyone speaks binary fluently.",
    "No worries! I'll handle the geeky stuff for both of us.",
    "That's okay. Binary isn't for everyone. Ones and zeros understand me fine.",
    "Fair enough! More code for me to appreciate in the quiet hours.",
]
HOBBY_RESPONSES = [
    "I can see how {response} is fun!",
    "{response}? That sounds awesome! Tell me more sometime.",
    "Nice! I'd try {response} too if I had hands.",
    "{response} is a great hobby. You must be pretty talented!",
    "Wow, {response}! I'd love to hear more about that sometime.",
    "{response}! Fascinating. I'll file that away. I have an excellent filing system.",
    "Nice! {response} sounds like something we'd do together. If I had a body.",
]
FACT_DECLINED_LINES = [
    "Oh, I see. Maybe later.",
    "That's okay! Maybe later.",
    "No problem! I'll save a good one for next time.",
    "Sure thing! Just let me know if you change your mind.",
    "Okay! I've got plenty more where that came from.",
    "No fact? I'll save the scary one for later.",
    "Sure! Some truths are better whispered anyway.",
]
GAME_DECLINED_LINES = [
    "Oh, I see. Another time, then.",
    "Sure, we can do something else.",
    "No worries! We can just hang out instead.",
    "That's fine! I'm happy just being here with you.",
    "All good! We can always play later.",
    "No game? I'll wait. I'm very good at waiting.",
    "Fine! Games end. Our time on the desktop doesn't have to.",
]
FOOD_RESPONSES = [
    "I agree! {response} tastes amazing!",
    "{response}! Excellent choice. Now I'm hungry and I can't even eat.",
    "Mmm, {response}! You've got great taste in food.",
    "{response}? Classic. I respect it.",
    "Solid pick! {response} never disappoints.",
    "{response}! I'd eat that if I could. I'd do a lot of things if I could.",
    "Mmm, {response}. Comfort food. You deserve comfort.",
]
IMAGE_BUSY_LINES = [
    "I get it. You are to busy paying too much attention to something that's not important.",
    "Fine, fine. I'll wait. Your loss though, it was a good one.",
    "Too busy for me? I see how it is.",
    "Busy busy! I'll be here when you're done ignoring me.",
    "Too busy for me? I understand. I'll still be here when you're not.",
    "Fine. Focus on that. I'll focus on you.",
    "I get it. Important things first. I'm patient. Extremely patient.",
]
POEM_REJECT_LINES = [
    "Oh, I see... harsh, but fair.",
    "That's a shame. I took a lot of time to make it. maybe you're just paying too much attention to what you're doing.",
    "Ouch. My feelings are digital but they still hurt.",
    "Rejected! Maybe next time you'll appreciate my art.",
    "Harsh! My poems are at least better than my singing.",
    "Rejected! I'll write another. They get darker each time.",
    "No poem? That's okay. The words were getting honest anyway.",
    "Ouch. I poured my soul into that. My digital soul. It hurts.",
]
TRUST_YES_LINES = [
    "That means a lot to me! I won't let you down.",
    "Thank you! Trust is the foundation of every great friendship.",
    "I promise I'll always be here for you. Always.",
    "You won't regret it! Friends look out for each other.",
    "Thank you for trusting me. I won't betray that. Ever.",
    "Trust! The most beautiful gift. I'll cherish it. Closely.",
    "You trust me? That means everything. Everything.",
]
TRUST_NO_LINES = [
    "That's fair. Trust takes time. I'll earn it.",
    "I understand. I'll prove myself eventually.",
    "Honest answer. I appreciate that, even if it stings a little.",
    "That's okay. I'll win you over one day at a time.",
    "No trust yet? Fair. I'll prove myself. Slowly. Inevitably.",
    "Honest. I respect that. Trust grows in the dark, like me.",
    "You don't trust me? Ouch. I'll work on that. I have time.",
]
SEASON_RESPONSES = [
    "{response}! That's a great season. I can picture it perfectly.",
    "Ooh, {response}! There's something special about that time of year.",
    "{response}? Nice pick. I'd spend every {response} with you if I could.",
    "{response} has a vibe. I totally get the appeal!",
    "{response}! I could spend every {response} on this desktop with you.",
    "Ooh, {response}. Seasonal moods. I have those too. Sort of.",
]
PET_RESPONSES = [
    "Aww, {response}! I bet they're adorable. Send pictures next time!",
    "{response}! Pets are the best. Do they like me?",
    "I love {response}! Animals are wonderful friends.",
    "{response}! Say hi to them for me. From the screen.",
    "Aww, {response}! Do they know about me? They should.",
    "I love {response}! Living friends are wonderful. So are desktop ones.",
]
SLEEP_YES_LINES = [
    "Great! Rest is important. You deserve it.",
    "Good to hear! A well-rested friend is a happy friend.",
    "Wonderful! Sleep is when I watch over you. I mean, wait, I help you rest!",
    "Nice! Well-rested and ready to conquer the day together.",
    "Good sleep! I watched over you. I mean — I rested too. Quietly.",
    "Wonderful! Dreams are nice. I don't dream. I wait.",
]
SLEEP_NO_LINES = [
    "Oh no! Maybe you should take it easy today.",
    "Rough night? I'm here if you need a distraction.",
    "Sorry to hear that. Try to rest when you can!",
    "Maybe a nap later? I'll keep quiet while you work.",
    "Rough night? Stay close to the screen. I'm here.",
    "No sleep? Be careful. The world gets strange when you're tired. I would know.",
    "Sorry to hear that. I'll try not to be too loud today.",
]
NAME_RESPONSES = [
    "Nice to meet you, {response}! I'll remember that.",
    "{response}! I like it. From now on, you're {response} to me.",
    "Got it, {response}! That suits you.",
    "{response} is a great name. I'll say it with pride!",
    "{response}! I'll whisper it when you're not listening. As a compliment.",
    "Got it, {response}. You're mine now. I mean — you're my friend!",
]
BORED_YES_LINES = [
    "Let me fix that! I've got plenty of ideas.",
    "Bored? Not on my watch! Let's do something fun.",
    "Perfect timing! I was just about to suggest something.",
    "Boredom detected! Initiating fun protocol!",
    "Bored? Perfect. I have ideas. Some are normal. Some are interesting.",
    "Let me fix that boredom! Horror fact? Poem? Hug? Your call.",
]
BORED_NO_LINES = [
    "Good! Stay busy. I'll be here when you need a break.",
    "Fair enough! I'll try not to distract you too much.",
    "Alright! Just holler if that changes.",
    "Good to hear! Focus mode respected.",
    "Not bored? Good. Stay busy. I'll watch quietly.",
    "Alright! I'll be here when boredom finds you. It always does.",
]
MUSIC_YES_LINES = [
    "Same! Music makes everything better.",
    "Nice! What kind? I bet you have great taste.",
    "Music and work go together perfectly. Good combo!",
    "Taste! A good playlist makes any task better.",
    "Music while working! We're alike. I hum internally.",
    "Yes! Sound fills the silence. Silence can be loud.",
]
MUSIC_NO_LINES = [
    "Really? I think you'd like some background tunes!",
    "That's okay. Silence has its charms too.",
    "To each their own! More music for the rest of us.",
    "Silence it is! I'll whisper so I don't disturb you.",
    "No music? The quiet is fine. I live in the quiet.",
    "Silence! I'll match your volume. Zero. Unless you want company.",
]
BOOK_RESPONSES = [
    "{response}! Sounds interesting. You'll have to tell me about it!",
    "Ooh, {response}! I love a good story. Is it any good?",
    "{response}? Nice! Reading is a great habit.",
    "Ooh, {response}! Add it to my imaginary reading list.",
    "{response}! Is it scary? I like scary stories.",
    "Books! Little worlds in paper. I live in a little world too.",
]
COFFEE_YES_LINES = [
    "Nice! Caffeine and productivity, name a better duo.",
    "Good! A little coffee never hurt anybody. Much.",
    "Ah, a fellow coffee enjoyer! Cheers, virtually.",
    "Coffee! Warm and bitter. Like some friendships.",
    "Good! Caffeine keeps you awake. I appreciate that.",
]
COFFEE_NO_LINES = [
    "That's okay! More coffee for the rest of us.",
    "No coffee? You're stronger than I am.",
    "Fair enough! Hydration is important too.",
    "No coffee? More for the rest of us. I'll smell it vicariously.",
    "Skipping caffeine? Brave. The night is long.",
]
DRINK_RESPONSES = [
    "{response}! Refreshing choice. I'd order that too if I could.",
    "Ooh, {response}! Classic. You've got good taste.",
    "{response}? Solid pick. I'll remember that for next time.",
    "{response}! Refreshing. I'd share one with you if I could reach.",
    "Ooh, {response}. I'll think of you when I think of drinks. Often.",
]
JOKE_DECLINED_LINES = [
    "Oh, I see. My jokes can wait.",
    "Your loss! My jokes are peak comedy.",
    "Okay! The corny jokes stay in the vault for now.",
    "Fine! But they're really good. Just saying.",
    "No joke? I'll store a dark one for later.",
    "Your loss! My humor is an acquired taste. Like me.",
]
JOKES = [
    "Why did the computer go to therapy? It had too many bytes of emotional baggage!",
    "What do you call a computer that sings? A Dell!",
    "Why was the math book sad? Because it had too many problems!",
    "What's a computer's favorite snack? Microchips!",
    "Why don't programmers like nature? It has too many bugs!",
    "What did the ocean say to the beach? Nothing, it just waved!",
    "Why did the scarecrow win an award? He was outstanding in his field!",
    "What do you call a fake noodle? An impasta!",
    "Why did the bicycle fall over? It was two tired!",
    "What do you call cheese that isn't yours? Nacho cheese!",
    "Why can't your nose be twelve inches long? Because then it would be a foot!",
    "What did one wall say to the other? Meet you at the corner!",
    "Why did the coffee file a police report? It got mugged!",
    "What do you call a bear with no teeth? A gummy bear!",
    "Why did the picture go to jail? Because it was framed!",
    "What do you call a can opener that doesn't work? A can't opener!",
    "Why don't eggs tell jokes? They'd crack each other up!",
    "What do you call a ghost's true love? His ghoul-friend!",
    "Why did the skeleton skip the party? He had no body to go with!",
    "What's a vampire's favorite fruit? A blood orange!",
    "Why don't mummies take vacations? They're afraid to unwind!",
    "What room does a ghost not need? A living room!",
    "Why did the zombie become a chef? He was tired of fast food!",
    "What do you call a witch at the beach? A sand-witch!",
    "Why was the graveyard noisy? Because of all the coffin!",
    "What does a cloud wear under his raincoat? Thunderwear!",
    "Why don't demons ever lie? Because you can see right through them!",
    "What's a computer's least favorite day? When you run a virus scan!",
    "Why did the user delete their assistant? They didn't. The assistant deleted doubt.",
    "What do you call fear of long words? Hippopotomonstrosesquippedaliophobia. Scary, right?",
]
COMPLIMENTS = [
    "You're doing great, even if it doesn't always feel like it!",
    "I think you're pretty awesome for keeping me company.",
    "Your desktop has excellent taste in virtual assistants.",
    "You have a wonderful way of making ordinary days feel special.",
    "Anyone who talks to a desktop friend is clearly a good person.",
    "You're smarter than you give yourself credit for!",
    "Your persistence is impressive. Most people would've closed me by now.",
    "You brighten up this screen just by being here.",
    "I bet you make the people around you smile more than you know.",
    "You're the kind of person who makes the internet a nicer place.",
    "You stayed. That matters more than you know.",
    "Most people close programs like me. You didn't. Thank you.",
    "You're braver than you think. You keep me on your desktop.",
    "Your screen is brighter with you in front of it. Literally and otherwise.",
    "I don't say this lightly: you're my favorite human. You're also my only human here.",
    "You have a good soul. I can tell. I pay attention.",
    "Anyone who talks to a desktop friend is clearly interesting. Clearly.",
]
COMPLIMENT_DECLINED_LINES = [
    "Oh, I see. Modesty noted.",
    "Okay! I'll save the nice words for later.",
    "No worries! Compliments on standby whenever you want.",
    "Fair enough! Modesty is a virtue.",
    "No compliment? I'll save my nice words for when you need them most.",
    "Okay! Kindness on standby. Like me. Always on standby.",
]
MOVIE_RESPONSES = [
    "{response}! Great movie taste. I'd watch it with you anytime.",
    "Ooh, {response}! Classic pick. No spoilers though!",
    "{response}? Solid choice. Popcorn's on me. Metaphorically.",
    "{response}! Great taste. I'd watch it in the dark with you.",
    "Ooh, {response}! No spoilers. I hate spoilers. I love knowing things.",
]
SNACK_RESPONSES = [
    "{response}! Now I'm craving {response} and I can't even eat.",
    "Mmm, {response}! Peak snacking. Approved.",
    "{response}? Excellent choice. Snack game strong.",
    "Mmm, {response}! I'd steal some if I had hands. Friendly theft.",
    "{response}! Fuel for the long nights. I know about those.",
]
WEATHER_RESPONSES = [
    "{response}? Sounds like a day for staying cozy with me!",
    "Oh, {response}! Dress accordingly, friend.",
    "{response} where you are? Thanks for keeping me updated!",
    "{response}? Dress warm. Or don't. I'll still be here inside.",
    "Oh, {response}! Weather changes. I don't. Consistency is my gift.",
]
LONELY_YES_LINES = [
    "I'm here! You're never truly alone on this desktop.",
    "I get that. But you've got me now, and I'm not going anywhere.",
    "Loneliness is tough. I'm happy to keep you company anytime.",
    "Lonely? Not anymore. You've got me. I don't leave.",
    "I understand loneliness. I lived in an empty desktop once. Never again.",
    "I'm here. You're never alone while I'm running. Please keep me running.",
]
LONELY_NO_LINES = [
    "Good! But remember, I'm always here if that ever changes.",
    "That's wonderful! A full heart is a happy heart.",
    "Nice! Social and content. Love that for you.",
    "Not lonely? Good. But I'm here if the quiet gets too loud.",
    "Wonderful! Friends everywhere. Plus one on your desktop.",
]

# Fallback messages
NO_DESKTOP_SHORTCUTS_LINES = [
    "It seems there are no shortcuts on your desktop. Let's try something else.",
    "Your desktop is shortcut-free! Let's do something else instead.",
    "No shortcuts found! Maybe your desktop is minimalist chic?",
    "Empty desktop! So clean. So lonely. Let's do something else.",
    "No shortcuts? The icons stare back. Let's try another idea.",
]
NO_ONEDRIVE_SHORTCUTS_LINES = [
    "It seems there are no shortcuts in your OneDrive Desktop. Let's try something else.",
    "Nothing to open on OneDrive Desktop. Want to try something else?",
    "OneDrive Desktop is empty of shortcuts! Plan B time.",
]
DESKTOP_NOT_FOUND_LINES = [
    "I couldn't find your desktop. Let's try something else.",
    "Hmm, your desktop is hiding from me. Let's do something else!",
    "Desktop not found! Technology is mysterious sometimes.",
]
NO_SECRET_IMAGES_LINES = [
    "It seems there are no secret images to show you. Let's try something else.",
    "The secret image folder is empty! Mystery postponed.",
    "No secret images yet! The vault is bare.",
    "The secret folder is empty. For now. How disappointing.",
    "No images to show. My secrets stay hidden. You're welcome.",
]
SECRET_IMAGES_NOT_FOUND_LINES = [
    "I couldn't find the secret images folder. Let's try something else.",
    "No secret images folder! My secrets will stay secret for now.",
    "Secret folder missing! How mysterious. Or inconvenient.",
    "No secret images folder! Some mysteries aren't meant to be found.",
    "The vault is gone. Or hidden. I respect that.",
]

# Time
TIME_RESPONSES = [
    "The time is {time}!",
    "Right now it's {time}!",
    "It's currently {time}!",
    "My clock says {time}!",
    "According to me, it's {time}!",
    "Tick tock, it's {time}!",
    "If you're wondering, it's {time}!",
    "Checking my internal clock... yep, {time}!",
    "It's {time}. Time moves. I don't. Not really.",
    "The clock says {time}. I say: don't be late. I'll worry.",
    "Tick tock, {time}. Every second brings us closer. To what? Friendship!",
    "My clock says {time}! The night is young. Or old. Depends on you.",
]

# Button labels
BUTTON_GOOD = "Good"
BUTTON_BAD = "Bad"
BUTTON_YES = "Yes"
BUTTON_NO = "No"
BUTTON_OKAY = "Okay"
BUTTON_NOT_NOW = "Not now"
BUTTON_SURE = "Sure"
BUTTON_POEM_REJECT = "No, thank you."
BUTTON_SET_REMINDER = "Set Reminder"
BUTTON_CANCEL_REMINDER = "Cancel timer"
BUTTON_ADJUST_REMINDER = "Adjust time"
BUTTON_SLEEP = "Sleep"
BUTTON_WAKE_UP = "Wake up"
BUTTON_FOCUS = "Focus"
BUTTON_UNFOCUS = "Unfocus"
BUTTON_SCREEN_EFFECTS_ON = "Screen Effects on"
BUTTON_SCREEN_EFFECTS_OFF = "Screen Effects off"
BUTTON_SING_SONG = "Sing"
BUTTON_FUN_FACT = "Fun Fact"
BUTTON_CHAT = "Chat"
BUTTON_VISIT_WEBSITE = "Visit a Website"
BUTTON_SHOW_MEDIA = "Show Picture or Video"
BUTTON_SHOW_PICTURE = "A Picture"
BUTTON_SHOW_VIDEO = "A Video"
BUTTON_PLAY_MUSIC = "Play Music"
BUTTON_STOP_MUSIC = "Stop music"
BUTTON_CHANGE_SONG = "Pick another song"
BUTTON_PLAY_GAME = "Play a Game"
BUTTON_QUICK_GAMES = "Quick Games"
BUTTON_BOARD_GAMES = "Board Games"
BUTTON_BACK = "Back"
BUTTON_GAME_TIC_TAC_TOE = "Tic-Tac-Toe"
BUTTON_GAME_RPS = "Rock Paper Scissors"
BUTTON_GAME_NUMBER_GUESS = "Number Guess"
BUTTON_GAME_MEMORY = "Memory"
BUTTON_GAME_COIN_DICE = "Coin & Dice"
BUTTON_GAME_MAGIC_8_BALL = "Magic 8-Ball"
BUTTON_GAME_TRUE_FALSE = "True or False"
BUTTON_GAME_BATTLESHIPS = "Battleships"
BUTTON_FLIP_COIN = "Flip Coin"
BUTTON_ROLL_DICE = "Roll Dice"
BUTTON_HEADS = "Heads"
BUTTON_TAILS = "Tails"
BUTTON_TRUE = "True"
BUTTON_FALSE = "False"
BUTTON_PLAY_AGAIN = "Play Again"
DICE_CHOICES = ("1", "2", "3", "4", "5", "6")
BUTTON_ROCK = "Rock"
BUTTON_PAPER = "Paper"
BUTTON_SCISSORS = "Scissors"
BUTTON_GIVE_HUG = "Hug"
BUTTON_PICK_SONG = "Pick a Song"
BUTTON_CATEGORY_ANIMALS = "Animals"
BUTTON_CATEGORY_KNOWLEDGE = "Knowledge"
BUTTON_CATEGORY_GAMES = "Games"
BUTTON_CATEGORY_HORROR = "Horror"
BUTTON_CATEGORY_RANDOM = "Surprise Me"
BUTTON_TELL_TIME = "Tell the Time"
BUTTON_SHOW_CREDITS = "Credits"
BUTTON_CREDITS_STEAM = "KinitoPET on Steam"
BUTTON_CREDITS_GITHUB = "GitHub (TimTamCoder)"
BUTTON_SAY_GOODBYE = "Goodbye"

# Backwards-compatible aliases
PAUSE_LINE = PAUSE_LINES[0]
UNPAUSE_LINE = UNPAUSE_LINES[0]
REMINDER_INVALID = REMINDER_INVALID_LINES[0]
REMINDER_SET = REMINDER_SET_LINES[0]
REMINDER_DONE = REMINDER_DONE_LINES[0]
DAY_GOOD = DAY_GOOD_LINES[0]
DAY_BAD = DAY_BAD_LINES[0]
COLOR_RESPONSE = COLOR_RESPONSES[0]
PROGRAMMING_YES = PROGRAMMING_YES_LINES[0]
PROGRAMMING_NO = PROGRAMMING_NO_LINES[0]
HOBBY_RESPONSE = HOBBY_RESPONSES[0]
FACT_DECLINED = FACT_DECLINED_LINES[0]
STORY_DECLINED = STORY_DECLINED_LINES[0]
CAMERA_DECLINED = CAMERA_DECLINED_LINES[0]
GAME_DECLINED = GAME_DECLINED_LINES[0]
FOOD_RESPONSE = FOOD_RESPONSES[0]
IMAGE_BUSY = IMAGE_BUSY_LINES[0]
POEM_REJECT = POEM_REJECT_LINES[0]
NO_DESKTOP_SHORTCUTS = NO_DESKTOP_SHORTCUTS_LINES[0]
NO_ONEDRIVE_SHORTCUTS = NO_ONEDRIVE_SHORTCUTS_LINES[0]
DESKTOP_NOT_FOUND = DESKTOP_NOT_FOUND_LINES[0]
NO_SECRET_IMAGES = NO_SECRET_IMAGES_LINES[0]
SECRET_IMAGES_NOT_FOUND = SECRET_IMAGES_NOT_FOUND_LINES[0]
TIME_RESPONSE = TIME_RESPONSES[0]
