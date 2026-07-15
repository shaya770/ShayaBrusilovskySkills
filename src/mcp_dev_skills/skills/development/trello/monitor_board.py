"""Skill: monitor_trello_board — silent background monitoring for work."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SKILL = {
    "name": "monitor_trello_board",
    "group": "development.trello",
    "description": (
        "Monitor Trello board silently in background. "
        "Polls every 3 seconds. Silent until work appears, then alerts. "
        "Runs indefinitely until WORK found."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "poll_interval": {
                "type": "integer",
                "description": "Poll interval in seconds (default 3)",
                "default": 3,
                "minimum": 1,
            },
        },
    },
}

ACTIONABLE_LISTS = {"Approved", "Inbox"}


def _load_config(workspace_root: Path) -> tuple[dict, str | None]:
    """Load Trello config from .claude/trello.json."""
    config_path = workspace_root / ".claude" / "trello.json"
    if not config_path.exists():
        return {}, "Trello not configured. Run: configure_trello skill first."

    try:
        return json.loads(config_path.read_text(encoding="utf-8")), None
    except Exception as e:
        return {}, f"Error reading trello.json: {e}"


def _get_json(url: str) -> dict | None:
    """GET request to Trello API."""
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.load(resp)
    except Exception:
        return None


def _check_board_once(board_id: str, api_key: str, token: str) -> list[tuple[str, str]] | None:
    """Single board check. Returns list of (column, card_name) or None on error."""
    auth = f"key={api_key}&token={token}"

    lists = _get_json(
        f"https://api.trello.com/1/boards/{board_id}/lists"
        f"?fields=name&filter=open&{auth}"
    )
    if lists is None:
        return None  # API error

    work = []
    for lst in lists:
        if lst["name"] not in ACTIONABLE_LISTS:
            continue
        cards = _get_json(
            f"https://api.trello.com/1/lists/{lst['id']}/cards"
            f"?fields=name,labels&{auth}"
        )
        if not cards:
            continue
        for card in cards:
            labels = {l["name"] for l in card.get("labels", [])}
            if "wait" not in labels:
                work.append((lst["name"], card["name"]))

    return work


def monitor_board(workspace_root: Path, poll_interval: int = 3) -> str:
    """Monitor Trello board silently until work is found."""
    sys.stdout.reconfigure(encoding="utf-8")

    config, error = _load_config(workspace_root)
    if error:
        return f"Error: {error}"

    board_id = config.get("board_id")
    api_key = config.get("api_key")
    token = config.get("token")

    if not all([board_id, api_key, token]):
        return "Error: Incomplete Trello config. Run configure_trello skill."

    if poll_interval < 1:
        poll_interval = 1

    # Monitor loop — silent until work found
    while True:
        work = _check_board_once(board_id, api_key, token)

        if work is not None and len(work) > 0:
            # WORK FOUND — output and stop
            lines = ["WORK found:\n"]
            for column, name in work:
                lines.append(f"  [{column}] {name}")
            return "\n".join(lines)

        # No work found or API error — sleep and retry silently
        time.sleep(poll_interval)


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    poll_interval = kwargs.get("poll_interval", 3)
    return monitor_board(workspace_root, poll_interval=poll_interval)
