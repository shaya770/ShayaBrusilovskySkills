"""Skill: move_card — move card to another column."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

SKILL = {
    "name": "move_card",
    "group": "development.trello",
    "description": "Move card to another column (list) by name.",
    "input_schema": {
        "type": "object",
        "properties": {
            "card_id": {
                "type": "string",
                "description": "Trello card ID",
            },
            "target_column": {
                "type": "string",
                "description": "Target column name (e.g., 'In Progress', 'Review', 'Done')",
            },
        },
        "required": ["card_id", "target_column"],
    },
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


def move_card(workspace_root: Path, card_id: str, target_column: str) -> str:
    """Move card to target column."""
    config = _load_config(workspace_root)
    board_id = config.get("board_id")
    api_key = config.get("api_key")
    token = config.get("token")

    if not board_id or not api_key or not token:
        return "Error: Trello not configured"

    auth = f"key={api_key}&token={token}"

    # 1. Find target list by name
    lists_url = f"https://api.trello.com/1/boards/{board_id}/lists?fields=name&filter=open&{auth}"
    lists = _get_json(lists_url)
    if not lists:
        return "Error: Failed to fetch board columns"

    target_list_id = None
    for lst in lists:
        if lst.get("name") == target_column:
            target_list_id = lst.get("id")
            break

    if not target_list_id:
        available = [lst.get("name") for lst in lists]
        return f"Error: Column '{target_column}' not found. Available: {', '.join(available)}"

    # 2. Move card
    move_url = f"https://api.trello.com/1/cards/{card_id}?{auth}"
    result = _api_put(move_url, {"idList": target_list_id})
    if not result:
        return f"Error: Failed to move card"

    return f"✓ Card moved to '{target_column}'"


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    card_id = kwargs.get("card_id")
    target_column = kwargs.get("target_column")

    if not card_id or not target_column:
        return "Error: card_id and target_column are required"

    return move_card(workspace_root, card_id, target_column)
