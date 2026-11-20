from __future__ import annotations

import json
import re
from dataclasses import dataclass
from urllib.parse import quote, urlsplit

from content.allowed_sites import ALLOWED_SITES
from content.site_validator import is_allowed_url
from kinito.websites import find_saved_website, validate_website_url, website_change_requested

_ACTION_FIELDS = {
    **{name: {} for name in (
        "music_open", "music_close", "music_play", "music_pause", "music_stop",
        "music_next", "music_previous", "timer_status", "timer_cancel", "known_since",
    )},
    "music_track": {"title": (str, 300)},
    "music_volume": {"volume": (int, 100)},
    "music_shuffle": {"enabled": (bool, None)},
    "music_repeat": {"mode": (str, ("one", "all"))},
    "timer_set": {"seconds": (int, 604800)},
    "timer_change": {"seconds": (int, 604800)},
    "website_open": {"url": (str, 2048)},
    "website_save": {"site_name": (str, 100), "url": (str, 2048), "aliases": (str, 2000)},
    "website_edit": {"site_name": (str, 100), "new_name": (str, 100), "url": (str, 2048),
                     "aliases": (str, 2000), "replace_aliases": (bool, None)},
    "note_create": {"text": (str, 10000), "title": (str, 200)},
}


def _action_schema(name, fields):
    properties = {"name": {"const": name}}
    for key, (kind, bound) in fields.items():
        spec = {"type": {str: "string", int: "integer", bool: "boolean"}[kind]}
        if kind is int:
            spec.update(minimum=1 if key == "seconds" else 0, maximum=bound)
        elif isinstance(bound, tuple):
            spec["enum"] = list(bound)
        elif kind is str:
            spec["maxLength"] = bound
        properties[key] = spec
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


ACTION_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "actions": {"type": "array", "maxItems": 4, "items": {
            "oneOf": [_action_schema(name, fields) for name, fields in _ACTION_FIELDS.items()]
        }},
        "question": {"type": "string", "maxLength": 500},
    },
    "required": ["actions", "question"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class ActionPlan:
    actions: list[dict]
    question: str = ""


def parse_action_plan(raw: str) -> ActionPlan:
    if not isinstance(raw, str) or len(raw) > 50000:
        raise ValueError("Invalid action response.")
    try:
        data = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid action response.") from exc
    if not isinstance(data, dict) or set(data) != {"question", "actions"}:
        raise ValueError("Invalid action plan.")
    question, actions = data["question"], data["actions"]
    if not isinstance(question, str) or len(question) > 500:
        raise ValueError("Invalid question.")
    if not isinstance(actions, list) or len(actions) > 4 or (question.strip() and actions):
        raise ValueError("Invalid action list.")
    for action in actions:
        if not isinstance(action, dict) or not isinstance(action.get("name"), str):
            raise ValueError("Invalid action.")
        fields = _ACTION_FIELDS.get(action["name"])
        if fields is None or set(action) != {"name", *fields}:
            raise ValueError("Unknown action or parameters.")
        for key, (kind, bound) in fields.items():
            value = action[key]
            if type(value) is not kind:
                raise ValueError("Invalid parameter type.")
            if kind is int and not (1 if key == "seconds" else 0) <= value <= bound:
                raise ValueError("Parameter out of range.")
            if kind is str:
                if isinstance(bound, tuple):
                    if value not in bound:
                        raise ValueError("Invalid parameter choice.")
                elif len(value) > bound or (not value.strip() and key not in {"title", "aliases", "new_name"}
                                           and not (action["name"] == "website_edit" and key == "url")):
                    raise ValueError("Invalid parameter length.")
                if key == "title" and action["name"] == "music_track" and not value.strip():
                    raise ValueError("Missing song title.")
    return ActionPlan(actions, question.strip())


def direct_saved_website_plan(text: str) -> tuple[ActionPlan, str] | None:
    if not website_change_requested(text):
        return None
    request = re.sub(
        r"^\s*(?:(?:kinito|please|bitte)[,\s]+)*(?:(?:can|could|would)\s+you\s+(?:please\s+)?)?",
        "", text, flags=re.I,
    )
    request = re.sub(r"\s+(?:pls|please|bitte)[.!?]?$", "", request, flags=re.I)
    save = re.fullmatch(r"(?:save|store|speichere?|hinterlege)\s+(\S+)\s+(?:as|als|unter(?:\s+dem\s+Namen)?)\s+(.+)", request, re.I)
    if save and (save[1].lower().startswith(("http://", "https://")) or "." in save[1]):
        try:
            url = validate_website_url(save[1])
        except ValueError as exc:
            return ActionPlan([], str(exc)), text
        labels = re.split(
            r"\s+(?:(?:with|mit(?:\s+den)?)\s+)?(?:aliases|alias|aliase|aliasen)(?:\s*:\s*|\s+)",
            save[2], maxsplit=1, flags=re.I,
        )
        action = {"name": "website_save", "site_name": labels[0].strip().strip("\"'"),
                  "url": url, "aliases": labels[1] if len(labels) > 1 else ""}
        return parse_action_plan(json.dumps({"actions": [action], "question": ""})), text
    edit = re.fullmatch(
        r"(?:change|update|edit|ändere|aendere|bearbeite)\s+(.+?)\s+(url|address|adresse|aliases|aliase|alias)\s+(?:to|auf|zu)\s+(.+)",
        request, re.I,
    )
    if edit:
        field = "url" if edit[2].lower() in {"url", "address", "adresse"} else "aliases"
        action = {"name": "website_edit", "site_name": edit[1].strip().strip("\"'"), "new_name": "",
                  "url": edit[3].strip() if field == "url" else "",
                  "aliases": edit[3].strip() if field == "aliases" else "", "replace_aliases": field == "aliases"}
        return parse_action_plan(json.dumps({"actions": [action], "question": ""})), text
    rename = re.fullmatch(r"(?:rename\s+(.+?)\s+to\s+(.+)|benenne\s+(.+?)\s+in\s+(.+?)\s+um)", request, re.I)
    if rename:
        old, new = (rename[1], rename[2]) if rename[1] else (rename[3], rename[4])
        action = {"name": "website_edit", "site_name": old.strip().strip("\"'"), "new_name": new.strip().strip("\"'"),
                  "url": "", "aliases": "", "replace_aliases": False}
        return parse_action_plan(json.dumps({"actions": [action], "question": ""})), text
    return None


def direct_browser_plan(
    text: str, *, awaiting_url: bool = False, browser_context: bool = False, saved_websites=None,
) -> tuple[ActionPlan, str] | None:
    saved_websites = saved_websites or []
    bare = re.sub(r"\s+(?:pls|please|bitte)[.!?]?$", "", text.strip(), flags=re.I).rstrip(".!?")
    saved = find_saved_website(bare, saved_websites)
    if saved:
        url, _ = resolve_browser_url(saved["url"], "Open " + saved["url"])
        return ActionPlan([{"name": "website_open", "url": url}]), "Open " + url
    match = re.fullmatch(
        r"\s*(?:(?:kinito|please|bitte)[,\s]+)*"
        r"(?:(?:could|can|would)\s+you\s+(?:please\s+)?)?"
        r"(?:open|visit|browse(?:\s+to)?|öffne|oeffne|besuche|ruf(?:e)?)\s+(.+?)\s*",
        text, re.I,
    )
    if not match:
        match = re.fullmatch(
            r"\s*(?:kinito[,\s]+)?(?:kannst|könntest|koenntest|würdest|wuerdest)\s+du\s+"
            r"(?:bitte\s+)?(.+?)\s+(?:öffnen|oeffnen|aufrufen|besuchen)(?:\s+bitte)?[.!?]?\s*",
            text, re.I,
        )
    if not match and browser_context:
        match = re.fullmatch(r"\s*(?:and\s+now|now|jetzt|nun|und\s+jetzt)\s+(.+?)\s*", text, re.I)
    if not match and re.fullmatch(r"(?:wikipedia|wiki)/\S[^\r\n]*", text.strip(), re.I):
        match = re.fullmatch(r"(.+)", text.strip())
    if not match and not awaiting_url:
        return None
    target = match[1] if match else text.strip()
    target = re.sub(r"(?:,\s+|\s+)(?:pls|please|bitte)[.!?]?$", "", target, flags=re.I).rstrip(".?!")
    target = re.sub(
        r"\s+(?:(?:in|with|using)\s+(?:(?:the|my|your|default|system)\s+)*browser|"
        r"im\s+(?:standard)?browser|in\s+(?:meinem|dem|deinem)\s+(?:standard)?browser)$",
        "", target, flags=re.I,
    )
    target = re.sub(r"^(?:(?:the|die|webseite|website|seite|url|adresse|address)\s+)+", "", target, flags=re.I)
    target = target.strip("\"'")
    address = re.fullmatch(r"https?://[^\s<>\"']+|(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:[/?#][^\s<>\"']*)?", target, re.I)
    saved = find_saved_website(target, saved_websites)
    wikipedia = re.fullmatch(r"(?:wikipedia|wiki)/(.+)", target, re.I)
    if saved:
        url = saved["url"]
    elif wikipedia:
        url = "https://en.wikipedia.org/wiki/" + quote(wikipedia[1].strip().replace(" ", "_"), safe="")
    elif address:
        url = target if target.lower().startswith(("http://", "https://")) else "https://" + target
    elif not match or re.search(
        r"\b(?:not|never|nicht|kein|don't|and|und|music|musik|player|timer|note|notes|notiz|sticky|chat|game|spiel|settings|einstellungen)\b",
        target, re.I,
    ):
        return None
    else:
        sites = [site for group in ALLOWED_SITES.values() for site in group]
        site = next((site for site in sites if site["title"].casefold() == target.casefold()), None)
        if site is None and target.casefold() in ALLOWED_SITES:
            site = ALLOWED_SITES[target.casefold()][0]
        if site is None:
            return ActionPlan([], "Please give me the exact website address to open. A site name alone is not enough."), text
        url = site["url"]
    authorized_text = "Open " + url
    try:
        url, _ = resolve_browser_url(url, authorized_text)
    except ValueError as exc:
        return ActionPlan([], str(exc)), text
    return ActionPlan([{"name": "website_open", "url": url}]), authorized_text


def requested_timer_seconds(text: str) -> int | None:
    amounts = {
        "a": 1, "an": 1, "one": 1, "ein": 1, "eine": 1, "einen": 1,
        "einer": 1, "einem": 1, "anderthalb": 1.5,
        "two": 2, "zwei": 2, "three": 3, "drei": 3, "four": 4, "vier": 4,
        "five": 5, "fünf": 5, "fuenf": 5, "six": 6, "sechs": 6,
        "seven": 7, "sieben": 7, "eight": 8, "acht": 8, "nine": 9, "neun": 9,
        "ten": 10, "zehn": 10, "fifteen": 15, "fünfzehn": 15, "twenty": 20,
        "zwanzig": 20, "thirty": 30, "dreißig": 30, "half": 0.5, "halbe": 0.5,
    }
    pattern = (
        r"(?<![\w.,+-])(\d+(?:[.,]\d+)?|" + "|".join(amounts) + r")\s*"
        r"(hours?|hrs?|stunden?|std|h|minutes?|mins?|minuten?|m|seconds?|secs?|sek(?:unden?)?|s)\b"
    )
    text = re.sub(r"\bhalf\s+an?\s+hour\b", "0.5 hours", text, flags=re.I)
    matches = list(re.finditer(pattern, text, re.I))
    if not matches:
        clock = re.search(r"(?<![\w:+-])(\d+):([0-5]\d)(?::([0-5]\d))?(?![\d:])", text)
        if clock:
            first, second, third = clock.groups()
            total = int(first) * (3600 if third is not None else 60) + int(second) * (60 if third is not None else 1)
            if third is not None:
                total += int(third)
            return total if 0 < total <= 604800 else None
        return None
    total = 0.0
    for match in matches:
        raw, unit = match.groups()
        amount = amounts.get(raw.casefold())
        if amount is None:
            amount = float(raw.replace(",", "."))
        unit = unit.casefold()
        factor = 3600 if unit.startswith(("h", "st")) else 60 if unit.startswith("m") else 1
        total += amount * factor
    return int(total) if total.is_integer() and 0 < total <= 604800 else None


def resolve_browser_url(value: str, user_text: str) -> tuple[str, bool]:
    sites = [site for group in ALLOWED_SITES.values() for site in group]
    for site in sites:
        if value.casefold() == site["title"].casefold():
            value = site["url"]
            break
    if any(ord(char) < 33 or ord(char) == 127 for char in value) or "\\" in value:
        raise ValueError("Please provide a valid HTTP/HTTPS address.")
    try:
        parsed = urlsplit(value)
        port = parsed.port
        valid = (parsed.scheme in {"http", "https"} and parsed.hostname
                 and parsed.username is None and parsed.password is None
                 and (port is None or 0 < port < 65536))
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("Please provide a valid HTTP/HTTPS address.")
    if is_allowed_url(value):
        return value, False
    request = re.match(
        r"^\s*(?:(?:kinito|please|bitte)[,\s]+)*"
        r"(?:(?:can|could|would)\s+you\s+(?:please\s+)?)?(?:open|visit|browse(?:\s+to)?|"
        r"öffne|öffnen|oeffne|besuche|ruf(?:e)?)(?:\s+(?:please|bitte|die|the|webseite|website|seite|url|address|adresse))*\s+",
        user_text, re.IGNORECASE,
    )
    german_question = re.fullmatch(
        r"\s*(?:kinito[,\s]+)?(?:kannst|könntest|koenntest|würdest|wuerdest)\s+du\s+"
        r"(?:bitte\s+)?(?:(?:die|webseite|seite|url)\s+)*" + re.escape(value)
        + r"\s+(?:bitte\s+)?(?:öffnen|oeffnen|aufrufen|besuchen)\s*[?.!]?\s*",
        user_text, re.IGNORECASE,
    )
    if german_question:
        return value, True
    if not request:
        raise ValueError("Please explicitly ask me to open the exact web address.")
    target = user_text[request.end():].strip()
    if not (target == value or target.startswith(value + " ") or target in {value + mark for mark in ".?!"}):
        raise ValueError("Please explicitly ask me to open the exact web address.")
    if re.search(r"\b(?:not|never|nicht|kein|don't)\b", target[len(value):], re.IGNORECASE):
        raise ValueError("The address was not authorized for opening.")
    return value, True
