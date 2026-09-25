from unittest.mock import MagicMock, patch

import pytest

from kinito.features.music import MusicMixin
from kinito.settings_store import clamp_music_volume


class MusicStub(MusicMixin):
    pass


@pytest.fixture
def music():
    stub = MusicStub()
    stub.speak = MagicMock()
    stub.play_mp3 = MagicMock()
    stub.stop_background_music = MagicMock()
    stub.root = MagicMock()
    stub.root.winfo_exists.return_value = True
    stub._running = True
    stub._is_busy_with_speech = MagicMock(return_value=False)
    stub._is_background_music_playing = MagicMock(return_value=True)
    stub._persist_settings = MagicMock()
    stub._music_folder = ""
    stub._music_volume = 75
    stub.setup_music_player()
    return stub


def test_list_folder_mp3s_non_recursive(tmp_path):
    (tmp_path / "song1.mp3").write_bytes(b"x")
    (tmp_path / "song2.MP3").write_bytes(b"x")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "deep.mp3").write_bytes(b"x")
    files = MusicMixin._list_folder_mp3s(str(tmp_path))
    assert len(files) == 2
    assert all(f.lower().endswith(".mp3") for f in files)
    assert all("nested" not in f for f in files)


def test_reload_music_playlist_sorted(music, tmp_path):
    (tmp_path / "b.mp3").write_bytes(b"x")
    (tmp_path / "a.mp3").write_bytes(b"x")
    music._music_folder = str(tmp_path)
    assert music._reload_music_playlist() is True
    names = [path.lower() for path in music._music_playlist]
    assert names[0].endswith("a.mp3")
    assert names[1].endswith("b.mp3")


def test_reload_music_playlist_applies_saved_shuffle(music, tmp_path):
    (tmp_path / "a.mp3").write_bytes(b"x")
    (tmp_path / "b.mp3").write_bytes(b"x")
    music._music_folder = str(tmp_path)
    music._music_shuffle = True
    with patch.object(music, "_reshuffle_playlist_from_current") as reshuffle:
        assert music._reload_music_playlist() is True
    reshuffle.assert_called_once()


def test_play_user_mp3_rejects_non_mp3(music):
    music.play_user_mp3("song.wav")
    music.speak.assert_called_once()


def test_play_user_mp3_rejects_missing_file(music):
    music.play_user_mp3("missing.mp3")
    music.speak.assert_called_once()


def test_play_user_mp3_plays_and_announces(music, tmp_path):
    mp3 = tmp_path / "My Song.mp3"
    mp3.write_bytes(b"x")
    with patch("kinito.features.music.random.choice", return_value="Playing {song}!"):
        music.play_user_mp3(str(mp3))
    music.play_mp3.assert_called_once_with(str(mp3), volume=0.75)
    assert music._user_music_path == str(mp3)
    music.speak.assert_called_once_with("Playing My Song!", skip_ai=True)


def test_play_user_mp3_can_skip_announce(music, tmp_path):
    mp3 = tmp_path / "Quiet.mp3"
    mp3.write_bytes(b"x")
    music.play_user_mp3(str(mp3), announce=False)
    music.speak.assert_not_called()


def test_prev_next_wrap_in_playlist(music, tmp_path):
    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    c = tmp_path / "c.mp3"
    for path in (a, b, c):
        path.write_bytes(b"x")
    music._music_folder = str(tmp_path)
    music._reload_music_playlist()
    music._music_index = 1
    music.play_user_mp3 = MagicMock()

    music.play_previous_track()
    music.play_user_mp3.assert_called_with(str(a), announce=False)

    music._music_index = 0
    music.play_previous_track()
    music.play_user_mp3.assert_called_with(str(c), announce=False)

    music._music_index = 2
    music.play_next_track()
    music.play_user_mp3.assert_called_with(str(a), announce=False)


def test_toggle_music_playback_pauses_and_unpauses(music):
    music._user_music_path = "song.mp3"
    music._is_background_music_playing = MagicMock(return_value=True)
    with (
        patch("kinito.features.music.pygame.mixer.get_init", return_value=True),
        patch("kinito.features.music.pygame.mixer.music.pause") as pause,
        patch("kinito.features.music.pygame.mixer.music.unpause") as unpause,
    ):
        music.toggle_music_playback()
        pause.assert_called_once()
        assert music._music_paused is True
        music.toggle_music_playback()
        unpause.assert_called_once()
        assert music._music_paused is False


def test_set_music_volume_applies_and_persists(music):
    with (
        patch("kinito.features.music.pygame.mixer.get_init", return_value=True),
        patch("kinito.features.music.pygame.mixer.music.set_volume") as set_volume,
    ):
        music.set_music_volume(40)
    assert music._music_volume == 40
    set_volume.assert_called_once_with(0.4)
    music._persist_settings.assert_called()


def test_clamp_music_volume():
    assert clamp_music_volume(40) == 40
    assert clamp_music_volume(150) == 100
    assert clamp_music_volume(-5) == 0


def test_track_finished_advances_then_wraps(music, tmp_path):
    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    a.write_bytes(b"x")
    b.write_bytes(b"x")
    music._music_folder = str(tmp_path)
    music._reload_music_playlist()
    music._music_index = 0
    music._user_music_path = str(a)
    music._play_playlist_index = MagicMock()

    music._on_user_track_finished()
    music._play_playlist_index.assert_called_once_with(1, announce=False)

    music._music_index = 1
    music._user_music_path = str(b)
    music._play_playlist_index.reset_mock()
    music._on_user_track_finished()
    music._play_playlist_index.assert_called_once_with(0, announce=False)


def test_track_finished_repeats_one(music, tmp_path):
    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    a.write_bytes(b"x")
    b.write_bytes(b"x")
    music._music_folder = str(tmp_path)
    music._reload_music_playlist()
    music._music_index = 0
    music._music_repeat_mode = MusicMixin._MUSIC_REPEAT_ONE
    music._play_playlist_index = MagicMock()

    music._on_user_track_finished()
    music._play_playlist_index.assert_called_once_with(0, announce=False)


def test_toggle_music_shuffle_and_repeat(music):
    assert music._music_shuffle is False
    assert music._music_repeat_mode == MusicMixin._MUSIC_REPEAT_ALL
    music.toggle_music_shuffle()
    assert music._music_shuffle is True
    music._persist_settings.assert_called()
    music.toggle_music_repeat()
    assert music._music_repeat_mode == MusicMixin._MUSIC_REPEAT_ONE
    music.toggle_music_repeat()
    assert music._music_repeat_mode == MusicMixin._MUSIC_REPEAT_ALL


def test_open_music_player_applies_saved_shuffle(music, tmp_path):
    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    for path in (a, b):
        path.write_bytes(b"x")
    music._music_folder = str(tmp_path)
    music._music_shuffle = True
    music._show_music_player_window = MagicMock()
    music._play_playlist_index = MagicMock()
    music._user_music_is_active = MagicMock(return_value=False)
    with patch.object(music, "_reshuffle_playlist_from_current") as reshuffle:
        music.open_music_player()
    reshuffle.assert_called_once()
    music._show_music_player_window.assert_called_once()


def test_toggle_music_shuffle_puts_current_first(music, tmp_path):
    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    c = tmp_path / "c.mp3"
    for path in (a, b, c):
        path.write_bytes(b"x")
    music._music_folder = str(tmp_path)
    music._reload_music_playlist()
    music._music_index = 1
    music._user_music_path = str(b)
    with patch("kinito.features.music.random.shuffle") as shuffle_rest:
        music.toggle_music_shuffle()
    assert music._music_shuffle is True
    assert music._music_index == 0
    assert music._music_playlist[0] == str(b)
    assert set(music._music_playlist) == {str(a), str(b), str(c)}
    shuffle_rest.assert_called_once()
    assert set(shuffle_rest.call_args[0][0]) == {str(a), str(c)}


def test_toggle_music_shuffle_off_restores_sorted_order(music, tmp_path):
    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    c = tmp_path / "c.mp3"
    for path in (a, b, c):
        path.write_bytes(b"x")
    music._music_folder = str(tmp_path)
    music._music_playlist = [str(c), str(a), str(b)]
    music._music_index = 0
    music._user_music_path = str(c)
    music._music_shuffle = True
    music.toggle_music_shuffle()
    assert music._music_shuffle is False
    assert music._music_playlist == [str(a), str(b), str(c)]
    assert music._music_index == 2


def test_next_track_uses_shuffle_when_enabled(music, tmp_path):
    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    c = tmp_path / "c.mp3"
    for path in (a, b, c):
        path.write_bytes(b"x")
    music._music_folder = str(tmp_path)
    music._music_shuffle = False
    music._reload_music_playlist()
    music._music_index = 0
    music._music_shuffle = True
    music.play_user_mp3 = MagicMock()
    with patch("kinito.features.music.random.choice", return_value=2):
        music.play_next_track()
    music.play_user_mp3.assert_called_with(str(c), announce=False)


def test_next_track_follows_queue_order_when_shuffle_off(music, tmp_path):
    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    c = tmp_path / "c.mp3"
    for path in (a, b, c):
        path.write_bytes(b"x")
    music._music_folder = str(tmp_path)
    music._reload_music_playlist()
    music._music_index = 0
    music._music_shuffle = False
    music.play_user_mp3 = MagicMock()
    music.play_next_track()
    music.play_user_mp3.assert_called_with(str(b), announce=False)


def test_music_poll_waits_before_advancing(music):
    music._user_music_path = "song.mp3"
    music._is_background_music_playing = MagicMock(return_value=False)

    with patch("kinito.features.music.schedule_after") as schedule_after:
        music._schedule_user_music_poll()

    assert music._user_music_poll_misses == 1
    schedule_after.assert_called_once()
    assert schedule_after.call_args[0][3] == MusicMixin._MUSIC_POLL_INTERVAL_MS
    assert music._user_music_path == "song.mp3"


def test_music_poll_advances_after_grace_ticks(music):
    music._user_music_path = "song.mp3"
    music._music_playlist = ["song.mp3", "next.mp3"]
    music._music_index = 0
    music._user_music_poll_misses = MusicMixin._MUSIC_POLL_GRACE_TICKS - 1
    music._is_background_music_playing = MagicMock(return_value=False)
    music._play_playlist_index = MagicMock()
    music._schedule_user_music_poll()
    music._play_playlist_index.assert_called_once_with(1, announce=False)


def test_music_poll_ignores_not_playing_while_scrubbing(music):
    music._user_music_path = "song.mp3"
    music._music_scrubbing = True
    music._user_music_poll_misses = MusicMixin._MUSIC_POLL_GRACE_TICKS
    music._is_background_music_playing = MagicMock(return_value=False)
    music._on_user_track_finished = MagicMock()
    with patch("kinito.features.music.schedule_after") as schedule_after:
        music._schedule_user_music_poll()
    music._on_user_track_finished.assert_not_called()
    assert music._user_music_poll_misses == 0
    schedule_after.assert_called_once()


def test_probe_mp3_duration_fast_reads_xing_header(tmp_path):
    # Minimal MPEG-1 Layer III frame header + Xing with 100 frames @ 44100 Hz.
    # Duration = 100 * 1152 / 44100 ≈ 2.61s
    frame = bytearray(4 + 32 + 12)
    frame[0] = 0xFF
    frame[1] = 0xFB  # MPEG1, Layer III, no CRC
    frame[2] = 0x90  # 128 kbps, 44100 Hz
    frame[3] = 0x00  # stereo
    xing = 4 + 32
    frame[xing : xing + 4] = b"Xing"
    frame[xing + 4 : xing + 8] = (0x1).to_bytes(4, "big")  # frames flag
    frame[xing + 8 : xing + 12] = (100).to_bytes(4, "big")
    path = tmp_path / "xing.mp3"
    path.write_bytes(bytes(frame))
    duration = MusicMixin._probe_mp3_duration_fast(str(path))
    assert duration is not None
    assert abs(duration - (100 * 1152 / 44100)) < 0.01


def test_stop_user_music_stops_playback_and_speaks(music):
    music._user_music_path = "song.mp3"
    with patch("kinito.features.music.dlg.pick_line", return_value="Stopped."):
        music.stop_user_music()
    music.stop_background_music.assert_called_once()
    music.speak.assert_called_once_with("Stopped.")


def test_on_background_music_stopped_clears_state(music):
    music._user_music_path = "song.mp3"
    music._music_paused = True
    music._on_background_music_stopped()
    assert music._user_music_path is None
    assert music._music_paused is False


def test_toggle_player_kinito_mute_updates_state_and_interrupts(music):
    music.interrupt_speech = MagicMock()
    music._refresh_music_player_ui = MagicMock()
    assert music._is_player_kinito_muted() is False
    music.toggle_player_kinito_mute()
    assert music._is_player_kinito_muted() is True
    music.interrupt_speech.assert_called_once()
    music.toggle_player_kinito_mute()
    assert music._is_player_kinito_muted() is False
    music._refresh_music_player_ui.assert_called()


def test_close_music_player_stops_playback(music):
    music._user_music_path = "song.mp3"
    fake_window = MagicMock()
    music._music_player_window = fake_window
    music._music_player_widgets = {"song": MagicMock()}
    music._close_music_player_window()
    music.stop_background_music.assert_called_once()
    fake_window.destroy.assert_called_once()
    assert music._music_player_window is None


def test_close_music_player_clears_kinito_mute(music):
    music._player_kinito_muted = True
    music._music_player_window = MagicMock()
    music._music_player_widgets = {}
    music._close_music_player_window()
    assert music._is_player_kinito_muted() is False


def test_toggle_music_volume_popup_opens_and_closes(music):
    player = MagicMock()
    player.winfo_exists.return_value = True
    player.state.return_value = "normal"
    music._music_player_window = player
    anchor = MagicMock()
    anchor.winfo_rootx.return_value = 100
    anchor.winfo_rooty.return_value = 200
    anchor.winfo_width.return_value = 32
    music._music_player_widgets = {"volume_btn": anchor}

    fake_popup = MagicMock()
    fake_scale = MagicMock()
    with patch("kinito.features.music.tk.Toplevel", return_value=fake_popup) as toplevel:
        with patch("kinito.features.music.tk.Frame", return_value=MagicMock()):
            with patch("kinito.features.music.tk.Scale", return_value=fake_scale):
                music.toggle_music_volume_popup()
    toplevel.assert_called_once_with(player)
    assert music._music_volume_popup is fake_popup
    fake_scale.set.assert_called_once_with(75)
    fake_scale.configure.assert_called_once()
    assert "command" in fake_scale.configure.call_args.kwargs

    music.toggle_music_volume_popup()
    fake_popup.destroy.assert_called_once()
    assert music._music_volume_popup is None


def test_volume_popup_closes_on_outside_click(music):
    popup = MagicMock()
    popup.winfo_exists.return_value = True
    popup.winfo_rootx.return_value = 50
    popup.winfo_rooty.return_value = 50
    popup.winfo_width.return_value = 100
    popup.winfo_height.return_value = 40
    music._music_volume_popup = popup
    volume_btn = MagicMock()
    volume_btn.winfo_rootx.return_value = 10
    volume_btn.winfo_rooty.return_value = 100
    volume_btn.winfo_width.return_value = 32
    volume_btn.winfo_height.return_value = 32
    music._music_player_widgets = {"volume_btn": volume_btn}

    outside = MagicMock(x_root=300, y_root=300)
    music._on_music_volume_outside_click(outside)
    popup.destroy.assert_called_once()
    assert music._music_volume_popup is None


def test_volume_popup_stays_open_for_inside_click(music):
    popup = MagicMock()
    popup.winfo_exists.return_value = True
    popup.winfo_rootx.return_value = 50
    popup.winfo_rooty.return_value = 50
    popup.winfo_width.return_value = 100
    popup.winfo_height.return_value = 40
    music._music_volume_popup = popup
    music._music_player_widgets = {"volume_btn": MagicMock()}

    inside = MagicMock(x_root=70, y_root=60)
    music._on_music_volume_outside_click(inside)
    popup.destroy.assert_not_called()
    assert music._music_volume_popup is popup


def test_volume_popup_does_not_persist_initial_zero(music):
    music._music_volume = 75
    music.set_music_volume = MagicMock()
    player = MagicMock()
    player.winfo_exists.return_value = True
    player.state.return_value = "normal"
    music._music_player_window = player
    music._music_player_widgets = {
        "volume_btn": MagicMock(
            winfo_rootx=MagicMock(return_value=10),
            winfo_rooty=MagicMock(return_value=20),
            winfo_width=MagicMock(return_value=32),
            update_idletasks=MagicMock(),
        )
    }

    created = {}

    def fake_scale(*_args, **kwargs):
        scale = MagicMock()

        def configure(**cfg):
            if "command" in cfg:
                created["command"] = cfg["command"]

        scale.configure.side_effect = configure
        created["scale"] = scale
        return scale

    with patch("kinito.features.music.tk.Toplevel", return_value=MagicMock()):
        with patch("kinito.features.music.tk.Frame", return_value=MagicMock()):
            with patch("kinito.features.music.tk.Scale", side_effect=fake_scale):
                music._show_music_volume_popup()

    music.set_music_volume.assert_not_called()
    created["scale"].set.assert_called_once_with(75)
    assert "command" in created


def test_refresh_track_picker_selection_updates_highlight_only(music):
    current_btn = MagicMock()
    current_btn.cget.return_value = "#e6ded5"
    other_btn = MagicMock()
    other_btn.cget.return_value = MusicMixin._MUSIC_LIST_SELECTED_BG
    music._music_track_picker_buttons = {
        "a.mp3": other_btn,
        "b.mp3": current_btn,
    }
    music._music_track_picker_window = MagicMock()
    music._music_track_picker_window.winfo_exists.return_value = True
    music._user_music_path = "b.mp3"
    music._music_playlist = ["a.mp3", "b.mp3"]
    music._music_index = 1

    music._refresh_music_track_picker_selection()

    assert other_btn._kinito_normal_bg == MusicMixin._MUSIC_UI_BG
    assert current_btn._kinito_normal_bg == MusicMixin._MUSIC_LIST_SELECTED_BG
    other_btn.configure.assert_called_with(bg=MusicMixin._MUSIC_UI_BG)
    current_btn.configure.assert_called_with(bg=MusicMixin._MUSIC_LIST_SELECTED_BG)


def test_pick_music_track_plays_and_closes_picker(music, tmp_path):
    a = tmp_path / "Alpha Song.mp3"
    b = tmp_path / "Beta Song.mp3"
    for path in (a, b):
        path.write_bytes(b"x")
    music._music_playlist = [str(a), str(b)]
    music._music_index = 0
    music._play_playlist_index = MagicMock()
    music._close_music_track_picker = MagicMock()
    music._pick_music_track(str(b))
    music._close_music_track_picker.assert_called_once()
    music._play_playlist_index.assert_called_once_with(1, announce=False)


def test_toggle_music_track_picker_opens_when_closed(music):
    music._is_music_track_picker_open = MagicMock(return_value=False)
    music._show_music_track_picker = MagicMock()
    music.toggle_music_track_picker()
    music._show_music_track_picker.assert_called_once()


def test_close_player_closes_track_picker(music):
    music._close_music_track_picker = MagicMock()
    music._close_music_volume_popup = MagicMock()
    music._user_music_path = None
    fake_window = MagicMock()
    music._music_player_window = fake_window
    music._close_music_player_window()
    music._close_music_track_picker.assert_called_once()
    fake_window.destroy.assert_called_once()


def test_minimize_closes_volume_and_track_popups(music):
    music._close_music_volume_popup = MagicMock()
    music._close_music_track_picker = MagicMock()
    window = MagicMock()
    window.winfo_exists.return_value = True
    music._music_player_window = window
    music._minimize_music_player_window()
    music._close_music_volume_popup.assert_called_once()
    music._close_music_track_picker.assert_called_once()
    window.withdraw.assert_called_once()


def test_minimize_music_player_hides_without_stopping(music):
    music._user_music_path = "song.mp3"
    fake_window = MagicMock()
    fake_window.winfo_exists.return_value = True
    music._music_player_window = fake_window
    music._minimize_music_player_window()
    fake_window.withdraw.assert_called_once()
    music.stop_background_music.assert_not_called()
    assert music._music_player_window is fake_window


def test_is_music_player_minimized(music):
    assert music._is_music_player_minimized() is False

    window = MagicMock()
    window.winfo_exists.return_value = True
    window.state.return_value = "normal"
    music._music_player_window = window
    assert music._is_music_player_minimized() is False

    window.state.return_value = "withdrawn"
    assert music._is_music_player_minimized() is True


def test_show_music_player_restores_minimized_window(music):
    window = MagicMock()
    window.winfo_exists.return_value = True
    window.state.return_value = "withdrawn"
    music._music_player_window = window
    music._refresh_music_player_ui = MagicMock()
    music._silence_for_player_focus = MagicMock()

    music._show_music_player_window()

    window.deiconify.assert_called_once()
    window.lift.assert_called_once()
    window.focus_force.assert_called_once()
    music._refresh_music_player_ui.assert_called_once()
    music._silence_for_player_focus.assert_called_once()


def test_choose_music_folder_saves_and_reloads(music, tmp_path):
    (tmp_path / "track.mp3").write_bytes(b"x")
    with patch("kinito.features.music.filedialog.askdirectory", return_value=str(tmp_path)):
        assert music.choose_music_folder() is True
    assert music._music_folder == str(tmp_path)
    assert len(music._music_playlist) == 1
    music._persist_settings.assert_called()


def test_open_music_player_requires_folder(music):
    music._music_folder = ""
    with patch.object(music, "choose_music_folder", return_value=False) as choose:
        music.open_music_player()
    choose.assert_called_once()
    music.speak.assert_not_called()


def test_offer_random_music_asks_first(music):
    with patch("kinito.features.music.dlg.pick_line", return_value="Want music?"):
        music.offer_random_music()
    music.speak.assert_called_once_with("Want music?", 45, True)


def test_bind_music_player_button_hover_swaps_colors():
    button = MagicMock()
    MusicMixin._bind_music_player_button_hover(
        button,
        "#d9d9d9",
        "#c4c4c4",
        normal_fg="#111111",
        hover_fg="#ffffff",
    )
    assert button.bind.call_count == 2
    enter = button.bind.call_args_list[0][0][1]
    leave = button.bind.call_args_list[1][0][1]
    enter()
    button.configure.assert_any_call(bg="#c4c4c4")
    button.configure.assert_any_call(fg="#ffffff")
    button.configure.reset_mock()
    leave()
    button.configure.assert_any_call(bg="#d9d9d9")
    button.configure.assert_any_call(fg="#111111")


def test_format_queue_position():
    assert MusicMixin._format_queue_position(0, 87) == "1/87"
    assert MusicMixin._format_queue_position(4, 87) == "5/87"
    assert MusicMixin._format_queue_position(0, 0) == "0/0"


def test_format_track_duration():
    assert MusicMixin._format_track_duration(65) == "1:05"
    assert MusicMixin._format_track_duration(0) == "0:00"
    assert MusicMixin._format_track_duration(None) == "0:00"


def test_update_music_progress_ui_fills_bar(music):
    elapsed = MagicMock()
    total = MagicMock()
    bar = MagicMock()
    bar.winfo_width.return_value = 200
    bar.winfo_height.return_value = 10
    music._music_player_widgets = {
        "elapsed": elapsed,
        "total": total,
        "progress_bar": bar,
        "progress_fill": 1,
    }
    music._user_music_path = "song.mp3"
    music._music_track_duration = 100.0
    music._music_track_duration_path = "song.mp3"
    with patch.object(music, "_get_music_elapsed_seconds", return_value=25.0):
        music._update_music_progress_ui()
    elapsed.config.assert_called_once_with(text="0:25")
    total.config.assert_called_once_with(text="1:40")
    bar.coords.assert_called_once_with(1, 0, 0, 50, 10)


def test_music_progress_seconds_from_event(music):
    music._user_music_path = "song.mp3"
    music._music_track_duration = 100.0
    music._music_track_duration_path = "song.mp3"
    bar = MagicMock()
    bar.winfo_width.return_value = 200
    music._music_player_widgets = {"progress_bar": bar}
    event = MagicMock(x=50)
    assert music._music_progress_seconds_from_event(event) == 25.0


def test_progress_press_pauses_while_scrubbing(music):
    music._user_music_path = "song.mp3"
    music._music_paused = False
    music._is_background_music_playing = MagicMock(return_value=True)
    music._music_progress_seconds_from_event = MagicMock(return_value=12.0)
    music._update_music_progress_ui = MagicMock()
    with (
        patch("kinito.features.music.pygame.mixer.get_init", return_value=True),
        patch("kinito.features.music.pygame.mixer.music.pause") as pause,
    ):
        music._on_music_progress_press(MagicMock(x=10))
    assert music._music_scrubbing is True
    assert music._music_scrub_seconds == 12.0
    assert music._music_was_playing_before_scrub is True
    pause.assert_called_once()


def test_progress_release_seeks_and_resumes(music):
    music._music_scrubbing = True
    music._music_scrub_seconds = 8.0
    music._music_was_playing_before_scrub = True
    music._music_progress_seconds_from_event = MagicMock(return_value=20.0)
    music._seek_user_music = MagicMock()
    music._on_music_progress_release(MagicMock(x=40))
    music._seek_user_music.assert_called_once_with(20.0, resume=True)
    assert music._music_scrubbing is False


def test_get_music_elapsed_seconds_from_pygame(music):
    music._user_music_path = "song.mp3"
    music._music_track_duration = 120.0
    with (
        patch("kinito.features.music.pygame.mixer.get_init", return_value=True),
        patch("kinito.features.music.pygame.mixer.music.get_pos", return_value=4500),
    ):
        assert music._get_music_elapsed_seconds() == 4.5


def test_player_focus_active_requires_open_player(music):
    music._player_focus_enabled = True
    assert music._player_focus_active() is False

    window = MagicMock()
    window.winfo_exists.return_value = True
    music._music_player_window = window
    assert music._player_focus_active() is True

    music._player_focus_enabled = False
    assert music._player_focus_active() is False


def test_toggle_player_focus_persists_and_confirms(music):
    music._player_focus_enabled = True
    with patch("kinito.features.music.dlg.pick_line", return_value="Quiet off."):
        music.toggle_player_focus()
    assert music._player_focus_enabled is False
    music._persist_settings.assert_called()
    music.speak.assert_called_once_with("Quiet off.", skip_ai=True, allow_in_focus=True)


def test_silence_for_player_focus_interrupts_speech(music):
    music.interrupt_speech = MagicMock()
    music._player_focus_enabled = True
    window = MagicMock()
    window.winfo_exists.return_value = True
    music._music_player_window = window
    music._silence_for_player_focus()
    music.interrupt_speech.assert_called_once()


def test_silence_for_player_focus_skips_when_disabled(music):
    music.interrupt_speech = MagicMock()
    music._player_focus_enabled = False
    window = MagicMock()
    window.winfo_exists.return_value = True
    music._music_player_window = window
    music._silence_for_player_focus()
    music.interrupt_speech.assert_not_called()
