"""Tests for the SFX channel catalog and volume helpers."""

from __future__ import annotations

from kinito.sfx_channels import (
    SFX_CHANNEL_IDS,
    SFX_CHANNELS,
    channel_by_id,
    channel_id_for_path,
    channel_label,
)


def test_sfx_channels_have_unique_ids_and_paths():
    ids = [channel["id"] for channel in SFX_CHANNELS]
    paths = [channel["path"] for channel in SFX_CHANNELS]
    assert len(ids) == len(set(ids))
    assert len(paths) == len(set(paths))
    assert frozenset(ids) == SFX_CHANNEL_IDS


def test_channel_id_for_path_roundtrip():
    for channel in SFX_CHANNELS:
        assert channel_id_for_path(channel["path"]) == channel["id"]
        assert channel_by_id(channel["id"]) == channel
        assert channel_label(channel["id"]) == channel["label"]
    assert channel_id_for_path("missing.mp3") is None
    assert channel_by_id("nope") is None
