"""Skill: create_checklist — create checklist on card."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

SKILL = {
    "name": "create_checklist",
    "group": "development.trello",
    "description": "Create checklist on card (e.g., 'Questions', 'Answers').",
    "input_schema": {
        "type": "object",
        "properties": {
            "card_id": {
                "type": "string",
                "description": "Trello card ID",
            },
            "name": {
                "type": "string",
                "description": "Checklist name (e.g., 'Questions', 'Answers')",
            },
        },
        "required": ["card_id", "name"],
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


def create_checklist(workspace_root: Path, card_id: str, name: str) -> str:
    """Create checklist on card."""
    config = _load_config(workspace_root)
    api_key = config.get("api_key")
    token = config.get("token")

    if not api_key or not token:
        return "Error: Trello not configured"

    auth = f"key={api_key}&token={token}"

    # Create checklist
    checklist_url = f"https://api.trello.com/1/cards/{card_id}/checklists?{auth}"
    result = _api_post(checklist_url, {"name": name})
    if not result:
        return f"Error: Failed to create checklist '{name}'"

    checklist_id = result.get("id")
    return f"✓ Checklist '{name}' created (id: {checklist_id})"


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    card_id = kwargs.get("card_id")
    name = kwargs.get("name")

    if not card_id or not name:
        return "Error: card_id and name are required"

    return create_checklist(workspace_root, card_id, name)
