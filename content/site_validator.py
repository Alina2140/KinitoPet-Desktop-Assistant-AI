"""URL allow-list helpers for the sandboxed in-app browser."""

import random
from urllib.parse import urlparse

from content.allowed_sites import ALLOWED_SITES

_ALLOWED_URLS = set()
_URL_TO_SITE = {}
_ALLOWED_HOSTS = set()

for _category, _sites in ALLOWED_SITES.items():
    for _site in _sites:
        _url = _site["url"].rstrip("/")
        _ALLOWED_URLS.add(_site["url"])
        _ALLOWED_URLS.add(_url)
        _URL_TO_SITE[_site["url"]] = _site
        _URL_TO_SITE[_url] = _site
        _host = urlparse(_site["url"]).netloc.lower()
        if _host:
            _ALLOWED_HOSTS.add(_host)
            if _host.startswith("www."):
                _ALLOWED_HOSTS.add(_host[4:])


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
    if host in _ALLOWED_HOSTS:
        return True
    return any(host == allowed or host.endswith(f".{allowed}") for allowed in _ALLOWED_HOSTS)


def is_allowed_url(url):
    """Return True only for HTTPS URLs on the configured allow-list."""
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
    if url in _ALLOWED_URLS or normalized in _ALLOWED_URLS:
        return True

    return _hostname_allowed(parsed.netloc)


def get_site_by_url(url):
    """Look up site metadata dict for an allowed URL."""
    return _URL_TO_SITE.get(url) or _URL_TO_SITE.get(_normalize_url(url))


def pick_random_site(category):
    """Return a random site dict from *category*, or None if empty."""
    sites = ALLOWED_SITES.get(category)
    if not sites:
        return None
    return random.choice(sites)


def pick_random_category():
    """Return a random key from ALLOWED_SITES."""
    return random.choice(list(ALLOWED_SITES.keys()))
