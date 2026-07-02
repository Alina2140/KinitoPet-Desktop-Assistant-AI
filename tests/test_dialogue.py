import pytest

from content import dialogue as dlg
from content.goodbye_lines import GOODBYE_LINES


def test_pick_line_returns_member():
    lines = ["a", "b", "c"]
    assert dlg.pick_line(lines) in lines


def test_pick_line_requires_non_empty_list():
    with pytest.raises(IndexError):
        dlg.pick_line([])


def test_pick_declined_line_returns_from_ack_or_specific():
    specific = ["Specific decline line."]
    seen = {dlg.pick_declined_line(specific) for _ in range(40)}
    assert seen & set(dlg.DECLINED_ACK_LINES)
    assert "Specific decline line." in seen


@pytest.mark.parametrize(
    "questions,marker",
    [
        (dlg.CAMERA_QUESTIONS, dlg.CAMERA_QUESTION_MARKER),
        (dlg.BROWSER_QUESTIONS, dlg.BROWSER_QUESTION_MARKER),
        (dlg.MUSIC_PLAYER_QUESTIONS, dlg.MUSIC_PLAYER_QUESTION_MARKER),
        (dlg.HUG_QUESTIONS, dlg.HUG_QUESTION_MARKER),
        (dlg.STORY_QUESTIONS, dlg.STORY_QUESTION_MARKER),
        (dlg.DAY_QUESTIONS, dlg.DAY_QUESTION),
        (dlg.TRUST_QUESTIONS, dlg.TRUST_QUESTION),
        (dlg.POEM_QUESTIONS, dlg.POEM_QUESTION),
        (dlg.FUN_FACT_QUESTIONS, dlg.FUN_FACT_QUESTION),
        (dlg.GAME_QUESTIONS, dlg.GAME_QUESTION),
        (dlg.IMAGE_QUESTIONS, dlg.IMAGE_QUESTION),
        (dlg.COLOR_QUESTIONS, dlg.COLOR_QUESTION),
        (dlg.LONELY_QUESTIONS, dlg.LONELY_QUESTION),
    ],
)
def test_spontaneous_questions_contain_dialog_marker(questions, marker):
    marker_lower = marker.lower()
    for question in questions:
        assert marker_lower in question.lower(), f"Missing marker in: {question!r}"


@pytest.mark.parametrize(
    "lines",
    [
        dlg.CAMERA_DECLINED_LINES,
        dlg.BROWSER_DECLINED_LINES,
        GOODBYE_LINES,
    ],
    ids=["camera_declined", "browser_declined", "goodbye"],
)
def test_response_line_pools_are_non_empty(lines):
    assert len(lines) >= 1
    assert all(isinstance(line, str) and line.strip() for line in lines)
