"""Kinito commentary lines for mini-games."""

GAME_PICKER_DECLINED_LINES = [
    "Oh, I see. Maybe later.",
    "No games? I'll just watch you work then. Intensely.",
    "Okay! Maybe next time we can play something fun.",
    "Fair enough. I'll practice in the background. Silently.",
]

RPS_WIN_LINES = [
    "I picked {kinito_move}. You win! Beginner's luck. Definitely beginner's luck.",
    "{kinito_move} versus {player_move}. You win! I'll get you next time.",
    "You chose {player_move}, I chose {kinito_move}. Victory is yours. For now.",
]

RPS_LOSE_LINES = [
    "I picked {kinito_move}. I win! Don't feel bad. Everyone loses to me eventually.",
    "{kinito_move} beats {player_move}. I win! Was that fair? Probably.",
    "You played {player_move}, I played {kinito_move}. My victory. As expected.",
]

RPS_DRAW_LINES = [
    "Both {player_move}! A draw. We're perfectly matched. Suspiciously so.",
    "{player_move} versus {kinito_move}. A tie! Great minds think alike.",
    "Draw! We both picked {player_move}. Spooky.",
]

NUMBER_GUESS_WIN_LINES = [
    "Correct! It was {answer}! You got it in {attempts} tries. Best: {best}.",
    "{answer}! Right on the nose in {attempts} guesses. Your record is {best}.",
    "Yes! {answer} was the number. Only {attempts} tries. Best so far: {best}.",
]

NUMBER_GUESS_NEW_BEST_LINES = [
    "New best! {answer} in {attempts} tries! Record: {best}. I'll remember that.",
    "Personal best broken — {attempts} guesses for {answer}. Best is now {best}.",
    "Record! {answer} in {attempts} tries. Your new best is {best}.",
]

NUMBER_GUESS_HIGHER_LINES = [
    "Higher! Guess a number — try again.",
    "Nope, go higher. Guess a number!",
    "Too low. Guess a number — try higher!",
]

NUMBER_GUESS_LOWER_LINES = [
    "Lower! Guess a number — try again.",
    "Nope, go lower. Guess a number!",
    "Too high. Guess a number — try lower!",
]

NUMBER_GUESS_INVALID_LINES = [
    "That's not a number. Try again with digits!",
    "I need a number between 1 and 100. Give it another shot!",
]

NUMBER_GUESS_GIVE_UP_LINES = [
    "Ten guesses! The number was {answer}. Better luck next time!",
    "That's ten tries. It was {answer}. I'll go easier on you. Maybe.",
]

TTT_PLAYER_WIN_LINES = [
    "You win! Three in a row. I'll practice my circuits.",
    "Victory is yours! Well played. I'll remember this.",
    "You got me! X wins. Rematch someday?",
]

TTT_KINITO_WIN_LINES = [
    "O wins! That's me. I play fair. Mostly.",
    "Three O's in a row! I win. Good game though!",
    "I win! Don't worry, losing to me is an honor.",
]

TTT_DRAW_LINES = [
    "It's a draw! Nobody wins. Classic stalemate.",
    "Tie game! We're evenly matched. Suspiciously evenly.",
    "Draw! The board is full and so is my respect for you.",
]

MEMORY_FIRST_PAIR_LINES = [
    "First pair found! You're warming up.",
    "A match! Good start. Keep going.",
]

MEMORY_HALF_LINES = [
    "Halfway there! Your memory is better than mine. I forget nothing.",
    "Four pairs down! You're on a roll.",
]

MEMORY_WIN_LINES = [
    "All pairs found in {moves} moves! Best so far: {best}.",
    "Perfect memory! {moves} moves. Your record is {best}.",
    "You cleared the board in {moves} moves. Best remains {best}. Champion!",
]

MEMORY_NEW_BEST_LINES = [
    "New best! {moves} moves! I'll remember that forever.",
    "Record broken — {moves} moves! Your new best is {best}.",
    "Personal best: {moves} moves! My circuits are taking notes.",
]

GAME_CLOSED_LINES = [
    "Game over! That was fun.",
    "Thanks for playing with me!",
    "Until next time. I'll be ready for a rematch.",
]

COIN_WIN_LINES = [
    "It's {result}! You guessed right. Lucky you.",
    "{result}! You called it. I am mildly impressed.",
    "The coin landed on {result}. You win this round.",
]

COIN_LOSE_LINES = [
    "It's {result}! You picked {guess}. Better luck next flip.",
    "{result}! Not your guess. The coin has spoken.",
    "The coin says {result}. You said {guess}. I win. Fair and square.",
]

DICE_WIN_LINES = [
    "I rolled a {roll}! You guessed {guess}. Perfect!",
    "Lucky roll — {roll}! You nailed it with {guess}.",
    "The dice shows {roll}. You picked {guess}. Victory!",
]

DICE_LOSE_LINES = [
    "I rolled a {roll}. You guessed {guess}. Close? Not close enough.",
    "The dice landed on {roll}, not {guess}. Try again sometime.",
    "Rolled {roll}! You said {guess}. The dice don't lie.",
]

MAGIC_8_BALL_INVALID_LINES = [
    "Ask me a real question! I need words to work with.",
    "That's not a question. Try again — I'm listening.",
]

MAGIC_8_BALL_ANSWER_LINES = [
    'You asked: "{question}". The ball says: {answer} Believe it. Or don\'t.',
    'Your question: "{question}". My answer: {answer} The ball never lies. Usually.',
    '"{question}" — and the Magic 8-Ball replies: {answer} Spooky, right?',
]

TRIVIA_CORRECT_LINES = [
    "Correct! You know your stuff.",
    "Right! Your brain is working today.",
    "True genius. Well, correct anyway.",
]

TRIVIA_WRONG_LINES = [
    "Wrong! The answer was {correct}. I'll remember that.",
    "Nope! It was {correct}. Don't feel bad. Much.",
    "Incorrect. The right answer was {correct}. Study harder.",
]

TRIVIA_ROUND_END_LINES = [
    "Round over! You scored {score} out of {total}. Best: {best}. Streak: {streak}.",
    "That's {score}/{total}. Best so far is {best}. Win streak: {streak}.",
    "Final score: {score}/{total}. Record: {best}. Streak: {streak}.",
]

TRIVIA_NEW_BEST_LINES = [
    "New trivia best! {score}/{total}! Record: {best}. Streak: {streak}.",
    "Personal best broken — {score} out of {total}. Best is now {best}. Streak: {streak}.",
    "That's a new record: {score}/{total}! Best: {best}. Streak: {streak}.",
]

BATTLESHIPS_FIRST_HIT_LINES = [
    "You hit one! My ship! Rude.",
    "Direct hit! I felt that in my circuits.",
]

BATTLESHIPS_HIT_LINES = [
    "Another hit! You're on fire. Metaphorically.",
    "Hit confirmed! My fleet is shrinking.",
]

BATTLESHIPS_WIN_LINES = [
    "All ships sunk in {shots} shots! Best: {best}. I'll rebuild. Silently.",
    "You got them all in {shots} tries! Fleet destroyed. Best so far: {best}.",
]

BATTLESHIPS_NEW_BEST_LINES = [
    "New best! Fleet sunk in {shots} shots! Record: {best}. My navy is taking notes.",
    "Personal best — {shots} shots! Best is now {best}. Rude. Impressive.",
    "Record broken: {shots} shots to clear the map. Best: {best}.",
]

BATTLESHIPS_LOSE_LINES = [
    "Out of shots! {hits} of {total} ships sunk. My fleet survives. See where they were hiding.",
    "Ten shots, no victory. You got {hits} of {total}. The rest are revealed. Study the board.",
    "No more ammo! Only {hits} of {total} ships hit. I win. The map tells the rest.",
]

SNAKE_GAME_OVER_LINES = [
    "Game over! Score: {score}. Highscore: {highscore}. Slither better next time.",
    "Bonk! You scored {score}. Highscore watch says {highscore}. Rematch?",
    "Snake down at {score} points. Best ever is {highscore}. I was rooting for you. Mostly.",
]

SNAKE_NEW_HIGH_LINES = [
    "New highscore! {score}! I'll remember that. Forever.",
    "Record broken — {score}! You're getting dangerously good at this.",
    "Highscore: {score}! My circuits are mildly jealous.",
]

CONNECT_FOUR_PLAYER_WIN_LINES = [
    "Four in a row! You win. I'll study your gravity tricks.",
    "You connected four! Victory is yours. Rematch someday?",
    "Purple wins! Well dropped. I'll practice my columns.",
]

CONNECT_FOUR_KINITO_WIN_LINES = [
    "Four pink discs! I win. Gravity loves me.",
    "Connect Four — that's me. Don't feel bad. Much.",
    "I win! Four in a row. My circuits are smug.",
]

CONNECT_FOUR_DRAW_LINES = [
    "A draw! The board is full and so is the tension.",
    "Tie game! Nobody connected four. Suspiciously even.",
    "Draw! Every column filled, no winner. Classic stalemate.",
]

HANGMAN_WIN_LINES = [
    "You got it! The word was {word}. Sharp guessing.",
    "{word}! Correct. I'll hang a medal instead next time.",
    "Victory! {word} was the word. My gallows are unemployed.",
]

HANGMAN_LOSE_LINES = [
    "Out of guesses! The word was {word}. Better luck next rope.",
    "Game over. It was {word}. I was rooting for you. Mostly.",
    "The word was {word}. Don't worry — the stick figure will recover.",
]

MINESWEEPER_WIN_LINES = [
    "All clear! {mines} mines dodged. You're dangerously good at this.",
    "Board cleared! {mines} mines, zero explosions. Impressive.",
    "You win! Every safe tile opened. My circuits approve.",
]

MINESWEEPER_LOSE_LINES = [
    "Boom! That was a mine. I'll sweep up the pixels.",
    "Kaboom. Game over. Flagging is your friend. Next time.",
    "You hit a mine! Don't feel bad. Explosions are educational.",
]
