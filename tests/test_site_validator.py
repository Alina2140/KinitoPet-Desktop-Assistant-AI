import pytest

from content.allowed_sites import ALLOWED_SITES
from content.site_validator import (
    get_site_by_url,
    is_allowed_url,
    pick_random_category,
    pick_random_site,
)


@pytest.mark.parametrize(
    "url",
    [
        "https://www.nationalgeographic.com/animals",
        "https://www.nationalgeographic.com/animals/",
        "https://nationalgeographic.com/animals",
        "https://spaceplace.nasa.gov/",
        "https://www.kinitopet.com/",
        "https://kinito-interactive.itch.io/kinitopet",
    ],
)
def test_allowed_urls_and_host_variants(url):
    assert is_allowed_url(url) is True


@pytest.mark.parametrize(
    "url",
    [
        "",
        "http://www.nationalgeographic.com/animals",
        "ftp://www.nationalgeographic.com/animals",
        "https://evil.example.com",
        "https://192.168.1.1",
        "https://10.0.0.1/admin",
        "javascript:alert(1)",
        "file:///etc/passwd",
    ],
)
def test_blocked_urls(url):
    assert is_allowed_url(url) is False


def test_subdomain_of_allowed_host_is_permitted():
    assert is_allowed_url("https://blog.nationalgeographic.com/animals") is True


def test_get_site_by_url_normalizes_trailing_slash():
    site = ALLOWED_SITES["animals"][0]
    assert get_site_by_url(site["url"]) is site
    assert get_site_by_url(site["url"].rstrip("/")) is site


def test_pick_random_site_returns_member_of_category():
    site = pick_random_site("horror")
    assert site in ALLOWED_SITES["horror"]
    assert is_allowed_url(site["url"])


def test_pick_random_site_unknown_category():
    assert pick_random_site("nonexistent") is None


def test_pick_random_category_is_valid_key():
    assert pick_random_category() in ALLOWED_SITES
