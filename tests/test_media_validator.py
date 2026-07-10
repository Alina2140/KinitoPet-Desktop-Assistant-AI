import os

import pytest

from content.allowed_videos import ALLOWED_VIDEOS
from content.media_validator import (
    is_allowed_image_path,
    is_allowed_video_path,
    is_allowed_video_url,
    pick_random_image,
    pick_random_video,
)


@pytest.mark.parametrize(
    "url",
    [
        "https://science.nasa.gov/earth/earth-at-night/",
        "https://science.nasa.gov/earth/earth-at-night",
        "https://zoo.sandiegozoo.org/live-cams",
        "https://www.nationalgeographic.com/environment",
    ],
)
def test_allowed_video_urls(url):
    assert is_allowed_video_url(url) is True


@pytest.mark.parametrize(
    "url",
    [
        "",
        "http://science.nasa.gov/earth/earth-at-night/",
        "https://evil.example.com/video",
        "https://192.168.1.1/stream",
        "file:///tmp/video.mp4",
    ],
)
def test_blocked_video_urls(url):
    assert is_allowed_video_url(url) is False


def test_subdomain_of_allowed_video_host_is_permitted():
    assert is_allowed_video_url("https://blog.nationalgeographic.com/environment") is True


def test_pick_random_video_returns_local_or_url(tmp_path, monkeypatch):
    media_dir = tmp_path / "UserMedia"
    videos_dir = media_dir / "videos"
    media_dir.mkdir()
    videos_dir.mkdir()
    image = media_dir / "cat.png"
    image.write_bytes(b"fake")
    video = videos_dir / "clip.mp4"
    video.write_bytes(b"fake")

    monkeypatch.setattr("content.media_validator.user_media_directory", str(media_dir))
    monkeypatch.setattr("content.media_validator.user_videos_directory", str(videos_dir))

    assert is_allowed_image_path(str(image)) is True
    assert is_allowed_video_path(str(video)) is True
    assert is_allowed_image_path(str(videos_dir / "clip.mp4")) is False
    assert is_allowed_video_path(str(image)) is False

    picked_image = pick_random_image()
    assert picked_image == str(image)

    choice = pick_random_video()
    assert choice is not None
    assert choice[0] in {"local", "url"}
    if choice[0] == "url":
        assert choice[1] in [video for videos in ALLOWED_VIDEOS.values() for video in videos]


def test_pick_random_image_empty_folder(tmp_path, monkeypatch):
    media_dir = tmp_path / "UserMedia"
    media_dir.mkdir()
    monkeypatch.setattr("content.media_validator.user_media_directory", str(media_dir))
    monkeypatch.setattr("content.media_validator.user_videos_directory", str(media_dir / "videos"))
    assert pick_random_image() is None


def test_path_traversal_blocked(tmp_path, monkeypatch):
    media_dir = tmp_path / "UserMedia"
    media_dir.mkdir()
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"fake")
    link = media_dir / "escape.png"
    try:
        os.symlink(outside, link)
    except OSError:
        pytest.skip("symlinks not supported")

    monkeypatch.setattr("content.media_validator.user_media_directory", str(media_dir))
    assert is_allowed_image_path(str(link)) is False
