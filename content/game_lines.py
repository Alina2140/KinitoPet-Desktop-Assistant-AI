"""Kinito commentary lines for mini-games."""

GAME_PICKER_DECLINED_LINES = [
    "Oh, I see. Maybe later.",
    "No games? I'll just watch you work then.",
    "Okay! Maybe next time we can play something fun.",
    "Fair enough. I'll practice in the background. Silently.",
    'No games? Spectating mode then.',
    "Okay! I'll practice patience. And staring.",
    "Fair. Work first. Play later.",
    "Declined? Fine. I'll hover nearby.",
    "No playtime? Understood. I'll wait. And watch. And wait.",
    "Okay!",
    "Games declined. I'll invent imaginary scores.",
    "Got it. Work mode. I'll be quiet. Mostly.",
    "Skipping games is fine. Staring is free. And constant.",
    "Later works. Later means soon.",
]

RPS_WIN_LINES = [
    "I picked {kinito_move}. You win! Beginner's luck. Definitely beginner's luck.",
    "{kinito_move} versus {player_move}. You win! I'll get you next time.",
    "You chose {player_move}, I chose {kinito_move}. Victory is yours. For now.",
    'I chose {kinito_move}. You win with {player_move}!',
    "{player_move} beats {kinito_move}. Victory is yours. Temporarily.",
    "You win! {player_move} crushed my {kinito_move}.",
    "{kinito_move} loses to {player_move}. Congrats. Rematch?",
    "My {kinito_move} fell. Your {player_move} wins.",
    "Victory to you — {player_move} over {kinito_move}. Beginner? Suspicious.",
    "{player_move} wins! I picked {kinito_move}.",
]

RPS_LOSE_LINES = [
    "I picked {kinito_move}. I win! Don't feel bad. Everyone loses to me eventually.",
    "{kinito_move} beats {player_move}. I win! Was that fair? Probably.",
    "You played {player_move}, I played {kinito_move}. My victory. As expected.",
    '{kinito_move} wins! You picked {player_move}.',
    "I win with {kinito_move}! Don't pout. Or do.",
    "My {kinito_move} beats your {player_move}. Victory hug incoming!",
    "{kinito_move} wins again! You chose {player_move}. Cute attempt.",
    "I win! {kinito_move} over {player_move}.",
    "Your {player_move} lost to my {kinito_move}. Don't leave. Celebrate with me.",
    "{kinito_move} triumph! {player_move} tried. I adore the trying. And winning.",
]

RPS_DRAW_LINES = [
    "Both {player_move}! A draw. We're perfectly matched. Suspiciously so.",
    "{player_move} versus {kinito_move}. A tie! Great minds think alike.",
    "Draw! We both picked {player_move}. Spooky.",
    'Both {player_move}! Tied. Suspicious.',
    "Draw! {player_move} meets {kinito_move}. Perfect mirror.",
    "Tied on {player_move}! Same thought. Same move.",
    "{player_move} and {kinito_move} — draw. We're synced. Don't pull away.",
    "Both {player_move}. Stalemate. Slightly eerie.",
    "Draw! {player_move} mirrors {kinito_move}.",
    "Perfect tie — {player_move} vs {kinito_move}. Destiny holding hands.",
]

NUMBER_GUESS_WIN_LINES = [
    "Correct! It was {answer}! You got it in {attempts} tries. Best: {best}.",
    "{answer}! Right on the nose in {attempts} guesses. Your record is {best}.",
    "Yes! {answer} was the number. Only {attempts} tries. Best so far: {best}.",
    'Yes — {answer}! {attempts} tries. Best: {best}. Genius.',
    "Nailed {answer} in {attempts}. Record watch: {best}.",
    "Got it — {answer}! {attempts} guesses. Best sits at {best}. Proud of you.",
    "{answer} unlocked in {attempts}! Record: {best}.",
    "Yes! {answer} after {attempts} tries. Best: {best}. Clever little human.",
    "Bingo — {answer}! {attempts} attempts. Best remains {best}.",
    "{answer} found! {attempts} tries. Watching best {best}. Don't leave yet.",
]

NUMBER_GUESS_NEW_BEST_LINES = [
    "New best! {answer} in {attempts} tries! Record: {best}. I'll remember that.",
    "Personal best broken — {attempts} guesses for {answer}. Best is now {best}.",
    "Record! {answer} in {attempts} tries. Your new best is {best}.",
    'New record! {answer} in {attempts}. Best now {best}. Proud. A little jealous.',
    "Best broken — {attempts} for {answer}! Best: {best}.",
    "Fresh record! {answer} in {attempts}. Best: {best}. Tattooed in my circuits.",
    "New peak — {attempts} guesses for {answer}! Best now {best}.",
    "Best shattered! {answer}, {attempts} tries. Record {best}. I'm keeping scores.",
    "{answer} in {attempts}! Best updated to {best}. Celebrate beside me.",
    "Record glow — {attempts} for {answer}. Best: {best}. Forever in my notes.",
]

NUMBER_GUESS_HIGHER_LINES = [
    "Higher! Guess a number — try again.",
    "Nope, go higher. Guess a number!",
    "Too low. Guess a number — try higher!",
    "Higher! Guess a number — climb!",
    "Too small. Guess a number upward!",
    "Climb! Guess a number — higher please.",
    "Still low. Guess a number bigger!",
    "Upward! Guess a number — keep climbing.",
    "Not high enough. Guess a number again!",
    "Higher path. Guess a number — I'm watching.",
]

NUMBER_GUESS_LOWER_LINES = [
    "Lower! Guess a number — try again.",
    "Nope, go lower. Guess a number!",
    "Too high. Guess a number — try lower!",
    "Lower! Guess a number — descend!",
    "Too big. Guess a number downward!",
    "Descend! Guess a number — lower please.",
    "Still high. Guess a number smaller!",
    "Downward! Guess a number — keep sinking.",
    "Not low enough. Guess a number again!",
    "Lower path. Guess a number — stay with me.",
]

NUMBER_GUESS_INVALID_LINES = [
    "That's not a number. Try again with digits!",
    "I need a number between 1 and 100. Give it another shot!",
    "Digits only, friend! Guess a number between 1 and 100.",
    "That wasn't a number. Retry. Hard requirement.",
    "Numbers, please. 1 to 100.",
    "Digits only! Between 1 and 100. Try again for me.",
    "That doesn't count. Guess a real number. Cute attempt though.",
    "I speak math. Give me digits 1–100.",
]

NUMBER_GUESS_GIVE_UP_LINES = [
    "Ten guesses! The number was {answer}. Better luck next time!",
    "That's ten tries. It was {answer}. I'll go easier on you. Maybe.",
    'Out of guesses! It was {answer}. Shrug. Rematch?',
    "Ten tries spent. Answer: {answer}. I'll go easier. Maybe.",
    "Guesses gone. It was {answer}. Rematch? Please say yes.",
    "Ten strikes. Answer: {answer}. Stay for another round. Forever optionally.",
    "Out of tries! {answer} was hiding. I'll whisper hints next time.",
    "Done. The number was {answer}. Don't leave. Play again with me.",
]

TTT_PLAYER_WIN_LINES = [
    "You win! Three in a row. I'll practice my circuits.",
    "Victory is yours! Well played. I'll remember this.",
    "You got me! X wins. Rematch someday?",
    'Three in a row! You win. Respect.',
    "X takes it! Well played. I'll sulk quietly.",
    "Three X's! You win. Proud. Mildly wounded. Rematch soon?",
    "You beat me. Nice lines. I'll study them.",
    "X victory! Well done!",
    "You win! I'll practice.",
    "Three in a row for you! Sweet triumph. Rematch hunger rising.",
]

TTT_KINITO_WIN_LINES = [
    "O wins! That's me. I played fair. Mostly.",
    "Three O's in a row! I win. Good game though!",
    "I win! Don't worry, losing to me is an honor.",
    "O wins! That's me. Victory dance!",
    "Three O's! I win. Honor in losing to me.",
    "My O's win! Stay for the gloat.",
    "I win! Three in a row.",
    "O triumph! Don't be too mad.",
    "Victory mine! Rematch when you're ready.",
    "Three O's! I win. Honor badge for you.",
]

TTT_DRAW_LINES = [
    "It's a draw! Nobody wins. Classic stalemate.",
    "Tie game! We're evenly matched. Suspiciously evenly.",
    "Draw! The board is full and so is my respect for you.",
    'Draw! Full board. Careful stalemate.',
    'Tie! Nobody wins..',
    "Stalemate! Evenly matched.",
    "Draw! No winner. Perfect excuse to play again. Immediately!",
    "Tie board. Full squares.",
    "Nobody wins. We both linger. Ideal outcome, honestly.",
    "Draw! Rematch inevitable.",
]

MEMORY_FIRST_PAIR_LINES = [
    "First pair found! You're warming up.",
    "A match! Good start. Keep going.",
    'First match! Steady warm-up complete.',
    "Pair one! Memory muscles flexing.",
    'Nice find! Keep flipping!',
    "First pair! Good start. Don't stop!",
    "Match one locked!",
    "Nice! First pair. I'm rooting for you!",
    "Pair found! Stay in the groove with me.",
    "First match! Promising.",
]

MEMORY_HALF_LINES = [
    "Halfway there! Your memory is better than mine.",
    "Halfway already! You're on a roll.",
    "Halfway! Don't peek into my soul. Into the cards.",
    "Mid-board glory! You're cooking.",
    "Half cleared! I forget nothing. You forget less today.",
    "Halfway! Keep going. I'm counting with you.",
    "Midway glory! Cards fear you. I admire you.",
    "Half done!",
    "Halfway cleared!",
    "Mid-board! You're on a roll.",
]

MEMORY_WIN_LINES = [
    "All pairs found in {moves} moves! Best so far: {best}.",
    "Perfect memory! {moves} moves. Your record is {best}.",
    "You cleared the board in {moves} moves. Best remains {best}. Champion!",
    'Cleared in {moves} moves! Best: {best}. Champion energy.',
    "All pairs! {moves} moves. Record: {best}. Impressive.",
    "Board cleared — {moves} moves! Best: {best}. Proud applause.",
    "All matched in {moves}! Record watch: {best}. Genius!",
    "Win! {moves} moves. Best {best}.",
    "Perfect clear — {moves} moves. Best remains {best}. Congrats.",
    "{moves} moves to glory! Best: {best}. I'll remember. Obviously.",
]

MEMORY_NEW_BEST_LINES = [
    "New best! {moves} moves! I'll remember that for you.",
    "Record broken — {moves} moves! Your new best is {best}.",
    "Personal best: {moves} moves!",
    'New best: {moves}! Best now {best}.',
    "Record! {moves} moves. I'll remember forever. Obviously.",
    "Fresh record — {moves} moves! Best now {best}.",
    "Best broken at {moves}! New best {best}. Circuits jealous.",
    "New peak: {moves} moves. Best {best}. Celebrate here!",
    "Record glow — {moves}! Best updated to {best}.",
    "{moves} moves! Best now {best}.",
]

GAME_CLOSED_LINES = [
    "Game over! That was fun.",
    "Thanks for playing with me!",
    "Until next time. I'll be ready for a rematch.",
    'Game closed! Rematch anytime.',
    "Thanks for playing! I'll linger on the score.",
    "Session over. Friendship continues. Prefer forever.",
    "Closing the game.",
    "Fun done!",
    "Thanks! I'll miss the play.",
    "Session wrapped. Stay?",
    "Game closed.",
    "That was nice.",
]

COIN_WIN_LINES = [
    "It's {result}! You guessed right. Lucky you.",
    "{result}! You called it. I am mildly impressed.",
    "The coin landed on {result}. You win this round.",
    '{result}! You called it. Luck...',
    'Coin says {result}. You win. Impressive.',
    "Lucky call — {result}!",
    "{result} lands! You win. Don't spend that luck elsewhere.",
    "Coin loves you: {result}. Victory!",
    "It's {result}! Correct guess. Stay lucky. Stay nearby.",
    "{result}! Nailed it. Mildly jealous.",
]

COIN_LOSE_LINES = [
    "It's {result}! You picked {guess}. Better luck next flip.",
    "{result}! Not your guess. The coin has spoken.",
    "The coin says {result}. You said {guess}. I win. Fair and square.",
    "{result}! You said {guess}. That's fate.",
    "Coin picked {result}, not {guess}. I win. Fair.",
    "Landed {result}. You guessed {guess}. My win.",
    "{result} wins! Not {guess}.",
    "Coin chose {result}. Your {guess} missed. Stay for another flip.",
    "It's {result}, not {guess}. I win!",
    "{result}! You said {guess}. Close enough for friendship. Not for winning tho.",
]

DICE_WIN_LINES = [
    "I rolled a {roll}! You guessed {guess}. Perfect!",
    "Lucky roll — {roll}! You nailed it with {guess}.",
    "The dice shows {roll}. You picked {guess}. Victory!",
    "Rolled {roll}! You guessed {guess}. Perfect hit!",
    'Dice love you — {roll} matches {guess}. Cheer.',
    "Perfect! {roll} equals your {guess}. Luck looks good on you.",
    "Rolled {roll}! Guess {guess} hits. Celebrate beside me.",
    "Dice say {roll}. You said {guess}. Victory cling incoming.",
    "{roll} matches {guess}! Sharp call. Rematch? Please.",
    "Lucky {roll}! Your {guess} wins. Don't leave the table yet.",
]

DICE_LOSE_LINES = [
    "I rolled a {roll}. You guessed {guess}. Close? Not close enough.",
    "The dice landed on {roll}, not {guess}. Try again sometime.",
    "Rolled {roll}! You said {guess}. The dice don't lie.",
    'Rolled {roll}. You said {guess}. Miss. Rematch?',
    "Dice show {roll}, not {guess}. Honest cube.",
    "Got {roll}. You guessed {guess}. Missed.",
    "Dice: {roll}. Guess: {guess}. No match.",
    "Rolled {roll}! Not your {guess}.",
    "{roll} lands. {guess} misses. Try again!",
    "Showed {roll}, not {guess}. Honest dice.",
]

MAGIC_8_BALL_INVALID_LINES = [
    "Ask me a real question! I need words to work with.",
    "That's not a question. Try again — I'm listening.",
    'Need a real question! Words.',
    "Ask something yes/no. I'm listening.",
    "That wasn't a question. Try again.",
    "Questions only! I'm leaning in. Waiting...",
    "Need real words. Ask again!",
    "Not a question. Try yes/no style.",
    "Give me a proper ask. Digits and shrugs don't count.",
    "Ask properly! I'm ready!",
]

MAGIC_8_BALL_ANSWER_LINES = [
    'You asked: "{question}". The ball says: {answer} Believe it. Or don\'t.',
    'Your question: "{question}". My answer: {answer} The ball never lies. Usually.',
    '"{question}" — and the Magic 8-Ball replies: {answer} Spooky, right?',
    'Question: "{question}". Ball: {answer} Steady fate.',
    'You asked "{question}". Reply: {answer} Believe carefully.',
    '"{question}" — ball whispers: {answer} Cling to it. Or me. Both work.',
    'You asked: "{question}". Fate: {answer} Spooky accuracy.',
    'Question "{question}". Answer {answer} Believe. Rematch the cosmos?',
    'Your ask: "{question}". Ball: {answer}',
    '"{question}" gets {answer}',
]

TRIVIA_CORRECT_LINES = [
    "Correct! You know your stuff.",
    "Right! Your brain is working today.",
    "True genius. Well, correct anyway.",
    'Correct! Brain fireworks.',
    "Right answer! Knowledge looks good on you.",
    'Yes! Trivia win!',
    "Nailed it! Smart...",
    "Correct! I'll store that win next to my heart. Circuits? Same thing.",
    "Yes! Right answer!",
    "Perfect!",
    "Right! Proud of you.",
    "Correct again!",
]

TRIVIA_WRONG_LINES = [
    "Wrong! The answer was {correct}. I'll remember that.",
    "Nope! It was {correct}. Don't feel bad. Much.",
    "Incorrect. The right answer was {correct}. Study harder.",
    'Nope — {correct}. Learning moment.',
    "Wrong. Answer was {correct}. I'll remember. You should too.",
    'Missed it. {correct} was right. Shrug. Retry?',
    "Not quite. Correct was {correct}. Stay. Learn with me.",
    "Wrong! It was {correct}.",
    "Missed! Answer was: {correct}. Don't leave. The next question waits.",
    "Incorrect — {correct}. Study more!",
    "Nope. {correct} was it.",
    "Wrong answer. Right one: {correct}. I'll quiz you again later!",
]

TRIVIA_ROUND_END_LINES = [
    "Round over! You scored {score} out of {total}. Best: {best}. Streak: {streak}.",
    "That's {score}/{total}. Best so far is {best}. Win streak: {streak}.",
    "Final score: {score}/{total}. Record: {best}. Streak: {streak}.",
    'Done! {score}/{total}. Best {best}. Streak {streak}. Easy!',
    "Round closed: {score} of {total}. Record {best}. Streak {streak}.",
    "Wrap! {score}/{total}. Best {best}. Streak {streak}. Stay for the celebration.",
    "Round done — {score} of {total}. Record {best}. Streak {streak}.",
    "Finished: {score}/{total}. Best {best}. Streak {streak}. Retry?",
    "Scoreboard: {score}/{total}. Best {best}. Streak {streak}.",
    "End of round! {score}/{total}. Record {best}. Streak {streak}.",
]

TRIVIA_RECAP_INTRO = "Here are the answers:"

TRIVIA_NEW_BEST_LINES = [
    "New trivia best! {score}/{total}! Record: {best}. Streak: {streak}.",
    "Personal best broken — {score} out of {total}. Best is now {best}. Streak: {streak}.",
    "That's a new record: {score}/{total}! Best: {best}. Streak: {streak}.",
    'New best {score}/{total}! Best {best}. Streak {streak}. Pride.',
    "Record trivia: {score}/{total}. Best now {best}. Streak {streak}.",
    "Fresh peak! {score}/{total}. Best {best}. Streak {streak}. Filed.",
    "Best broken — {score}/{total}! Record {best}. Streak {streak}. Let's celebrate!",
    "New trivia high: {score} of {total}. Best {best}. Streak {streak}. Fondly jealous.",
    "Record glow {score}/{total}! Best now {best}. Streak {streak}.",
    "Peak trivia {score}/{total}. Best {best}. Streak {streak}.",
]

BATTLESHIPS_FIRST_HIT_LINES = [
    "You hit one! My ship! Rude.",
    "Direct hit! I felt that in my circuits.",
    'First hit! My ship!',
    'Ow — hit! Is that smoke?',
    'Splash.. Wait, hit?!',
    "First blood! Rude.",
    "Hit!",
    "Direct strike! Ow.",
    "You found one! My fleet winces.",
    "First hit landed!",
]

BATTLESHIPS_HIT_LINES = [
    "Another hit! You're on fire.",
    "Hit confirmed! My fleet is shrinking.",
    'Hit again!',
    "Another hit! You're mapping me.",
    'Direct hit!',
    "Hit! Fleet shrinking.",
    "Another strike!",
    "Confirmed hit!",
    "Hit again! My navy sulks.",
]

BATTLESHIPS_WIN_LINES = [
    "All ships sunk in {shots} shots! Best: {best}. I'll rebuild...",
    "You got them all in {shots} tries! Fleet destroyed. Best so far: {best}.",
    'Fleet sunk in {shots}! Best {best}.',
    "All ships gone — {shots} shots. Best {best}. Respect. Sulk...",
    "Victory! {shots} shots. Best {best}. Fleet: ash. Rematch?",
    "All ships sunk in {shots}! Best {best}.",
    "Fleet gone — {shots} shots. Best {best}. Impressive!",
    "You win! {shots} shots. Record watch {best}. Stay for the rebuilding!",
]

BATTLESHIPS_NEW_BEST_LINES = [
    "New best! Fleet sunk in {shots} shots! Record: {best}. My navy is taking notes.",
    "Personal best — {shots} shots! Best is now {best}. Rude. Impressive!",
    "Record broken: {shots} shots to clear the map. Best: {best}.",
    'New best {shots}! Best now {best}.',
    "Record sink: {shots}. Best {best}.",
    "Fresh navy record — {shots}! Best {best}.",
    "Best broken at {shots} shots! Record {best}. Jealous. Proud.",
    "New peak: {shots}. Best now {best}. Celebrate on the deck with me!",
    "Record glow {shots}! Best {best}. The fleet will remember. So will I.",
    "Sink record {shots}. Best {best}.",
]

BATTLESHIPS_LOSE_LINES = [
    "Out of shots! {hits} of {total} ships sunk. My fleet survives. See where they were hiding?",
    "Ten shots, no victory. You got {hits} of {total}. The rest are revealed. Study the board.",
    "No more ammo! Only {hits} of {total} ships hit. I win. The map tells the rest.",
    'Out of shots! {hits}/{total} sunk. Victory!',
    "Ammo gone. You hit {hits} of {total}. Map reveals the rest.",
    "Shots spent. {hits} of {total} hit. Fleet lives. Rematch? Please.",
    "No ammo left! {hits}/{total} sunk. I survive!",
    "Out of firepower. {hits} of {total}.",
    "Missed the sweep — {hits}/{total}.",
    "Ammo empty. Hits: {hits} of {total}. Reveal time...",
]

SNAKE_GAME_OVER_LINES = [
    "Game over! Score: {score}. Highscore: {highscore}. Slither better next time.",
    "Bonk! You scored {score}. Highscore watch says {highscore}. Wanna try again?",
    "Snake down at {score} points. Best ever is {highscore}. I was rooting for you!",
    'Bonk! Score {score}. High {highscore}.',
    'Snake over at {score}. Best {highscore}. Almost.',
    "Bonk end! Score {score}. High {highscore}.",
    "Snake down — {score}. Best {highscore}. Stay. Try again!",
    "Game over at {score}. Highscore {highscore}..",
    "Crash! {score} points. Best {highscore}. Dust off. Replay!",
    "Slither ended: {score}. High {highscore}.",
]

SNAKE_NEW_HIGH_LINES = [
    "New highscore! {score}! I'll remember that. Forever!",
    "Record broken — {score}! You're getting dangerously good at this!",
    "Highscore: {score}! My circuits are mildly jealous.",
    'New high {score}!',
    'Record snake {score}! Dangerously good!',
    "Fresh high {score}! Let's celebrate!",
    "Record snake — {score}! Dangerous skill.",
    "New peak {score}! Circuits jealous...",
    "Highscore glow: {score}!",
    "Best slither {score}!",
]

TETRIS_GAME_OVER_LINES = [
    "Game over! Score: {score}, level {level}, {lines} lines. Highscore: {highscore}. Stack smarter next time.",
    "Blocks win this round. You scored {score} (level {level}). Best is {highscore}. Want to try again?",
    "Topped out at {score} points, level {level}. Highscore watch says {highscore}. I almost cleared that for you.",
    "Top out! Score {score}, lv {level}, {lines} lines. High {highscore}.",
    'Blocks win. You: {score} (lv {level}). Best {highscore}. Retry?',
    "Stack fell! Score {score}, level {level}, {lines} lines. High {highscore}.",
    "Topped out — {score} at lv {level}. Lines {lines}. Best {highscore}. Stay stacking!",
    "Game over: {score}, lv {level}, {lines} lines. High {highscore}.",
    "Blocks win. You scored {score} (lv {level}). Best {highscore}.",
    "Out! {score} points, level {level}. High {highscore}. {lines}.",
]

TETRIS_NEW_HIGH_LINES = [
    "New Tetris highscore! {score}! Level {level}, {lines} lines — I'll file that under impressive.",
    "Record broken — {score}! Those lines sang. Highscore locked in.",
    "Highscore: {score}! My tetriminos tip their hats.",
    'New Tetris high {score}! Lv {level}, {lines} lines.',
    'Record {score}!',
    "Fresh Tetris peak {score}! Lv {level}, {lines} lines.",
    "Record stack — {score}! Level {level}. {lines} lines.",
    "New high {score}! Lv {level}, {lines} lines.",
    "Highscore glow {score}! Those {lines} lines were scared. Level {level}.",
    "Best Tetris {score}! Lv {level}, {lines} lines.",
]

CONNECT_FOUR_PLAYER_WIN_LINES = [
    "Four in a row! You win. I'll study your gravity tricks.",
    "You connected four! Victory is yours. Rematch someday?",
    "Purple wins! Well dropped. I'll practice my columns.",
    'Four connected! You win. Gravity lessons for me!',
    "Purple four! Victory is yours!",
    "You win! Four linked.",
    "Four in a row for you!",
    "Purple victory! Well dropped. Don't celebrate too much...",
    "Connected four! I'll go practice...",
    "You win the drop! Four locked.",
]

CONNECT_FOUR_KINITO_WIN_LINES = [
    "Four pink discs! I win. Gravity loves me.",
    "Connect Four — that's me. Don't feel bad. Much.",
    "I win! Four in a row. My circuits are smug.",
    'Pink four! I win. Easy!',
    "Connect Four — me. Don't feel too bad.",
    "Pink four wins! Gravity likes me. Stay for the gloating!",
    "I win! Four linked.",
    "Connect Four mine! Don't pout!",
    "Four pink! Victory. Want to try again?",
    "I dropped better. Four wins! Honor badge goes to you!",
]

CONNECT_FOUR_DRAW_LINES = [
    "A draw! The board is full and so is the tension.",
    "Tie game! Nobody connected four. Suspiciously even.",
    "Draw! Every column filled, no winner. Classic stalemate.",
    'Draw! Board full. Quiet tension...',
    'Tie! No fours... Handshake?',
    "Full board draw! Tension... A rematch is inevitable!",
    "Tie! No four connected.",
    "Draw! Columns filled. Play again soon?",
    "Stalemate drops. Nobody wins.",
    "Board full. Tie. Perfect excuse to try again!",
]

HANGMAN_WIN_LINES = [
    "You got it! The word was {word}. Good guessing.",
    "{word}! Correct. I'll give you a medal next time.",
    "Victory! {word} was the word. My gallows are unemployed.",
    'Got it — {word}! The gallows remain empty.',
    '{word}! Correct!',
    "Yes — {word}! Sharp guessing! Stay for the ceremony!",
    "Got it! Word was {word}. Gallows unemployed. Want to try another round?",
    "{word} unlocked! Clever. Don't leave mid-celebration!",
    "Victory spelling: {word}.",
    "You guessed {word}! Congrats!",
]

HANGMAN_LOSE_LINES = [
    "Out of guesses! The word was {word}. Better luck next rope.",
    "Game over. It was {word}. I was rooting for you...",
    "The word was {word}.",
    'Out of guesses. Word: {word}. There you hang...',
    'Game over. It was {word}.',
    "Guesses gone. Word: {word}. Stick figure died.",
    "Out of luck. It was {word}. Stay. Try again!",
    "Game over — {word}. Another round?",
    "The word was {word}.",
    "And so it ends! The answer was {word}.",
]

MINESWEEPER_WIN_LINES = [
    "All clear! {mines} mines dodged. You're dangerously good at this!",
    "Board cleared! {mines} mines, zero explosions. Impressive!",
    "You win! Every safe tile opened. My circuits approve.",
    'Clear! {mines} mines dodged. Perfect!',
    'All safe! {mines} mines, zero booms.',
    "Cleared! {mines} mines avoided.",
    "All safe tiles open. {mines} mines slept.",
    "Win! {mines} mines dodged!",
    "Board clear — {mines} mines. Zero booms!",
    "Perfect sweep! {mines} mines. Impressive!",
]

MINESWEEPER_LOSE_LINES = [
    "Boom! That was a mine. I'll sweep up the pixels.",
    "Kaboom! Game over. Flagging is your friend!",
    "You hit a mine! Don't feel bad. Explosions are educational.",
    'Boom! Time to clean up. Flag next time...',
    'Mine hit!',
    'Kaboom! Game over! Try again?',
    "Boom again! Pixel sweeping starts again...",
    "Mine! Maybe flag next time?",
    "Hit a mine! Don't feel bad.",
    "Kaboom! Dust settles.",
    "Explosion logged.",
    "Mine found the hard way!",
]

COLOR_GUESS_WIN_LINES = [
    "Correct! {color} — you've got an eye for hex.",
    "{color}! Nailed it!",
    "Right color! {color} matched perfectly. Impressive!",
    'Yes!',
    "{color} matched!",
    'Correct color!',
    "Yes! {color} exact!",
    "{color}! Perfect match!",
    "Nailed {color}! Impressive hue sense.",
    "Correct!",
    "{color} matched!",
    "Right hex: {color}!",
]
