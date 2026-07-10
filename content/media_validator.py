"""Allow-list helpers for user media images, local videos, and curated video URLs."""

import os
import random
from urllib.parse import urlparse

from content.allowed_videos import ALLOWED_VIDEOS
from kinito.assets import (
    list_image_files,
    list_video_files,
    user_media_directory,
    user_videos_directory,
)

_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
_VIDEO_EXTENSIONS = (".mp4", ".webm", ".mov", ".mkv", ".avi")

_ALLOWED_VIDEO_URLS = set()
_URL_TO_VIDEO = {}
_ALLOWED_VIDEO_HOSTS = set()

for _category, _videos in ALLOWED_VIDEOS.items():
    for _video in _videos:
        _url = _video["url"].rstrip("/")
        _ALLOWED_VIDEO_URLS.add(_video["url"])
        _ALLOWED_VIDEO_URLS.add(_url)
        _URL_TO_VIDEO[_video["url"]] = _video
        _URL_TO_VIDEO[_url] = _video
        _host = urlparse(_video["url"]).netloc.lower()
        if _host:
            _ALLOWED_VIDEO_HOSTS.add(_host)
            if _host.startswith("www."):
                _ALLOWED_VIDEO_HOSTS.add(_host[4:])


def _normalize_url(url):
    """Strip a trailing slash for consistent URL lookup."""
    return url.rstrip("/")


def _normalize_host(netloc):
    """Lowercase host without port; strip leading www."""
    host = netloc.lower().split(":")[0]
    if host.startswith("www."):
        return host[4:]
    return host


def _hostname_allowed(netloc):
    """Return True if *netloc* matches an allowed host or subdomain."""
    host = _normalize_host(netloc)
    if not host:
        return False
    if host in _ALLOWED_VIDEO_HOSTS:
        return True
    return any(host == allowed or host.endswith(f".{allowed}") for allowed in _ALLOWED_VIDEO_HOSTS)


def _path_inside_directory(path, directory):
    """Return True when *path* resolves to a file inside *directory*."""
    if not path or not directory:
        return False
    try:
        real_path = os.path.realpath(path)
        real_dir = os.path.realpath(directory)
    except OSError:
        return False
    if not os.path.isfile(real_path):
        return False
    common = os.path.commonpath([real_path, real_dir])
    return common == real_dir


def is_allowed_image_path(path):
    """Return True only for image files inside GameAssets/UserMedia/."""
    if not path:
        return False
    if not path.lower().endswith(_IMAGE_EXTENSIONS):
        return False
    return _path_inside_directory(path, user_media_directory)


def is_allowed_video_path(path):
    """Return True only for video files inside GameAssets/UserMedia/videos/."""
    if not path:
        return False
    if not path.lower().endswith(_VIDEO_EXTENSIONS):
        return False
    return _path_inside_directory(path, user_videos_directory)


def is_allowed_video_url(url):
    """Return True only for HTTPS URLs on the configured video allow-list."""
    if not url:
        return False

    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False
    if not parsed.netloc:
        return False
    if parsed.netloc.replace(".", "").isdigit():
        return False

    normalized = _normalize_url(url)
    if url in _ALLOWED_VIDEO_URLS or normalized in _ALLOWED_VIDEO_URLS:
        return True

    return _hostname_allowed(parsed.netloc)


def get_video_by_url(url):
    """Look up video metadata dict for an allowed URL."""
    return _URL_TO_VIDEO.get(url) or _URL_TO_VIDEO.get(_normalize_url(url))


def list_allowed_images():
    """Return validated image paths from the user media folder."""
    return [path for path in list_image_files(user_media_directory) if is_allowed_image_path(path)]


def list_allowed_local_videos():
    """Return validated video paths from the user videos folder."""
    return [path for path in list_video_files(user_videos_directory) if is_allowed_video_path(path)]


def pick_random_image():
    """Return a random allowed user image path, or None if the folder is empty."""
    images = list_allowed_images()
    if not images:
        return None
    return random.choice(images)


def pick_random_video():
    """Return ('local', path) or ('url', video_dict), or None if nothing is available."""
    local_videos = list_allowed_local_videos()
    remote_videos = [video for videos in ALLOWED_VIDEOS.values() for video in videos]
    pool: list[tuple[str, object]] = [("local", path) for path in local_videos]
    pool.extend(("url", video) for video in remote_videos)
    if not pool:
        return None
    return random.choice(pool)


def pick_random_video_category():
    """Return a random key from ALLOWED_VIDEOS."""
    return random.choice(list(ALLOWED_VIDEOS.keys()))


def pick_random_video_from_category(category):
    """Return a random video dict from *category*, or None if empty."""
    videos = ALLOWED_VIDEOS.get(category)
    if not videos:
        return None
    return random.choice(videos)
