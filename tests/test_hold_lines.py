from content.hold_lines import HOLD_LINES, pick_hold_line


def test_pick_hold_line_returns_pool_member():
    line = pick_hold_line()
    assert line in HOLD_LINES


def test_hold_lines_ask_to_let_go():
    joined = " ".join(HOLD_LINES).lower()
    assert "let go" in joined or "release" in joined
