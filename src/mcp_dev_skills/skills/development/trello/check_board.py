"""Skill: check_trello_board — quick probe for actionable work on Trello."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SKILL = {
    "name": "check_trello_board",
    "group": "development.trello",
    "description": (
        "Quick probe of the Trello board: returns actionable work (cards in "
        "'Approved' or 'Inbox' without 'wait' label). Uses board config from "
        ".claude/trello.json. Use to gate full board polling."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "auto_mode": {
                "type": "boolean",
                "description": (
                    "If true, skip Inbox cards edited within 5 min "
                    "(assumed drafts). Approved cards always taken."
                ),
                "default": False,
            },
        },
    },
}

ACTIONABLE_LISTS = {"Approved", "Inbox"}
IDLE_MINUTES = 5


def _load_config(workspace_root: Path) -> tuple[dict, str | None]:
    """Load Trello config from .claude/trello.json.

    Returns: (config_dict, error_message)
    """
    config_path = workspace_root / ".claude" / "trello.json"
    if not config_path.exists():
        return {}, "Trello not configured. Run: configure_trello skill first."

    try:
        return json.loads(config_path.read_text(encoding="utf-8")), None
    except Exception as e:
        return {}, f"Error reading trello.json: {e}"


def _get_json(url: str, attempts: int = 4) -> dict:
    """GET with retries for Trello transient errors."""
    last_err = None
    for i in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                return json.load(resp)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last_err = exc
            time.sleep(2 * (i + 1))
    raise last_err


def _idle_minutes(card: dict) -> float | None:
    """Minutes since card was last touched."""
    raw = card.get("dateLastActivity")
    if not raw:
        return None
    ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - ts).total_seconds() / 60


def check_board(workspace_root: Path, auto_mode: bool = False) -> str:
    """Check Trello board for actionable work."""
    sys.stdout.reconfigure(encoding="utf-8")

    config, error = _load_config(workspace_root)
    if error:
        return f"Error: {error}"

    board_id = config.get("board_id")
    api_key = config.get("api_key")
    token = config.get("token")

    if not all([board_id, api_key, token]):
        return "Error: Incomplete Trello config. Run configure_trello skill."

    auth = f"key={api_key}&token={token}"

    try:
        lists = _get_json(
            f"https://api.trello.com/1/boards/{board_id}/lists"
            f"?fields=name&filter=open&{auth}"
        )
        list_cards = {}
        for lst in lists:
            if lst["name"] in ACTIONABLE_LISTS:
                list_cards[lst["name"]] = _get_json(
                    f"https://api.trello.com/1/lists/{lst['id']}/cards"
                    f"?fields=name,labels,dateLastActivity&{auth}"
                )
    except Exception as exc:
        return f"Error: Trello API error: {exc}"

    work = []
    skipped_draft = []
    for list_name, cards in list_cards.items():
        for card in cards:
            labels = {l["name"] for l in card["labels"]}
            if "wait" in labels:
                continue
            if auto_mode and list_name == "Inbox":
                idle = _idle_minutes(card)
                if idle is not None and idle < IDLE_MINUTES:
                    skipped_draft.append((card["name"], idle))
                    continue
            work.append((list_name, card["name"]))

    lines = []
    if work:
        lines.append("WORK — actionable cards found:\n")
        for column, name in work:
            lines.append(f"  [{column}] {name}")
    else:
        lines.append("NO_WORK — nothing to do right now.")

    if skipped_draft:
        lines.append("\n(Drafts, skipped in auto mode):")
        for name, idle in skipped_draft:
            lines.append(f"  ({idle:.0f}m idle) {name}")

    return "\n".join(lines)


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    auto_mode = kwargs.get("auto_mode", False)
    return check_board(workspace_root, auto_mode=auto_mode)
