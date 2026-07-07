"""Tests for chamfered bubble chrome."""

from unittest.mock import MagicMock, patch

from kinito.bubble_ui import (
    chamfered_rect_points,
    draw_bubble_shell,
    measure_chamfered_button,
    outline_canvas_pad,
)


def test_chamfered_rect_points_clip_corners():
    points = chamfered_rect_points(0, 0, 20, 10, 3)
    assert points[:2] == [3, 0]
    assert points[-2:] == [0, 3]


def test_outline_canvas_pad_is_at_least_one():
    assert outline_canvas_pad(0) == 1
    assert outline_canvas_pad(2) == 2


def test_measure_chamfered_button_adds_padding():
    parent = MagicMock()
    mock_font = MagicMock()
    mock_font.measure.return_value = 20
    mock_font.metrics.return_value = 14

    with patch("kinito.bubble_ui.tkfont.Font", return_value=mock_font):
        width, height = measure_chamfered_button(
            parent,
            text="OK",
            font=("Helvetica", 10),
            padx=8,
            pady=2,
            chamfer=5,
            border_width=1,
        )

    assert width > 30
    assert height > 15


def test_draw_bubble_shell_creates_body_and_tail():
    canvas = MagicMock()

    draw_bubble_shell(
        canvas,
        panel_width=120,
        body_height=40,
        tail_center_x=60,
        bg="#FFF8E7",
        border="#000000",
        border_width=1,
        chamfer=8,
        tail_height=12,
        tail_half_width=11,
        offset_x=1,
        offset_y=1,
    )

    canvas.delete.assert_called_once_with("bubble")
    assert canvas.create_polygon.call_count == 2
