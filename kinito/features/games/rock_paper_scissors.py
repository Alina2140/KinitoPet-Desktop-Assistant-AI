"""Rock-paper-scissors outcome logic."""

from content import dialogue as dlg

MOVES = (dlg.BUTTON_ROCK, dlg.BUTTON_PAPER, dlg.BUTTON_SCISSORS)

_BEATS = {
    dlg.BUTTON_ROCK: dlg.BUTTON_SCISSORS,
    dlg.BUTTON_PAPER: dlg.BUTTON_ROCK,
    dlg.BUTTON_SCISSORS: dlg.BUTTON_PAPER,
}


def rps_winner(player_move: str, kinito_move: str) -> str | None:
    """Return 'player', 'kinito', or None for a draw."""
    if player_move not in MOVES or kinito_move not in MOVES:
        return None
    if player_move == kinito_move:
        return None
    if _BEATS[player_move] == kinito_move:
        return "player"
    return "kinito"
