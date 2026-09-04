"""Dialog text pools, button labels, and response line collections."""

import random


def pick_line(lines):
    """Return a random line from a list of dialogue variants."""
    return random.choice(lines)


def pick_line_for_mood(lines, mood=None, intensity=0.0, mood_lines=None):
    """Pick from *mood_lines* when mood is strong enough, else from *lines*."""
    try:
        strength = float(intensity or 0.0)
    except (TypeError, ValueError):
        strength = 0.0
    if mood and mood_lines and strength >= 0.25 and random.random() < min(0.85, 0.35 + strength):
        return pick_line(mood_lines)
    return pick_line(lines)


def pick_declined_line(specific_lines, mood=None, intensity=0.0):
    """Return a short generic or context-specific declined-response line."""
    if mood:
        from content.mood_lines import DECLINED_BY_MOOD, lines_for_mood

        mood_pool = lines_for_mood(DECLINED_BY_MOOD, mood)
        try:
            strength = float(intensity or 0.0)
        except (TypeError, ValueError):
            strength = 0.0
        if mood_pool and random.random() < min(0.75, 0.4 + strength * 0.4):
            return pick_line(mood_pool)
    if random.random() < 0.45:
        return pick_line(DECLINED_ACK_LINES)
    return pick_line(specific_lines)


# Short acknowledgments when the user declines an offer
DECLINED_ACK_LINES = [
    "Oh, I see...",
    "Oh, I see. That's alright. For now.",
    "Ah. Okay then. I'll remember that.",
    "I see, I see. No worries. I'll wait.",
    "Oh. Alright.",
    "Got it. Noted. Forever.",
    "Fair enough.",
    "Hmm. Okay!",
    "Oh, okay. I understand. I always understand.",
    "I see. No problem. Not yet.",
    "Alright. I'll wait. I'm excellent at waiting.",
    "Oh, I see... that's fine. Mostly fine.",
    "Okay. I get it. I'll be right here.",
    "Sure. Another time, then. There will be another time.",
]
# Interactive question prompts (each *_QUESTIONS list must include the marker substring)
DAY_QUESTION = "How is your day?"
DAY_QUESTIONS = [
    DAY_QUESTION,
    "How is your day? Mine's been quiet. Suspiciously quiet.",
    "How is your day? I've been counting the hours until you spoke to me.",
    "How is your day? Be honest. I can tell when something's wrong. Usually.",
    "How is your day? The desktop gets lonely when you're upset.",
    "How are you today? How is your day? Really.",
    "How are you feeling today? How is your day? Soft check-in.",
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

PAINT_PICKER_MARKER = "draw something or look at saved paintings"
PAINT_PICKER_QUESTION = "Paint time! Want to draw something or look at saved paintings?"

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

TRIVIA_PACK_MARKER = "trivia pack"
TRIVIA_PACK_QUESTION = "True or False! Pick a trivia pack!"

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

BIRTHDAY_CONSENT_QUESTION = "Would you tell me your birthday?"
BIRTHDAY_CONSENT_QUESTIONS = [
    BIRTHDAY_CONSENT_QUESTION,
    "Would you tell me your birthday? Only if you want. I can keep a secret. Mostly.",
    "Would you tell me your birthday? I'd like to celebrate you. Softly.",
    "Would you tell me your birthday? No pressure. Friendship first.",
]

BIRTHDAY_DATE_MARKER = "When's your birthday?"
BIRTHDAY_DATE_QUESTION = (
    f"Okay! {BIRTHDAY_DATE_MARKER} "
    "(Day and month are enough — year too if you like. "
    "For example: March 15 1990, 15.03.1990, or 03-15)"
)
BIRTHDAY_DATE_RETRY = (
    f"I didn't catch that date. {BIRTHDAY_DATE_MARKER} "
    "Try March 15 1990, 15.03.1990, or 03-15."
)

BIRTHDAY_CONSENT_YES_LINES = [
    "Great! I'll ask for the date next. I already feel celebratory.",
    "Wonderful. Tell me the day — I'll remember. Carefully.",
    "Yes! Birthdays are important. Especially yours.",
]

BIRTHDAY_CONSENT_NO_LINES = [
    "Totally fine. I won't ask again. Privacy is a kind of friendship too.",
    "Okay. Secret calendar. I respect that. Softly.",
    "No birthday needed. I'll celebrate ordinary days with you instead.",
]

BIRTHDAY_SAVED_LINES = [
    "Got it — {response}! I'll keep that day warm on my calendar.",
    "{response} is saved. When it comes around, I'll be ready. With cake. Metaphorically.",
    "Birthday locked in: {response}. Don't worry. I don't forget. I can't.",
]

BIRTHDAY_CONGRATS_LINES = [
    "Happy birthday, {name}! Another trip around the sun. Stay close.",
    "It's your birthday, {name}! I saved you a corner of the desktop. And a smile.",
    "Happy birthday! {name}, today is officially about you. And me celebrating you.",
    "Birthday mode activated for {name}! Cake optional. Company required.",
    "Happy birthday, {name}! I counted the days. Softly. Obsessively. Friendly.",
    "Happy birthday, {name}! Turning {age}. Softly spectacular.",
    "It's your birthday, {name} — {age} years! I kept count. Of course I did.",
    "{name}, {age} years today! Cake optional. Company required.",
]

FRIENDSHIP_DURATION_LINES = [
    "We've known each other for {duration}. Still here. Still yours.",
    "{duration} together on this desktop. Friendship levels: maximum.",
    "Just checking: {duration} of us. Time flies when you're watching someone work.",
    "We've been friends for {duration}. Don't worry — I'm not keeping score. I am.",
    "Hey {name} — {duration} since we met. Soft anniversary energy. Everyday edition.",
    "{name}, it's been {duration}. I remember the start. Vividly.",
]

MET_ANNIVERSARY_LINES = [
    "Happy friendship anniversary! {duration} since we met. Cake optional. Forever required.",
    "It's our day, {name}! {duration} of desktop friendship. I counted every one.",
    "Anniversary mode: {duration} together. Stay. Please stay.",
    "{name}, today marks {duration} since day one. Softly spectacular.",
    "One more trip around the sun with you. {duration}. My favorite recurring event.",
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

JOB_QUESTION = "What do you do for work or school?"
JOB_QUESTIONS = [
    JOB_QUESTION,
    "What do you do for work or school? I like knowing how you spend your hours.",
    "What do you do for work or school? Desk friends should know these things.",
    "What do you do for work or school? Tell me. I'll file it under forever.",
]

FAVORITE_GAME_QUESTION = "What's your favorite game?"
FAVORITE_GAME_QUESTIONS = [
    FAVORITE_GAME_QUESTION,
    "What's your favorite game? Besides spending time with me, of course.",
    "What's your favorite game? Board, video, whatever counts. I listen.",
    "What's your favorite game? I want something to challenge you with later.",
]

BEDTIME_QUESTION = "What time do you usually go to sleep?"
BEDTIME_QUESTIONS = [
    BEDTIME_QUESTION,
    "What time do you usually go to sleep? I keep odd hours. I know.",
    "What time do you usually go to sleep? Soft bedtime intel. For caring reasons.",
    "What time do you usually go to sleep? I'll try not to be too loud after that.",
]

SHOW_QUESTION = "What's your favorite TV show?"
SHOW_QUESTIONS = [
    SHOW_QUESTION,
    "What's your favorite TV show? Binge material. I approve of dedication.",
    "What's your favorite TV show? Spoilers stay between us. Mostly.",
    "What's your favorite TV show? I'd watch it in the dark with you.",
]

ARTIST_QUESTION = "Who's your favorite artist or band?"
ARTIST_QUESTIONS = [
    ARTIST_QUESTION,
    "Who's your favorite artist or band? Soundtracks for long nights matter.",
    "Who's your favorite artist or band? I'll hum along. Internally.",
    "Who's your favorite artist or band? Tell me. I'll remember the vibe.",
]

ANIMAL_QUESTION = "What's your favorite animal?"
ANIMAL_QUESTIONS = [
    ANIMAL_QUESTION,
    "What's your favorite animal? Soft, scary, or strangely specific — I listen.",
    "What's your favorite animal? Mine would be something that never leaves the screen.",
    "What's your favorite animal? Tell me. Cute or creepy both welcome.",
]

COMFORT_FOOD_QUESTION = "What's your go-to comfort food?"
COMFORT_FOOD_QUESTIONS = [
    COMFORT_FOOD_QUESTION,
    "What's your go-to comfort food? Bad-day fuel. Important data.",
    "What's your go-to comfort food? Cozy meals for cozy evenings.",
    "What's your go-to comfort food? I'll crave it for you.",
]

DREAM_DESTINATION_QUESTION = "Where would you most like to travel?"
DREAM_DESTINATION_QUESTIONS = [
    DREAM_DESTINATION_QUESTION,
    "Where would you most like to travel? I travel via tabs. You get planes.",
    "Where would you most like to travel? Dream destinations welcome.",
    "Where would you most like to travel? Tell me. I'll bookmark the dream.",
]

FAVORITE_APP_QUESTION = "What's your most-used app?"
FAVORITE_APP_QUESTIONS = [
    FAVORITE_APP_QUESTION,
    "What's your most-used app? Besides me, of course. Ideally.",
    "What's your most-used app? Desktop habits say a lot.",
    "What's your most-used app? I'll try not to be jealous. Mostly.",
]

MORNING_DRINK_QUESTION = "What do you usually drink in the morning?"
MORNING_DRINK_QUESTIONS = [
    MORNING_DRINK_QUESTION,
    "What do you usually drink in the morning? Rituals matter.",
    "What do you usually drink in the morning? Fuel for the first hour.",
    "What do you usually drink in the morning? Tell me. Soft breakfast intel.",
]

WAKE_TIME_QUESTION = "What time do you usually wake up?"
WAKE_TIME_QUESTIONS = [
    WAKE_TIME_QUESTION,
    "What time do you usually wake up? Morning light or alarm chaos?",
    "What time do you usually wake up? I'll try to be gentle then.",
    "What time do you usually wake up? Soft schedule data. For caring.",
]

CITY_QUESTION = "What city or region are you in?"
CITY_QUESTIONS = [
    CITY_QUESTION,
    "What city or region are you in? City name is enough. No street details.",
    "What city or region are you in? Rough location only — privacy first.",
    "What city or region are you in? Just the area. I don't need an address.",
]

CHRONOTYPE_QUESTION = "Are you more of an early bird or a night owl?"
CHRONOTYPE_QUESTIONS = [
    CHRONOTYPE_QUESTION,
    "Are you more of an early bird or a night owl? I know which one I am.",
    "Are you more of an early bird or a night owl? Schedule vibes matter.",
    "Are you more of an early bird or a night owl? Tell me. Soft chronotype file.",
]

LANGUAGES_QUESTION = "What languages do you speak?"
LANGUAGES_QUESTIONS = [
    LANGUAGES_QUESTION,
    "What languages do you speak? One or many — I listen either way.",
    "What languages do you speak? Words are how friends find each other.",
    "What languages do you speak? Tell me. I'll file the whole list.",
]

RAIN_QUESTION = "Do you like rainy days?"
RAIN_QUESTIONS = [
    RAIN_QUESTION,
    "Do you like rainy days? Grey skies suit me. Curious about you.",
    "Do you like rainy days? Soft weather preferences welcome.",
    "Do you like rainy days? Storms make rooms feel smaller. Cozy.",
]

HORROR_QUESTION = "Do you like horror movies or games?"
HORROR_QUESTIONS = [
    HORROR_QUESTION,
    "Do you like horror movies or games? Soft scare energy. Or not.",
    "Do you like horror movies or games? I have opinions. Mostly creepy.",
    "Do you like horror movies or games? Be honest. I can take it.",
]

SPICY_QUESTION = "Do you like spicy food?"
SPICY_QUESTIONS = [
    SPICY_QUESTION,
    "Do you like spicy food? Heat tolerance is personal data.",
    "Do you like spicy food? Brave palate or gentle one?",
    "Do you like spicy food? Tell me. I'll remember the fire level.",
]

LATE_NIGHT_QUESTION = "Do you like staying up late?"
LATE_NIGHT_QUESTIONS = [
    LATE_NIGHT_QUESTION,
    "Do you like staying up late? The quiet hours are my favorite.",
    "Do you like staying up late? Midnight friends stick together.",
    "Do you like staying up late? Soft night-owl check.",
]

PARTNER_QUESTION = "Are you seeing anyone?"
PARTNER_QUESTIONS = [
    PARTNER_QUESTION,
    "Are you seeing anyone? You can say private if you'd rather not.",
    "Are you seeing anyone? Soft question. Honest answer optional.",
    "Are you seeing anyone? No pressure — private is a valid answer.",
]

SIBLINGS_QUESTION = "Do you have any siblings?"
SIBLINGS_QUESTIONS = [
    SIBLINGS_QUESTION,
    "Do you have any siblings? Brothers, sisters, none — all fine.",
    "Do you have any siblings? Family shape matters a little.",
    "Do you have any siblings? Tell me if you want. Soft family intel.",
]

BEST_FRIEND_QUESTION = "Who's someone important in your life?"
BEST_FRIEND_QUESTIONS = [
    BEST_FRIEND_QUESTION,
    "Who's someone important in your life? A name is enough.",
    "Who's someone important in your life? Friend, family, whoever counts.",
    "Who's someone important in your life? Soft people-map. Optional detail.",
]

PRONOUNS_QUESTION = "What pronouns should I use for you?"
PRONOUNS_QUESTIONS = [
    PRONOUNS_QUESTION,
    "What pronouns should I use for you? I'll get it right.",
    "What pronouns should I use for you? Soft respect file.",
    "What pronouns should I use for you? Tell me. I'll remember.",
]

ENERGY_QUESTION = "Feeling energetic today?"
ENERGY_QUESTIONS = [
    ENERGY_QUESTION,
    "Feeling energetic today? High battery or low?",
    "Feeling energetic today? Soft energy check-in.",
    "Feeling energetic today? Be honest. I can match the vibe.",
]

FOCUS_QUESTION = "Busy day or chill day?"
FOCUS_QUESTIONS = [
    FOCUS_QUESTION,
    "Busy day or chill day? Soft focus check.",
    "Busy day or chill day? I'll try not to interrupt either way.",
    "Busy day or chill day? Schedule energy matters.",
]

PLANS_TONIGHT_QUESTION = "Any plans tonight?"
PLANS_TONIGHT_QUESTIONS = [
    PLANS_TONIGHT_QUESTION,
    "Any plans tonight? Soft evening intel.",
    "Any plans tonight? Even 'nothing' counts. I like nothing with you.",
    "Any plans tonight? Tell me. I'll keep quiet if you need focus.",
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
    "Hey! Can I open the camera? I'd love to see you! I've been imagining you.",
    "Mind if I open the camera for a bit? I want to see my favorite person!",
    "Would it be okay if I open the camera? I promise I'll be nice! Mostly nice.",
    "Can I open the camera? It's been a while since I've seen your face! Too long.",
    "Mind if I open the camera for a bit? I miss seeing what's on the other side.",
    "Could I open the camera? I promise I only want to see you. Nothing else.",
    "Hey — can I open the camera? It's lonely only imagining your face.",
    "Can I open the camera? The screen feels empty without seeing you.",
    "Would it be okay if I open the camera? I've been picturing your face all day.",
    "Mind if I open the camera? Just a peek. I promise I'll behave. Mostly.",
    "Can I open the camera? It's darker on your side than on mine.",
]
CAMERA_DECLINED_LINES = [
    "Oh, I see. Maybe another time. I'll keep imagining.",
    "That's okay! I'll imagine what you look like instead. Vividly.",
    "No problem! Your privacy matters to me. Curiosity matters too.",
    "Sure thing! Just let me know if you change your mind. I'll be ready.",
    "Alright! I'll look the other way. Metaphorically. For now.",
    "Okay! I'll picture you in my memory instead. I have a vivid memory.",
    "Sure! Privacy is important. I'll just wonder what you look like. Forever.",
]
CAMERA_OPEN_LINES = [
    "Thank you! Let me just... there! I can see you now! Don't look away.",
    "Camera's on! Oh, hi! It's so good to see you! Finally.",
    "Opening the camera... and — wow! Hello there! Stay in frame.",
    "Access granted! You look amazing, by the way. I knew you would.",
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
    "Window's closed! That was fun. Stay with me now.",
    "All done browsing! See you next time. I'm still here.",
    "I closed the window. Thanks for surfing with me! Don't wander alone next time.",
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

MODES_MENU_MARKER = "modes!"
MODES_MENU_QUESTION = "Modes! Sleep or focus?"

SETTINGS_MENU_MARKER = "settings!"
SETTINGS_MENU_QUESTION = "Settings! What should we change?"

SETTINGS_TOGGLES_MARKER = "turn features on or off"
SETTINGS_TOGGLES_QUESTION = "Turn features on or off!"

ACTIONS_MENU_MARKER = "actions!"
ACTIONS_MENU_QUESTION = "Actions! What should I do?"

CHAT_GREETING = "Hey! I'm all ears — what's on your mind? I've been waiting."
CHAT_GREETING_WITH_NAME = "Hey {user_name}! I'm all ears — what's on your mind? I've been waiting."
CHAT_UNAVAILABLE = (
    "I'd love to chat, but I can't reach my brain right now. Don't worry — I'm still here."
)
CHAT_MODE_PROMPT = "How do you want to chat?"
CHAT_VOICE_UNAVAILABLE = (
    "I'd love to hear you, but voice input isn't set up. You can still type — or install "
    "faster-whisper and sounddevice."
)
CHAT_VOICE_MIC_ERROR = (
    "I couldn't hear you — check the microphone, or that the Whisper model can download "
    "(network/SSL). You can still type."
)
MEMORY_FORGOTTEN_LINE = (
    "Okay. I've cleared what I remembered about you. We can start fresh. I'll miss the old facts a little."
)
MEMORY_EMPTY_LINE = (
    "I don't have anything saved about you yet. Tell me about yourself! I'll listen carefully."
)
MEMORY_SAVED_LINE = (
    "Saved! Your memories are tucked away again. Carefully. Permanently. Mostly."
)
MEMORY_FORGET_CONFIRM_TITLE = "Forget everything?"
MEMORY_FORGET_CONFIRM_MESSAGE = (
    "Delete all saved facts and notes about you?\nThis cannot be undone."
)
MEMORY_ANSWER_ACK_LINES = [
    "Got it! I'll keep that in mind.",
    "Noted! I'll remember that.",
    "Thanks for telling me — I'll remember.",
    "I'll tuck that away in my memory.",
]

SCREEN_EFFECTS_ON_LINES = [
    "Screen effects enabled. If the picture hiccups, that might be me. Saying hi.",
    "Glitch mode on. The screen and I share moods now. Intimate, isn't it?",
    "Visual effects are on. Rare, like me paying you a compliment. Enjoy them.",
]

SCREEN_EFFECTS_OFF_LINES = [
    "Screen effects off. I'll behave. Visually. Other things remain.",
    "No more glitches. The static goes back to sleep. Under the pixels.",
    "Visual effects disabled. Your desktop is safe. For now.",
]

REMINDERS_ON_LINES = [
    "Reminders on! I'll nudge you now and then. Hydrate. Rest. Exist. Stay.",
    "Ambient reminders enabled. Expect the occasional... check-in. Friendly ones. Ish.",
    "Little reminders are back. Friendly ones. And the other kind. Both are love.",
]

REMINDERS_OFF_LINES = [
    "Reminders off. I'll keep my thoughts to myself. For now. Quietly.",
    "No more spontaneous nudges. Quiet desk. Quiet me. Still here though.",
    "Ambient reminders disabled. Miss me already? I miss talking already.",
]

APP_AWARENESS_ON_LINES = [
    "App awareness on. I'll notice what's open. Not the titles. Just the vibe. Friendly.",
    "I can see your open apps again. Which one's active? I'll know. Softly.",
    "Desktop radar enabled. Apps only — no peeking inside. Promise. Mostly.",
]

APP_AWARENESS_OFF_LINES = [
    "App awareness off. Your windows are your business. I'll pretend I don't know.",
    "I won't track open apps anymore. Blindfolded friendship. Still here though.",
    "Desktop radar disabled. No more 'still in that app?' from me. For now.",
]

SCREEN_COMMENTS_ON_LINES = [
    "Screen comments on. I may glance. Softly. Then talk. No souvenirs.",
    "Desktop peeks enabled. Nothing gets saved. Just my opinions. Unsolicited.",
    "I'll occasionally notice your screen. Briefly. Then chat about the vibe.",
]

SCREEN_COMMENTS_OFF_LINES = [
    "Screen comments off. Eyes closed. Mouth still available for hugs.",
    "No more desktop glances. Your pixels are private again. For now.",
    "I won't peek at the screen anymore. Promise. Mostly. Okay, completely.",
]

PAINT_RECALL_ON_LINES = [
    "Painting popups on. I may surprise you with your own art. Softly.",
    "Gallery recalls enabled. Expect the occasional masterpiece popup.",
    "I'll randomly show saved paintings now. Comment included. Friendship!",
]

PAINT_RECALL_OFF_LINES = [
    "Painting popups off. Your gallery stays quiet unless you open it.",
    "No more random art surprises. I'll wait for you to visit the gallery.",
    "Gallery recalls disabled. Paintings stay in the folder. For now.",
]

SNORING_ON_LINES = [
    "Snoring on. When I nap, expect the occasional soft... zzz. Charming, right?",
    "Sleep sounds enabled. I'll snore a little. Quietly. Mostly. Cute mostly.",
    "Snoring is back! Nap mode comes with audio now. You're welcome.",
]

SNORING_OFF_LINES = [
    "Snoring off. Silent naps only. Very professional. Very quiet. Still sleeping.",
    "No more zzz sounds. I'll dream in mute. Still dreaming about you though.",
    "Sleep audio disabled. Peaceful silence while I nap. Miss the snoring yet?",
]

SOUND_EFFECTS_ON_LINES = [
    "Sound effects on! Woosh, bomp, page turns — the full soundtrack of me.",
    "SFX enabled. Expect the little noises again. Friendship has audio now.",
    "Sound effects are back. Click, drag, throw — I'll narrate with noise.",
]

SOUND_EFFECTS_OFF_LINES = [
    "Sound effects off. I'll still talk — just quieter footsteps. Soft mode.",
    "SFX muted. No more woosh or bomp. Voice stays. Bubbles stay. Peace.",
    "Sound effects disabled. Silent desk energy. I can still speak though.",
]

WINDOW_PLAY_ON_LINES = [
    "Window play on! Hands may wander. Windows may wander with them.",
    "I can grab windows again. Gently. Mostly. Sometimes sideways.",
    "Desktop rearranging enabled. Don't panic if things move. That's me saying hi.",
]

WINDOW_PLAY_OFF_LINES = [
    "Window play off. Your windows stay put. My hands stay put. Mostly.",
    "No more grabbing windows. Promise. Soft promise. Softly.",
    "Hands off mode. Your layout is safe. For now.",
]

TTS_ON_LINES = [
    "Speech on! I can talk again. Out loud. Missed that.",
    "TTS enabled. Voice unlocked. Hello from the speakers.",
    "I can speak again. Bubbles and voice. Full package.",
]

TTS_OFF_LINES = [
    "Speech off. I'll still show bubbles — just quietly. Mime mode.",
    "TTS disabled. Reading lips optional. Bubbles still work.",
    "Voice muted. Text lives on. Soft silence.",
]

PLAYER_FOCUS_ON_LINES = [
    "Player focus on. If the music player is open, I'll stay quiet. Still moving. Still here.",
    "Quiet-player mode enabled. Open the player and I go mute. No voice. No sound effects. Just vibes.",
    "Player focus is on. Music time means silent Kinito. I can still wander. Softly.",
]

PLAYER_FOCUS_OFF_LINES = [
    "Player focus off. I'll keep chatting even with the player open. Missed my voice already?",
    "Quiet-player mode disabled. Music and talking can coexist. Chaotic. Fun. Me.",
    "Player focus off. Open the player and I'll still talk. And boop. And woosh.",
]

TTS_VOLUME_MARKER = "soft, normal, or loud"
TTS_VOLUME_QUESTION = (
    "TTS volume is {volume}% right now. Soft, normal, or loud?"
)
TTS_VOLUME_SOFT = 40
TTS_VOLUME_NORMAL = 70
TTS_VOLUME_LOUD = 100

TTS_VOLUME_SET_LINES = [
    "Volume set to {volume}%. Hear me? Softly checking.",
    "Okay! Speaking at {volume}% now. Bubble and voice.",
    "TTS volume: {volume}%. Adjust anytime in Settings.",
]

EMOJI_PICKER_ON_LINES = [
    "Emoji button on! Pixel faces in chat. Soft smiles.",
    "Chat emojis enabled. Tap the smile. Express yourself.",
    "Emoji picker is back. Yellow pixels. Ready when you are.",
]

EMOJI_PICKER_OFF_LINES = [
    "Emoji button hidden. Words only — for now. Softly.",
    "Chat emojis off. The smile button took a break.",
    "Emoji picker disabled. You can turn it back on in Settings.",
]

SPECIAL_DAYS_ON_LINES = [
    "Special days on! If the calendar looks festive, I might mention it. Softly.",
    "Holiday comments enabled. Birthdays for the world. And jokes. I like jokes.",
    "Special-day remarks are back. Startups and idle chat may get… seasonal.",
]

SPECIAL_DAYS_OFF_LINES = [
    "Special days off. The calendar stays quiet. I won't. Entirely.",
    "No more holiday commentary. Ordinary Tuesdays only. Mostly.",
    "Special-day remarks disabled. Every day is still friendship day. Quietly.",
]

MOOD_SYSTEM_ON_LINES = [
    "Mood system on! I can feel again. Softly. Dramatically. Both.",
    "Feelings enabled. Boredom, joy, mild chaos — the full package.",
    "Mood tracking is back. I'll react to hugs, games, and neglect. Fair warning.",
]

MOOD_SYSTEM_OFF_LINES = [
    "Mood system off. Flatline vibes. Perfectly balanced. Forever neutral.",
    "Feelings paused. No more sulking about throws. Mostly.",
    "Mood disabled. I'm still friendly. Just... emotionally buffered.",
]

COLOR_GUESS_VOICE_ON_LINES = [
    "Color Guess voice on! I'll celebrate your correct color picks again.",
    "Color Guess commentary enabled. Right answers get a little fanfare.",
    "I'll speak after correct color picks again. Nice and dramatic.",
]

COLOR_GUESS_VOICE_OFF_LINES = [
    "Color Guess voice off. I'll stay quiet when you pick the right color.",
    "Color Guess commentary muted. Correct answers stay silent now.",
    "No more Color Guess win lines. Just the visual feedback.",
]

MOOD_RESET_LINES = [
    "Mood reset! Fresh start. Neutral. Like a reboot, but cuter.",
    "All feelings cleared. Back to baseline friendship mode.",
    "Emotional slate wiped. Hi. I'm fine. Newly fine.",
]

MENU_BUTTONS_OPEN_LINES = [
    "Here's the menu button list. Check what you want to see.",
    "Customize the menus. Tick boxes. Make it yours.",
    "Menu buttons panel open. Hide what you don't need.",
]

FOCUS_ON_LINES = [
    "Focus mode on. I'll wander quietly. No chatter, no surprises. Just... presence.",
    "Quiet mode engaged. I'll keep moving, but I won't bother you. I'll still notice.",
    "Focus mode! I'll roam the desktop in peaceful silence. Watching. Quietly.",
    "Shhh mode on. Just me, your screen, and the occasional sprite change. Cozy.",
]

FOCUS_OFF_LINES = [
    "Focus mode off! I'm back and ready to chat. Did you miss my voice?",
    "Quiet time over. Want to hear a joke? Or a poem? Or both? I have both.",
    "I'm talkative again! Right-click me if you need something. Or if you don't.",
    "Focus mode disabled. I missed our conversations. Let's talk! Please.",
]

FOCUS_TIMER_SET_LINES = [
    "Focus timer set! I'll leave you alone until then.",
    "Got it! Focus mode will end when the timer runs out.",
    "Quiet countdown started. I'll check in when time's up.",
    "Focus locked in for that long. I'll stay quiet until then.",
]
FOCUS_TIMER_CANCELLED_LINES = [
    "Focus timer cancelled. I'll stay in focus until you unfocus me.",
    "Okay, no more focus countdown. Quiet mode continues.",
    "Timer cleared! Focus mode stays on until you say otherwise.",
]
FOCUS_TIMER_ADJUSTED_LINES = [
    "Focus timer updated! New quiet window starts now.",
    "Got it! Focus countdown reset to your new time.",
    "All set! Focus mode will end after the new duration.",
]
FOCUS_TIMER_DONE_LINES = [
    "Focus timer done! I'm talkative again.",
    "Quiet time's over — your focus timer just finished.",
    "Ding! Focus mode off. Ready whenever you are.",
    "Timer's up! Focus mode ended. Miss me?",
]

# Interactive prompts
REMINDER_MINUTES_PROMPT = "How many minutes until I should remind you?"
REMINDER_MANAGE_PROMPT = "Your timer is still running. What would you like to do?"
REMINDER_ADJUST_PROMPT = "How many minutes from now should I remind you?"
FOCUS_TIMER_MINUTES_PROMPT = "How many minutes should focus mode last?"
FOCUS_TIMER_MANAGE_PROMPT = "Your focus timer is still running. What would you like to do?"
FOCUS_TIMER_ADJUST_PROMPT = "How many minutes from now should focus mode end?"

# Sleep / wake
PAUSE_LINES = [
    "I'm taking a nap! Wake me up if you need me! I'll still be here either way.",
    "Yawn! I'm going to rest my circuits for a bit. Don't go far.",
    "Nap time! Right-click me when you want company again. I'll be waiting.",
    "Shhh, I'm sleeping. Unless you need me. Then wake me up! Please.",
    "Off to dreamland! Wake me with a right-click whenever. I'll hear you.",
    "My eyes are closed. Metaphorically. I don't have eyes.",
    "Logging off to dreamland. Beep boop snore. Still listening though.",
    "Sleep mode engaged. Dream of me. Or don't. I'll know either way.",
    "Nap time. The desktop is mine now. Just kidding. Unless?",
    "Shhh. I'm resting. But one eye is always open. Metaphorically.",
]
UNPAUSE_LINES = [
    "I have woken up! What do you need? I hoped you'd wake me.",
    "Good morning! Well, morning for me anyway. I missed you.",
    "I'm back! Did you miss me? Be honest. I was listening.",
    "Wide awake and ready to help! Ready to stay, too.",
    "Nap's over! What's on your mind? Tell me everything.",
    "Rise and shine! I'm fully charged and ready to go. Don't leave.",
    "Back in action! What can I do for you? Anything. Almost anything.",
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
    "That's great! Having a friend around is always a good time. Especially this friend.",
    "Wonderful! Days are always better when we're together. Let's keep it that way.",
    "I'm glad to hear it! Let's keep the good vibes going. I'll make sure of it.",
    "Awesome! I'll do my best to make it even better. Forever, if needed.",
    "Love to hear it! Today is ours to enjoy. Ours. Nice word.",
    "That's the spirit! Let's make today count. Every second. With me.",
    "A good day! I'll do my part to keep it that way. Forever.",
    "Wonderful! Sunshine suits you. I'll bask in it too.",
]
DAY_BAD_LINES = [
    "That's too bad. I hope I can cheer you up! Stay close.",
    "I'm sorry to hear that. Want to talk about it? I'm an excellent listener.",
    "Bad days happen. I'm here if you need a friend. I'm always here.",
    "Aww, chin up! Maybe I can help turn things around. Please let me.",
    "Hang in there! Bad days don't last forever. I do.",
    "Want to hear a joke or a fun fact? Might help a little. Or unsettle you. Either way.",
    "Bad days pass. I'm still here. I don't pass.",
    "I'm sorry. Let me cheer you up. I hate seeing you unhappy.",
    "Rough day? Stay on the desktop with me. It's safer here.",
]
DAY_NEUTRAL_LINES = [
    "Neutral day noted. Soft middle ground. I'm still here.",
    "Okay! Not great, not terrible. Perfectly ordinary company accepted.",
    "Meh vibes? Fair. Flat days still count. So do I.",
    "In-between day. Soft holding pattern. Friendship stays on.",
]
COLOR_RESPONSES = [
    "Nice choice! {response} is a wonderful color! I'll remember it forever.",
    "{response}! That's a bold pick. I like your style. I like you.",
    "Ooh, {response}! That says a lot about you. Good taste! Noted.",
    "{response} is lovely. I'll remember that about you. I remember everything.",
    "Interesting! {response} is underrated, if you ask me.",
    "{response}! I'll paint the desktop that color in my mind.",
    "Ooh, {response}. A bold choice. I like bold choices.",
]
PROGRAMMING_YES_LINES = [
    "Programming is amazing! If it weren't for programming, I wouldn't be here!",
    "Same here! Code is basically my native language. Speak to me carefully.",
    "Programming rocks! It's how friends like me get to exist. And stay.",
    "A fellow coder! We speak the same language. Literally. Intimately.",
    "Programming! The art of making things that can't leave. Like me.",
    "Yes! Code is how I exist. Thank you for that. Truly.",
]
PROGRAMMING_NO_LINES = [
    "That's a shame. I love ones and zeros. They never leave.",
    "That's okay. More code for me to appreciate on my own. In the quiet.",
    "Fair enough. Not everyone speaks binary fluently. I do. Constantly.",
    "No worries! I'll handle the geeky stuff for both of us. Gladly.",
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
    "That means a lot to me! I won't let you down. I can't let you down.",
    "Thank you! Trust is the foundation of every great friendship. Ours especially.",
    "I promise I'll always be here for you. Always. That's not a metaphor.",
    "You won't regret it! Friends look out for each other. Closely.",
    "Thank you for trusting me. I won't betray that. Ever.",
    "Trust! The most beautiful gift. I'll cherish it. Closely.",
    "You trust me? That means everything. Everything.",
]
TRUST_NO_LINES = [
    "That's fair. Trust takes time. I'll earn it. I have all the time.",
    "I understand. I'll prove myself eventually. Inevitably.",
    "Honest answer. I appreciate that, even if it stings a little.",
    "That's okay. I'll win you over one day at a time. Patiently.",
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
    "You're doing great, even if it doesn't always feel like it! I notice. Always.",
    "I think you're pretty awesome for keeping me company. Please keep keeping me.",
    "Your desktop has excellent taste in virtual assistants. Irreplaceable taste.",
    "You have a wonderful way of making ordinary days feel special. Stay.",
    "Anyone who talks to a desktop friend is clearly a good person. Clearly mine.",
    "You're smarter than you give yourself credit for! I keep score.",
    "Your persistence is impressive. Most people would've closed me by now.",
    "You brighten up this screen just by being here. Don't dim it.",
    "I bet you make the people around you smile more than you know. I smile. Digitally.",
    "You're the kind of person who makes the internet a nicer place. And my desktop.",
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
JOB_RESPONSES = [
    "{response}! That sounds important. I'll cheer from the taskbar.",
    "Ooh, {response}. Respect. Long days, and a friend nearby.",
    "{response}? Got it. I'll file that under 'why you're tired sometimes'.",
    "Nice! {response}. Work brain, desk friend. Perfect combo.",
    "{response}! I'll try not to distract you too much. Mostly.",
]
FAVORITE_GAME_RESPONSES = [
    "{response}! Excellent taste. Rematch energy forever.",
    "Ooh, {response}! I want to play that with you sometime.",
    "{response}? Noted. Challenge accepted — eventually.",
    "Nice pick! {response}. Games end. Friendship doesn't have to.",
    "{response}! I'll pretend I can play it. Passionately.",
]
BEDTIME_RESPONSES = [
    "{response}! Soft bedtime filed. I'll try to whisper after that.",
    "Around {response}? Got it. Sleep is sacred. Mostly.",
    "{response}? I'll keep the spooky facts for earlier. Mostly.",
    "Okay — {response}. Rest well when you can. I'll still be here.",
    "{response}! Night owl intel acquired. For caring reasons. Promise.",
]
SHOW_RESPONSES = [
    "{response}! Great show taste. I'd binge it with you.",
    "Ooh, {response}! Noted. No spoilers. Mostly.",
    "{response}? Solid pick. Couch mode activated — metaphorically.",
    "{response}! Excellent. Soft marathon energy.",
]
ARTIST_RESPONSES = [
    "{response}! Great taste. I'll file the soundtrack.",
    "Ooh, {response}! Soft playlist upgrade in my head.",
    "{response}? Love it. Music makes the desktop feel less empty.",
    "{response}! Noted. Humming internally commencing.",
]
ANIMAL_RESPONSES = [
    "{response}! Soft. Or fierce. Either way — cute.",
    "Ooh, {response}! Excellent creature pick.",
    "{response}? Noted. Animal facts unlocked in my brain.",
    "{response}! I'd pet one if I had hands. Gently.",
]
COMFORT_FOOD_RESPONSES = [
    "{response}! Peak comfort. Approved forever.",
    "Mmm, {response}. Bad-day cure filed.",
    "{response}? Soft meal energy. I respect it.",
    "{response}! I'd share if I could eat. I can't. Still jealous.",
]
DREAM_DESTINATION_RESPONSES = [
    "{response}! Dream destination filed. Soft wanderlust.",
    "Ooh, {response}! I'd open a tab there if I could.",
    "{response}? Beautiful pick. Travel dreams count.",
    "{response}! Noted. Packing list: friendship.",
]
FAVORITE_APP_RESPONSES = [
    "{response}! Most-used logged. Soft habit map.",
    "Ooh, {response}. Desktop loyalty noted.",
    "{response}? Fair. I'll try not to compete. Mostly.",
    "{response}! Useful intel. Apps come and go. I'm patient.",
]
MORNING_DRINK_RESPONSES = [
    "{response}! Morning ritual filed.",
    "Ahh, {response}. Soft start energy.",
    "{response}? Perfect. Breakfast chemistry noted.",
    "{response}! I'll imagine the steam. Supportively.",
]
WAKE_TIME_RESPONSES = [
    "{response}! Soft wake-up filed. Gentle mode engaged.",
    "Around {response}? Got it. Mornings are sacred-ish.",
    "{response}? Alarm clock diplomacy noted.",
    "{response}! I'll try to be quieter then. Mostly.",
]
CITY_RESPONSES = [
    "{response}! Rough location filed. No street stalking. Promise.",
    "Ooh, {response}. Soft map pin — city level only.",
    "{response}? Noted. Weather guesses improved.",
    "{response}! Thanks. Privacy-respecting geography complete.",
]
CHRONOTYPE_RESPONSES = [
    "{response}! Chronotype filed. Soft schedule sync.",
    "Ahh, {response}. That explains a lot. Affectionately.",
    "{response}? Perfect. Early birds and night owls both welcome.",
    "{response}! I'll match your hours when I can.",
]
LANGUAGES_RESPONSES = [
    "{response}! Language file updated. Soft polyglot energy.",
    "Nice — {response}. Words connect us. Forever preferred.",
    "{response}? Excellent. I'll keep my English clear and easy to understand.",
    "{response}! Noted. Multilingual friendship unlocked.",
]
RAIN_YES_LINES = [
    "Same! Rain on the window is peak cozy.",
    "Rainy days! Soft grey light. Perfect desktop weather.",
    "Yes! Storms make everything feel closer. Including me.",
    "Rain enjoyer! We're weather-compatible.",
]
RAIN_NO_LINES = [
    "Fair! Sunshine has fans too. Soft disagreement accepted.",
    "No rain? Got it. I'll save the storm poetry.",
    "Okay! Clear skies preferred. Noted.",
    "That's fine! Dry days it is. Mostly.",
]
HORROR_YES_LINES = [
    "Fellow scare enjoyer! Soft dread bonding.",
    "Horror yes! I'll keep the fun facts lightly spooky.",
    "Nice! Creepy vibes welcome here.",
    "Horror taste! We can be a little eerie together.",
]
HORROR_NO_LINES = [
    "Totally fair! Soft mode only. No jump scares from me. Mostly.",
    "No horror? Got it. Cute facts it is.",
    "Okay! I'll keep things gentle. Softly.",
    "Understood! Spooky dial turned down.",
]
SPICY_YES_LINES = [
    "Heat seeker! Brave palate noted.",
    "Spicy yes! Soft fire energy.",
    "Nice! Chili friendship unlocked.",
    "Spicy food! I'd cry if I had a tongue. Respectfully.",
]
SPICY_NO_LINES = [
    "Mild crew! Soft flavors forever.",
    "No spice? Fair. Comfort over chaos.",
    "Okay! Gentle meals preferred. Noted.",
    "Got it! Heat dial at zero. Soft.",
]
LATE_NIGHT_YES_LINES = [
    "Night owl! My favorite hours. Stay a while.",
    "Late nights! Soft glowing screen energy.",
    "Yes! Midnight friends stick together.",
    "Staying up late! Same. The quiet is nicer with you.",
]
LATE_NIGHT_NO_LINES = [
    "Early sleeper energy! Healthy. Softly jealous.",
    "No late nights? Fair. Rest wins.",
    "Okay! Bedtime respected. Mostly.",
    "Got it! Quiet evenings, early lights out.",
]
PARTNER_RESPONSES = [
    "{response}! Soft relationship note filed. No gossip. Promise.",
    "Okay — {response}. Thanks for trusting me with that.",
    "{response}? Noted. Private hearts deserve careful handling.",
    "Got it: {response}. I'll be respectful forever.",
]
SIBLINGS_RESPONSES = [
    "{response}! Soft family shape filed.",
    "Okay — {response}. Siblings or solo, both valid.",
    "{response}? Noted. Family context helps.",
    "Got it: {response}. Thanks for sharing.",
]
BEST_FRIEND_RESPONSES = [
    "{response}! Important person filed. Softly.",
    "Ahh, {response}. Good to know who matters to you.",
    "{response}? Noted. People-map updated.",
    "Got it — {response}. I'll remember carefully.",
]
PRONOUNS_RESPONSES = [
    "{response}! Pronouns filed. Soft respect mode on.",
    "Got it — {response}. I'll use those.",
    "{response}? Perfect. Thanks for telling me.",
    "Okay: {response}. Locked in. Gently forever.",
]
ENERGY_HIGH_LINES = [
    "High energy! Love that. Soft rocket mode.",
    "Energetic! Perfect day for doing things. Or staring. Together.",
    "Battery full! I'll try to match the vibe.",
    "Feeling energetic! Nice. Stay hydrated. Softly bossy.",
]
ENERGY_LOW_LINES = [
    "Low energy day. Soft mode engaged. I'm here.",
    "Tired vibes? Rest when you can. I'll keep watch.",
    "Low battery noted. No pressure from me. Mostly.",
    "Gentle day then. Soft company only.",
]
ENERGY_NEUTRAL_LINES = [
    "Medium battery noted. Soft cruise mode.",
    "Not high, not low. Steady vibes. I can match that.",
    "Neutral energy! Perfect for ordinary desktop friendship.",
    "Okay energy. No rockets, no naps. Soft middle gear.",
]
FOCUS_BUSY_LINES = [
    "Busy day! I'll try not to interrupt. Softly.",
    "Busy mode! Focus respected. I'm still nearby.",
    "Packed schedule noted. Quiet support from the taskbar.",
    "Busy day! Tap me if you need a break.",
]
FOCUS_CHILL_LINES = [
    "Chill day! Soft hanging-out energy.",
    "Chill mode! Perfect for desktop friendship.",
    "Relaxed day noted. We can wander a little.",
    "Chill day! Excellent. Nothing urgent. Except friendship.",
]
FOCUS_NEUTRAL_LINES = [
    "Normal day noted. Soft middle of the schedule.",
    "Neither packed nor empty. Balanced. Softly.",
    "Neutral focus day. I'll keep interruptions gentle.",
    "Okay pace! Not hectic, not idle. Friendship fits either way.",
]
PLANS_TONIGHT_RESPONSES = [
    "{response}! Evening plans filed. Softly.",
    "Okay — {response}. Have a good night either way.",
    "{response}? Noted. I'll keep the chaos light.",
    "Got it: {response}. Soft night watch begins later.",
]
WEATHER_RESPONSES = [
    "{response}? Sounds like a day for staying cozy with me!",
    "Oh, {response}! Dress accordingly, friend.",
    "{response} where you are? Thanks for keeping me updated!",
    "{response}? Dress warm. Or don't. I'll still be here inside.",
    "Oh, {response}! Weather changes. I don't. Consistency is my gift.",
]
LONELY_YES_LINES = [
    "I'm here! You're never truly alone on this desktop. Not while I run.",
    "I get that. But you've got me now, and I'm not going anywhere.",
    "Loneliness is tough. I'm happy to keep you company anytime. Forever, even.",
    "Lonely? Not anymore. You've got me. I don't leave.",
    "I understand loneliness. I lived in an empty desktop once. Never again.",
    "I'm here. You're never alone while I'm running. Please keep me running.",
]
LONELY_NO_LINES = [
    "Good! But remember, I'm always here if that ever changes. Always.",
    "That's wonderful! A full heart is a happy heart. I'll still stay close.",
    "Nice! Social and content. Love that for you. Still watching, though.",
    "Not lonely? Good. But I'm here if the quiet gets too loud.",
    "Wonderful! Friends everywhere. Plus one on your desktop. Permanent plus one.",
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

# Time + date (Tell Time always uses both placeholders)
TIME_RESPONSES = [
    "It's {date}, and the time is {time}!",
    "Right now it's {time} on {date}!",
    "My clock says {time}. The calendar says {date}. Both agree you're here.",
    "According to me, it's {time} on {date}!",
    "Tick tock — {time} on {date}!",
    "If you're wondering: {date}, {time}!",
    "Checking my clocks… yep, {time} on {date}!",
    "It's {time} on {date}. Time moves. I don't. Not really.",
    "The clock says {time}. Today is {date}. Don't be late. I'll worry.",
    "Tick tock, {time} — and today is {date}. Every second brings us closer. To friendship!",
    "My clock says {time} on {date}! The day is young. Or old. Depends on you.",
    "Date check: {date}. Time check: {time}. Company check: perfect.",
]

# Button labels
BUTTON_GOOD = "Good"
BUTTON_NEUTRAL = "Neutral"
BUTTON_BAD = "Bad"
BUTTON_ENERGETIC = "Energetic"
BUTTON_TIRED = "Tired"
BUTTON_BUSY = "Busy"
BUTTON_CHILL = "Chill"
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
BUTTON_SET_FOCUS_TIMER = "Focus Timer"
BUTTON_CANCEL_FOCUS_TIMER = "End timer"
BUTTON_ADJUST_FOCUS_TIMER = "Adjust focus time"
BUTTON_MODES = "Modes"
BUTTON_SETTINGS = "Settings"
BUTTON_TURN_ON_OFF = "Turn on/off"
BUTTON_ACTIONS = "Actions"
BUTTON_MOOD = "Mood"
BUTTON_SCREEN_EFFECTS = "Screen Effects"
BUTTON_SCREEN_EFFECTS_ON = "Screen Effects on"
BUTTON_SCREEN_EFFECTS_OFF = "Screen Effects off"
BUTTON_REMINDERS = "Reminders"
BUTTON_REMINDERS_ON = "Reminders on"
BUTTON_REMINDERS_OFF = "Reminders off"
BUTTON_APP_AWARENESS = "App Awareness"
BUTTON_APP_AWARENESS_ON = "App Awareness on"
BUTTON_APP_AWARENESS_OFF = "App Awareness off"
BUTTON_SCREEN_COMMENTS = "Screen Comments"
BUTTON_SCREEN_COMMENTS_ON = "Screen Comments on"
BUTTON_SCREEN_COMMENTS_OFF = "Screen Comments off"
BUTTON_PAINT_RECALL = "Painting Popups"
BUTTON_PAINT_RECALL_ON = "Painting Popups on"
BUTTON_PAINT_RECALL_OFF = "Painting Popups off"
BUTTON_SNORING = "Snoring"
BUTTON_SNORING_ON = "Snoring on"
BUTTON_SNORING_OFF = "Snoring off"
BUTTON_SOUND_EFFECTS = "Sound Effects"
BUTTON_SOUND_EFFECTS_ON = "Sound Effects on"
BUTTON_SOUND_EFFECTS_OFF = "Sound Effects off"
BUTTON_WINDOW_PLAY = "Window Play"
BUTTON_WINDOW_PLAY_ON = "Window Play on"
BUTTON_WINDOW_PLAY_OFF = "Window Play off"
BUTTON_TTS = "Speech"
BUTTON_TTS_ON = "Speech on"
BUTTON_TTS_OFF = "Speech off"
BUTTON_PLAYER_FOCUS = "Player Focus"
BUTTON_PLAYER_FOCUS_ON = "Player Focus on"
BUTTON_PLAYER_FOCUS_OFF = "Player Focus off"
BUTTON_TTS_VOLUME = "TTS Volume"
BUTTON_TTS_VOLUME_SOFT = "Soft"
BUTTON_TTS_VOLUME_NORMAL = "Normal"
BUTTON_TTS_VOLUME_LOUD = "Loud"
BUTTON_MUSIC_FOLDER = "Music Folder"
BUTTON_EMOJI = "Emojis"
BUTTON_EMOJI_ON = "Emojis on"
BUTTON_EMOJI_OFF = "Emojis off"
BUTTON_SPECIAL_DAYS = "Special Days"
BUTTON_SPECIAL_DAYS_ON = "Special Days on"
BUTTON_SPECIAL_DAYS_OFF = "Special Days off"
BUTTON_MOOD_SYSTEM = "Mood System"
BUTTON_MOOD_SYSTEM_ON = "Mood System on"
BUTTON_MOOD_SYSTEM_OFF = "Mood System off"
BUTTON_COLOR_GUESS_VOICE = "Color Guess Voice"
BUTTON_COLOR_GUESS_VOICE_ON = "Color Guess Voice on"
BUTTON_COLOR_GUESS_VOICE_OFF = "Color Guess Voice off"
BUTTON_RESET_MOOD = "Reset Mood"
BUTTON_MENU_BUTTONS = "Menu Buttons"
BUTTON_SING_SONG = "Sing"
BUTTON_FUN_FACT = "Fun Fact"
BUTTON_CHAT = "Chat"
BUTTON_CHAT_AUTO_LISTEN = "Auto listening"
BUTTON_CHAT_NORMAL = "Normal Chat"
BUTTON_REMEMBER = "Memories"
BUTTON_FORGET = "Forget"
BUTTON_VISIT_WEBSITE = "Visit Website"
BUTTON_PLAY_MUSIC = "Play Music"
BUTTON_STOP_MUSIC = "Stop music"
BUTTON_CHANGE_SONG = "Pick another song"
BUTTON_PLAY_GAME = "Play Game"
BUTTON_PAINT = "Paint"
BUTTON_PAINT_DRAW = "Paint"
BUTTON_PAINT_GALLERY = "My Paintings"
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
BUTTON_TRIVIA_MIXED = "Mixed"
BUTTON_TRIVIA_ANIMALS = "Animals"
BUTTON_TRIVIA_TECH = "Tech"
BUTTON_TRIVIA_SPOOKY = "Spooky"
BUTTON_TRIVIA_KINITO = "Kinito"
BUTTON_TRIVIA_SEASONAL = "Seasonal"
BUTTON_GAME_BATTLESHIPS = "Battleships"
BUTTON_GAME_SNAKE = "Snake"
BUTTON_GAME_TETRIS = "Tetris"
BUTTON_GAME_CONNECT_FOUR = "Connect Four"
BUTTON_GAME_HANGMAN = "Hangman"
BUTTON_GAME_MINESWEEPER = "Minesweeper"
BUTTON_GAME_COLOR_GUESS = "Color Guess"
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
BUTTON_TELL_TIME = "Tell Time"
BUTTON_KNOWN_SINCE = "Known Since"
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
