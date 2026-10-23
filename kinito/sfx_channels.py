"""Catalog of adjustable sound-effect / accompaniment channels."""

from __future__ import annotations

import os
from typing import TypedDict

from kinito.assets import (
    bomp_file_path,
    newbeginnings_file_path,
    page_turn_file_path,
    snoring_file_path,
    starttalk_file_path,
    stoptalk_file_path,
    surf_file_path,
    timer_file_path,
    tune_file_path,
    woosh_file_path,
)


class SfxChannel(TypedDict):
    id: str
    label: str
    path: str
    kind: str  # "sfx" (Sound) or "music" (mixer.music accompaniment)


# Order is menu order. "magic" is the fancy/magician TinyTune accompaniment.
SFX_CHANNELS: tuple[SfxChannel, ...] = (
    {
        "id": "surf",
        "label": "Surf",
        "path": surf_file_path,
        "kind": "sfx",
    },
    {
        "id": "magic",
        "label": "Magic",
        "path": tune_file_path,
        "kind": "music",
    },
    {
        "id": "poem",
        "label": "Poem",
        "path": newbeginnings_file_path,
        "kind": "music",
    },
    {
        "id": "bubble_open",
        "label": "Bubble Open",
        "path": starttalk_file_path,
        "kind": "sfx",
    },
    {
        "id": "bubble_close",
        "label": "Bubble Close",
        "path": stoptalk_file_path,
        "kind": "sfx",
    },
    {
        "id": "reading",
        "label": "Reading",
        "path": page_turn_file_path,
        "kind": "sfx",
    },
    {
        "id": "woosh",
        "label": "Throw",
        "path": woosh_file_path,
        "kind": "sfx",
    },
    {
        "id": "bomp",
        "label": "Bomp",
        "path": bomp_file_path,
        "kind": "sfx",
    },
    {
        "id": "snoring",
        "label": "Snoring",
        "path": snoring_file_path,
        "kind": "sfx",
    },
    {
        "id": "timer",
        "label": "Timer",
        "path": timer_file_path,
        "kind": "sfx",
    },
)

SFX_CHANNEL_IDS: frozenset[str] = frozenset(channel["id"] for channel in SFX_CHANNELS)


def _norm_path(path: str) -> str:
    return os.path.normcase(os.path.normpath(path))


_PATH_TO_CHANNEL: dict[str, str] = {
    _norm_path(channel["path"]): channel["id"] for channel in SFX_CHANNELS
}


def channel_id_for_path(path: str | None) -> str | None:
    """Return the channel id for a sound file path, or None if unlisted."""
    if not path:
        return None
    return _PATH_TO_CHANNEL.get(_norm_path(path))


def channel_by_id(channel_id: str) -> SfxChannel | None:
    """Return the catalog entry for *channel_id*, or None."""
    for channel in SFX_CHANNELS:
        if channel["id"] == channel_id:
            return channel
    return None


def channel_label(channel_id: str) -> str:
    """Human label for *channel_id*."""
    channel = channel_by_id(channel_id)
    if channel is None:
        return channel_id.replace("_", " ").title()
    return channel["label"]
