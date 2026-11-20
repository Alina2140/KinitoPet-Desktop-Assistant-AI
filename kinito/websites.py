from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlsplit


def website_name_key(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def validate_website_url(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise ValueError("Please supply an HTTP/HTTPS website address.")
    value = value.strip()
    if re.fullmatch(r"(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:[/?#][^\s]*)?", value):
        value = "https://" + value
    if any(ord(char) <= 32 or ord(char) == 127 for char in value) or "\\" in value:
        raise ValueError("Please supply a valid HTTP/HTTPS website address.")
    try:
        parsed = urlsplit(value)
        valid = (parsed.scheme in {"http", "https"} and parsed.hostname
                 and parsed.username is None and parsed.password is None
                 and (parsed.port is None or 0 < parsed.port < 65536))
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("Please supply a valid HTTP/HTTPS website address without login credentials.")
    return value


def normalize_saved_websites(raw, *, strict: bool = True) -> list[dict]:
    if not isinstance(raw, list) or len(raw) > 100:
        if strict:
            raise ValueError("At most 100 saved websites are supported.")
        raw = raw[:100] if isinstance(raw, list) else []
    result, used = [], set()
    for item in raw:
        try:
            if not isinstance(item, dict) or set(item) != {"name", "url", "aliases"}:
                raise ValueError("A saved website needs a name, URL and aliases.")
            names = [item["name"]]
            if not isinstance(item["aliases"], list) or len(item["aliases"]) > 20:
                raise ValueError("At most 20 aliases per website are supported.")
            names.extend(item["aliases"])
            if any(not isinstance(name, str) or not name.strip() or len(name) > 100
                   or any(ord(char) < 32 or ord(char) == 127 for char in name) for name in names):
                raise ValueError("Website names must contain 1–100 characters without control characters.")
            names = list(dict.fromkeys(name.strip() for name in names))
            keys = [website_name_key(name) for name in names]
            if len(set(keys)) != len(keys) or used.intersection(keys):
                raise ValueError("Each website name or alias must be unique.")
            entry = {"name": names[0], "url": validate_website_url(item["url"]), "aliases": names[1:]}
        except ValueError:
            if strict:
                raise
            continue
        result.append(entry)
        used.update(keys)
    return result


def find_saved_website(name: str, websites: list[dict]) -> dict | None:
    key = website_name_key(name)
    return next((site for site in websites if key in {
        website_name_key(label) for label in [site["name"], *site["aliases"]]
    }), None)


def split_website_aliases(value: str) -> list[str]:
    return [alias.strip().strip("\"'") for alias in re.split(r"[,;|]", value) if alias.strip()]


def website_change_requested(text: str) -> bool:
    return bool(re.match(
        r"^\s*(?:(?:kinito|please|bitte)[,\s]+)*(?:(?:can|could|would)\s+you\s+(?:please\s+)?)?"
        r"(?:save|store|remember|speichere?|merke|hinterlege|change|update|edit|rename|ändere|aendere|bearbeite|benenne)\b",
        text, re.I,
    )) and not re.search(r"\b(?:note|notiz|sticky)\b", text, re.I)


def explicit_website_url(url: str, text: str) -> bool:
    candidates = re.findall(r"https?://[^\s<>\"']+|(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:[/?#][^\s<>\"']*)?", text, re.I)
    for candidate in candidates:
        try:
            if validate_website_url(candidate.rstrip(".,!?;")) == validate_website_url(url):
                return True
        except ValueError:
            pass
    return False
