"""Skill: change_status — move card with workflow validation."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

SKILL = {
    "name": "change_status",
    "group": "development.trello",
    "description": (
        "Change card status (move between columns). Validates workflow rules. "
        "Claude can move: Inbox→Planning, Approved→In Progress, In Progress→Review. "
        "User moves: Planning→Approved, Review→Done."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "card_id": {
                "type": "string",
                "description": "Trello card ID",
            },
            "new_status": {
                "type": "string",
                "enum": ["Inbox", "Planning", "Approved", "In Progress", "Review", "Done"],
                "description": "Target column name",
            },
        },
        "required": ["card_id", "new_status"],
    },
}

# Claude can make these transitions
CLAUDE_TRANSITIONS = {
    "Inbox": ["Planning"],
    "Planning": [],  # User moves to Approved
    "Approved": ["In Progress"],
    "In Progress": ["Review"],
    "Review": [],  # User moves to Done
    "Done": [],
}


def _load_config(workspace_root: Path) -> dict:
    """Load Trello config."""
    config_path = workspace_root / ".claude" / "trello.json"
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return {}


def _get_json(url: str) -> dict | None:
    """GET request to Trello API."""
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.load(resp)
    except Exception:
        return None


def _api_put(url: str, data: dict) -> dict | None:
    """PUT request to Trello API."""
    try:
        body = urllib.parse.urlencode(data).encode("utf-8")
        request = urllib.request.Request(url, data=body, method="PUT")
        with urllib.request.urlopen(request, timeout=10) as resp:
            return json.load(resp)
    except Exception:
        return None


def change_status(workspace_root: Path, card_id: str, new_status: str) -> str:
    """Change card status with workflow validation.

    WORKFLOW RULES:
    - Claude can: Inbox→Planning, Approved→In Progress, In Progress→Review
    - User can: Planning→Approved, Review→Done
    - Move card to target column
    """
    config = _load_config(workspace_root)
    board_id = config.get("board_id")
    api_key = config.get("api_key")
    token = config.get("token")

    if not board_id or not api_key or not token:
        return "Error: Trello not configured"

    auth = f"key={api_key}&token={token}"

    # 1. Get current card's column
    card_url = f"https://api.trello.com/1/cards/{card_id}?fields=idList&{auth}"
    card = _get_json(card_url)
    if not card:
        return f"Error: Card {card_id} not found"

    current_list_id = card.get("idList")

    # 2. Get all lists to find current and target
    lists_url = f"https://api.trello.com/1/boards/{board_id}/lists?fields=name&filter=open&{auth}"
    lists = _get_json(lists_url)
    if not lists:
        return "Error: Failed to fetch board columns"

    current_status = None
    target_list_id = None

    for lst in lists:
        if lst.get("id") == current_list_id:
            current_status = lst.get("name")
        if lst.get("name") == new_status:
            target_list_id = lst.get("id")

    if not current_status:
        return "Error: Could not determine current status"

    if not target_list_id:
        available = [lst.get("name") for lst in lists]
        return f"Error: Status '{new_status}' not found. Available: {', '.join(available)}"

    # 3. Validate transition
    allowed = CLAUDE_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        if new_status == "Approved":
            return f"⚠️ Cannot move to Approved (user decision). Currently in: {current_status}"
        if new_status == "Done":
            return f"⚠️ Cannot move to Done (user decision). Currently in: {current_status}"
        return f"Invalid transition: {current_status}→{new_status}"

    # 4. Move card
    move_url = f"https://api.trello.com/1/cards/{card_id}?{auth}"
    result = _api_put(move_url, {"idList": target_list_id})
    if not result:
        return f"Error: Failed to move card to {new_status}"

    return f"✓ Card moved: {current_status} → {new_status}"


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    card_id = kwargs.get("card_id")
    new_status = kwargs.get("new_status")

    if not card_id or not new_status:
        return "Error: card_id and new_status are required"

    return change_status(workspace_root, card_id, new_status)
