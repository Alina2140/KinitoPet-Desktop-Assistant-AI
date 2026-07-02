from unittest.mock import MagicMock, patch

import pytest

from kinito.features.music import MusicMixin


class MusicStub(MusicMixin):
    pass


@pytest.fixture
def music():
    stub = MusicStub()
    stub.speak = MagicMock()
    stub.play_mp3 = MagicMock()
    stub.root = MagicMock()
    stub._is_busy_with_speech = MagicMock(return_value=False)
    return stub


def test_find_mp3_files_in_tmp_tree(music, tmp_path):
    music_dir = tmp_path / "Music"
    music_dir.mkdir()
    (music_dir / "song1.mp3").write_bytes(b"x")
    (music_dir / "song2.MP3").write_bytes(b"x")
    sub = music_dir / "nested"
    sub.mkdir()
    (sub / "deep.mp3").write_bytes(b"x")

    with patch.object(music, "_music_search_roots", return_value=[str(music_dir)]):
        files = music._find_mp3_files()
    assert len(files) == 3
    assert all(f.lower().endswith(".mp3") for f in files)


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
    thread_cls.assert_called_once()


def test_play_random_mp3_no_files(music):
    with patch.object(music, "_find_mp3_files", return_value=[]):
        music.play_random_mp3()
    music.speak.assert_called_once()


def test_ask_music_player_pick_skips_when_busy(music):
    music._is_busy_with_speech.return_value = True
    music.ask_music_player_pick()
    music.speak.assert_not_called()


def test_offer_random_music_asks_first(music):
    with patch("kinito.features.music.dlg.pick_line", return_value="Want music?"):
        music.offer_random_music()
    music.speak.assert_called_once_with("Want music?", 45, True)
