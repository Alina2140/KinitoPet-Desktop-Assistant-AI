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


def test_play_user_mp3_rejects_non_mp3(music):
    music.play_user_mp3("song.wav")
    music.speak.assert_called_once()


def test_play_user_mp3_rejects_missing_file(music):
    music.play_user_mp3("missing.mp3")
    music.speak.assert_called_once()


def test_play_user_mp3_plays_and_announces(music, tmp_path):
    mp3 = tmp_path / "My Song.mp3"
    mp3.write_bytes(b"x")
    with (
        patch("kinito.features.music.random.choice", return_value="Playing {song}!"),
        patch("kinito.features.music.threading.Thread") as thread_cls,
    ):
        music.play_user_mp3(str(mp3))
    music.play_mp3.assert_called_once_with(str(mp3), volume=0.75)
    assert music._user_music_path == str(mp3)
    thread_cls.assert_called_once()


def test_play_user_mp3_can_skip_announce(music, tmp_path):
    mp3 = tmp_path / "Quiet.mp3"
    mp3.write_bytes(b"x")
    with patch("kinito.features.music.threading.Thread") as thread_cls:
        music.play_user_mp3(str(mp3), announce=False)
    thread_cls.assert_not_called()


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
    music.toggle_music_repeat()
    assert music._music_repeat_mode == MusicMixin._MUSIC_REPEAT_ONE
    music.toggle_music_repeat()
    assert music._music_repeat_mode == MusicMixin._MUSIC_REPEAT_ALL


def test_next_track_uses_shuffle(music, tmp_path):
    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    c = tmp_path / "c.mp3"
    for path in (a, b, c):
        path.write_bytes(b"x")
    music._music_folder = str(tmp_path)
    music._reload_music_playlist()
    music._music_index = 0
    music._music_shuffle = True
    music.play_user_mp3 = MagicMock()
    with patch("kinito.features.music.random.choice", return_value=2):
        music.play_next_track()
    music.play_user_mp3.assert_called_with(str(c), announce=False)


def test_music_poll_waits_before_advancing(music):
    music._user_music_path = "song.mp3"
    music._is_background_music_playing = MagicMock(return_value=False)

    with patch("kinito.features.music.schedule_after") as schedule_after:
        music._schedule_user_music_poll()

    assert music._user_music_poll_misses == 1
    schedule_after.assert_called_once()
    assert music._user_music_path == "song.mp3"


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


def test_close_music_player_stops_playback(music):
    music._user_music_path = "song.mp3"
    fake_window = MagicMock()
    music._music_player_window = fake_window
    music._music_player_widgets = {"song": MagicMock()}
    music._close_music_player_window()
    music.stop_background_music.assert_called_once()
    fake_window.destroy.assert_called_once()
    assert music._music_player_window is None


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


def test_format_track_duration():
    assert MusicMixin._format_track_duration(65) == "1:05"
    assert MusicMixin._format_track_duration(None) == "--:--"
