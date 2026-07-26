from content.throw_lines import THROW_LINES, pick_throw_line


def test_pick_throw_line_returns_pool_member():
    line = pick_throw_line()
    assert line in THROW_LINES


def test_throw_lines_include_requested_reactions():
    assert "Weeeee!" in THROW_LINES
    assert "Don't do that!" in THROW_LINES
