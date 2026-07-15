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
        "'Approved' or 'Inbox' without 'wait' label). Use to gate full "
        "board polling—only fetch all cards when this returns 'WORK'."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "board_id": {
                "type": "string",
                "description": "Trello board ID",
            },
            "auto_mode": {
                "type": "boolean",
                "description": (
                    "If true, skip Inbox cards edited within 5 min "
                    "(assumed drafts). Approved cards always taken."
                ),
                "default": False,
            },
        },
        "required": ["board_id"],
    },
}

ACTIONABLE_LISTS = {"Approved", "Inbox"}
IDLE_MINUTES = 5


def _load_env(workspace_root: Path) -> dict[str, str]:
    """Load Trello creds from .env or .claude/trello.env."""
    env = {}
    for candidate in (
        workspace_root / ".claude" / "trello.env",
        workspace_root / ".env",
    ):
        if not candidate.exists():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return env


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


def check_board(workspace_root: Path, board_id: str, auto_mode: bool = False) -> str:
    """Check Trello board for actionable work."""
    sys.stdout.reconfigure(encoding="utf-8")

    env = _load_env(workspace_root)
    if "TRELLO_API_KEY" not in env or "TRELLO_TOKEN" not in env:
        return (
            "Error: Trello credentials not found. "
            "Create .claude/trello.env with TRELLO_API_KEY and TRELLO_TOKEN."
        )

    key, token = env["TRELLO_API_KEY"], env["TRELLO_TOKEN"]
    auth = f"key={key}&token={token}"

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
    board_id = kwargs.get("board_id")
    if not board_id:
        raise ValueError("board_id is required")
    auto_mode = kwargs.get("auto_mode", False)
    return check_board(workspace_root, board_id, auto_mode=auto_mode)
