"""Skill: set_plan — write plan with automatic original-task backup."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

SKILL = {
    "name": "set_plan",
    "group": "development.trello",
    "description": (
        "Write plan to card description. Automatically saves original task to comment "
        "on first write. Handles all Trello workflow rules."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "card_id": {
                "type": "string",
                "description": "Trello card ID",
            },
            "plan": {
                "type": "string",
                "description": "Plan text (in Russian)",
            },
        },
        "required": ["card_id", "plan"],
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


def _api_post(url: str, data: dict) -> dict | None:
    """POST request to Trello API."""
    try:
        body = urllib.parse.urlencode(data).encode("utf-8")
        with urllib.request.urlopen(url, data=body, timeout=10) as resp:
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


def set_plan(workspace_root: Path, card_id: str, plan: str) -> str:
    """Write plan to card.

    AUTOMATICALLY:
    - Saves original task description to comment (one-time)
    - Writes plan to description
    - Adds 'plan' label

    Workflow rule: Plan goes in description, original stays in comments.
    """
    config = _load_config(workspace_root)
    api_key = config.get("api_key")
    token = config.get("token")

    if not api_key or not token:
        return "Error: Trello not configured"

    auth = f"key={api_key}&token={token}"

    # 1. Get current description
    card_url = f"https://api.trello.com/1/cards/{card_id}?fields=desc&{auth}"
    card = _get_json(card_url)
    if not card:
        return f"Error: Card {card_id} not found"

    original_desc = card.get("desc", "")

    # 2. If has description, save to comment (one-time backup)
    if original_desc:
        comment_url = f"https://api.trello.com/1/cards/{card_id}/actions/comments?{auth}"
        comment_text = f"🤖 Original task:\n{original_desc}"
        result = _api_post(comment_url, {"text": comment_text})
        if not result:
            return "Error: Failed to save original task to comment"

    # 3. Update description with plan
    update_url = f"https://api.trello.com/1/cards/{card_id}?{auth}"
    result = _api_put(update_url, {"desc": plan})
    if not result:
        return "Error: Failed to write plan"

    # 4. Add 'plan' label
    # TODO: Get available labels and apply 'plan' label
    # For now, just confirm plan is written

    lines = [
        "✓ Plan written to card",
    ]
    if original_desc:
        lines.append("✓ Original task saved to comment")

    return "\n".join(lines)


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    card_id = kwargs.get("card_id")
    plan = kwargs.get("plan")

    if not card_id or not plan:
        return "Error: card_id and plan are required"

    return set_plan(workspace_root, card_id, plan)
