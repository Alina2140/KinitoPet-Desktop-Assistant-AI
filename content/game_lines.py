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
    "Correct! It was {answer}! You got it in {attempts} tries. Impressive.",
    "{answer}! Right on the nose in {attempts} guesses. You're good at this.",
    "Yes! {answer} was the number. Only {attempts} tries. I underestimated you.",
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
    "All pairs found in {moves} moves! You win!",
    "Perfect memory! {moves} moves. I'm impressed.",
    "You cleared the board in {moves} moves. Champion!",
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
    "Round over! You scored {score} out of {total}.",
    "That's {score} out of {total} correct. Not bad. Not amazing.",
    "Final score: {score}/{total}.",
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
    "All ships sunk in {shots} shots! You win. I'll rebuild. Silently.",
    "You got them all in {shots} tries! Fleet destroyed. Well played.",
]

BATTLESHIPS_LOSE_LINES = [
    "Out of shots! {hits} of {total} ships sunk. My fleet survives. See where they were hiding.",
    "Ten shots, no victory. You got {hits} of {total}. The rest are revealed. Study the board.",
    "No more ammo! Only {hits} of {total} ships hit. I win. The map tells the rest.",
]
