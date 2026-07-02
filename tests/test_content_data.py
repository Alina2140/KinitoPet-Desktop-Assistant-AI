"""Tests for all content data modules — text pools, structure, placeholders."""

from unittest.mock import patch

import pytest

from content import dialogue as dlg
from content.allowed_sites import ALLOWED_SITES
from content.browser_lines import BROWSER_LINES, HORROR_BROWSER_LINES
from content.camera_lines import CAMERA_LINES
from content.facts import FACTS, KINITO_FACT_WEIGHT, KINITO_FACTS, get_random_fact
from content.fancy_lines import FANCY_LINES
from content.goodbye_lines import GOODBYE_LINES
from content.hug_lines import HUG_ASK_LINES, HUG_LINES
from content.music_player_lines import MUSIC_PLAYER_LINES
from content.poems import POEMS
from content.startup import STARTUP_LINES
from content.stories import STORIES
from content.wisdom import WISDOM, format_wisdom_line, get_random_wisdom, load_quotes


def _assert_non_empty_strings(items, *, min_length=1):
    assert len(items) >= 1
    for item in items:
        assert isinstance(item, str)
        assert len(item.strip()) >= min_length


@pytest.mark.parametrize(
    "pool,name",
    [
        (STARTUP_LINES, "startup"),
        (GOODBYE_LINES, "goodbye"),
        (FACTS, "facts"),
        (STORIES, "stories"),
        (WISDOM, "wisdom"),
        (FANCY_LINES, "fancy"),
        (HUG_LINES, "hug"),
        (HUG_ASK_LINES, "hug_ask"),
        (BROWSER_LINES, "browser"),
        (HORROR_BROWSER_LINES, "horror_browser"),
        (CAMERA_LINES, "camera"),
        (MUSIC_PLAYER_LINES, "music_player"),
    ],
)
def test_content_pools_are_non_empty(pool, name):
    _assert_non_empty_strings(pool, min_length=10)


def test_poems_have_required_fields():
    assert len(POEMS) >= 1
    for poem in POEMS:
        assert isinstance(poem, dict)
        assert isinstance(poem["text"], str) and poem["text"].strip()
        assert isinstance(poem.get("whisper", False), bool)
        assert isinstance(poem.get("play_music", False), bool)


def test_quotes_json_loads_and_formats():
    quotes = load_quotes()
    assert len(quotes) >= 10
    for entry in quotes:
        assert entry["quote"].strip()
        line = format_wisdom_line(entry, "Test intro:")
        assert line.startswith("Test intro:")
        assert entry["quote"] in line


def test_get_random_wisdom_uses_quote_pool():
    line = get_random_wisdom()
    assert isinstance(line, str)
    assert len(line.strip()) >= 10


def test_music_player_lines_support_song_placeholder():
    for line in MUSIC_PLAYER_LINES:
        formatted = line.format(song="Test Song")
        assert "Test Song" in formatted
        assert "{song}" not in formatted


@pytest.mark.parametrize(
    "template",
    [
        dlg.COLOR_RESPONSES[0],
        dlg.HOBBY_RESPONSES[0],
        dlg.FOOD_RESPONSES[0],
        dlg.NAME_RESPONSES[0],
        dlg.TIME_RESPONSES[0],
    ],
)
def test_format_templates_accept_placeholders(template):
    if "{response}" in template:
        result = template.format(response="test")
    elif "{time}" in template:
        result = template.format(time="12:34")
    else:
        pytest.fail(f"Unknown placeholder pattern: {template!r}")
    assert "test" in result or "12:34" in result


def test_allowed_sites_structure():
    assert len(ALLOWED_SITES) >= 4
    for category, sites in ALLOWED_SITES.items():
        assert isinstance(category, str) and category
        assert len(sites) >= 1
        for site in sites:
            assert "title" in site and site["title"].strip()
            assert site["url"].startswith("https://")


def test_all_allowed_site_urls_are_https():
    from content.site_validator import is_allowed_url

    for sites in ALLOWED_SITES.values():
        for site in sites:
            assert is_allowed_url(site["url"]) is True


def test_kinito_fact_weight_is_in_target_range():
    assert 0.30 <= KINITO_FACT_WEIGHT <= 0.35


def test_get_random_fact_uses_kinito_pool_when_weight_hits():
    with patch("content.facts.random.random", return_value=0.0):
        with patch("content.facts.random.choice", return_value=KINITO_FACTS[0]) as choice:
            assert get_random_fact() == KINITO_FACTS[0]
            choice.assert_called_once_with(KINITO_FACTS)


def test_get_random_fact_uses_randfacts_when_weight_misses():
    with patch("content.facts.random.random", return_value=0.99):
        with patch("content.facts.randfacts.get_fact", return_value="library fact") as get_fact:
            assert get_random_fact() == "library fact"
            get_fact.assert_called_once()


def test_dialogue_line_pools_not_empty():
    pools = [
        dlg.PAUSE_LINES,
        dlg.UNPAUSE_LINES,
        dlg.JOKES,
        dlg.COMPLIMENTS,
        dlg.DECLINED_ACK_LINES,
        dlg.BROWSER_DECLINED_LINES,
        dlg.CAMERA_DECLINED_LINES,
        dlg.MUSIC_PLAYER_DECLINED_LINES,
        dlg.STORY_DECLINED_LINES,
        dlg.REMINDER_DONE_LINES,
    ]
    for pool in pools:
        _assert_non_empty_strings(pool)
