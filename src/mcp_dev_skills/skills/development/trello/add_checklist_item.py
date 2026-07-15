"""Skill: add_checklist_item — add item to checklist."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

SKILL = {
    "name": "add_checklist_item",
    "group": "development.trello",
    "description": "Add item to checklist on card.",
    "input_schema": {
        "type": "object",
        "properties": {
            "checklist_id": {
                "type": "string",
                "description": "Trello checklist ID",
            },
            "text": {
                "type": "string",
                "description": "Item text (e.g., '1) What is the goal?')",
            },
        },
        "required": ["checklist_id", "text"],
    },
}


def _load_config(workspace_root: Path) -> dict:
    """Load Trello config."""
    config_path = workspace_root / ".claude" / "trello.json"
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return {}


def _api_post(url: str, data: dict) -> dict | None:
    """POST request to Trello API."""
    try:
        body = urllib.parse.urlencode(data).encode("utf-8")
        with urllib.request.urlopen(url, data=body, timeout=10) as resp:
            return json.load(resp)
    except Exception:
        return None


def add_checklist_item(workspace_root: Path, checklist_id: str, text: str) -> str:
    """Add item to checklist."""
    config = _load_config(workspace_root)
    api_key = config.get("api_key")
    token = config.get("token")

    if not api_key or not token:
        return "Error: Trello not configured"

    auth = f"key={api_key}&token={token}"

    # Add item
    item_url = f"https://api.trello.com/1/checklists/{checklist_id}/checkItems?{auth}"
    result = _api_post(item_url, {"name": text})
    if not result:
        return f"Error: Failed to add item to checklist"

    return f"✓ Item added to checklist"


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    checklist_id = kwargs.get("checklist_id")
    text = kwargs.get("text")

    if not checklist_id or not text:
        return "Error: checklist_id and text are required"

    return add_checklist_item(workspace_root, checklist_id, text)
