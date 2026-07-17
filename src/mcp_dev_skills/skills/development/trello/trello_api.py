"""Shared Trello HTTP client with real error reporting.

Single place for all Trello REST calls. Raises TrelloAPIError with the
HTTP status so callers can tell "bad credentials" from "card not found"
instead of swallowing everything into None.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

BASE_URL = "https://api.trello.com/1"


class TrelloAPIError(Exception):
    """Trello API call failed. Carries HTTP status when available."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def api_request(
    method: str,
    path: str,
    api_key: str,
    token: str,
    params: dict | None = None,
) -> Any:
    """Perform a Trello API request and return parsed JSON.

    Args:
        method: "GET", "POST", "PUT" or "DELETE".
        path: API path without leading slash, e.g. "cards/abc123".
        params: Query params for GET, body params for POST/PUT.

    Raises:
        TrelloAPIError: on HTTP errors, network errors, or bad JSON.
    """
    auth = {"key": api_key, "token": token}
    body = None

    if method == "GET" or params is None:
        query = urllib.parse.urlencode({**auth, **(params or {})})
    else:
        query = urllib.parse.urlencode(auth)
        body = urllib.parse.urlencode(params).encode("utf-8")

    url = f"{BASE_URL}/{path}?{query}"
    request = urllib.request.Request(url, data=body, method=method)

    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        hints = {
            400: "bad request",
            401: "invalid API key or token",
            404: "not found (bad id, or token lacks access)",
            429: "rate limited by Trello",
        }
        hint = hints.get(exc.code, "unexpected HTTP error")
        raise TrelloAPIError(
            f"Trello API {exc.code} on {method} {path}: {hint}", status=exc.code
        ) from exc
    except urllib.error.URLError as exc:
        raise TrelloAPIError(f"Network error reaching Trello: {exc.reason}") from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise TrelloAPIError(f"Invalid JSON from Trello on {method} {path}") from exc


def get(path: str, api_key: str, token: str, params: dict | None = None) -> Any:
    return api_request("GET", path, api_key, token, params)


def post(path: str, api_key: str, token: str, params: dict | None = None) -> Any:
    return api_request("POST", path, api_key, token, params)


def put(path: str, api_key: str, token: str, params: dict | None = None) -> Any:
    return api_request("PUT", path, api_key, token, params)
