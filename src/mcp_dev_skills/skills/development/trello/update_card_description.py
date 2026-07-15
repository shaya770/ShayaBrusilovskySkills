"""Skill: update_card_description — write/update plan in card."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

SKILL = {
    "name": "update_card_description",
    "group": "development.trello",
    "description": (
        "Update card description (plan). On first write, saves original desc to comment."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "card_id": {
                "type": "string",
                "description": "Trello card ID",
            },
            "description": {
                "type": "string",
                "description": "New description text (plan)",
            },
            "save_original": {
                "type": "boolean",
                "description": "If true, save original desc to comment first (one-time)",
                "default": False,
            },
        },
        "required": ["card_id", "description"],
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


def _api_put(url: str, data: dict) -> dict | None:
    """PUT request to Trello API."""
    import urllib.request as req
    try:
        body = urllib.parse.urlencode(data).encode("utf-8")
        request = req.Request(url, data=body, method="PUT")
        with req.urlopen(request, timeout=10) as resp:
            return json.load(resp)
    except Exception:
        return None


def _get_json(url: str) -> dict | None:
    """GET request to Trello API."""
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.load(resp)
    except Exception:
        return None


def update_card_description(
    workspace_root: Path, card_id: str, description: str, save_original: bool = False
) -> str:
    """Update card description."""
    config = _load_config(workspace_root)
    api_key = config.get("api_key")
    token = config.get("token")

    if not api_key or not token:
        return "Error: Trello not configured"

    auth = f"key={api_key}&token={token}"

    # 1. Get current description (if save_original=True)
    if save_original:
        card_url = f"https://api.trello.com/1/cards/{card_id}?fields=desc&{auth}"
        card = _get_json(card_url)
        if not card:
            return f"Error: Card {card_id} not found"

        original_desc = card.get("desc", "")
        if original_desc:
            # Save to comment
            comment_url = f"https://api.trello.com/1/cards/{card_id}/actions/comments?{auth}"
            comment_text = f"🤖 Original task:\n{original_desc}"
            result = _api_post(comment_url, {"text": comment_text})
            if not result:
                return "Error: Failed to save original to comment"

    # 2. Update description
    update_url = f"https://api.trello.com/1/cards/{card_id}?{auth}"
    result = _api_put(update_url, {"desc": description})
    if not result:
        return "Error: Failed to update description"

    lines = [
        f"✓ Card description updated",
    ]
    if save_original:
        lines.append("✓ Original task saved to comment")

    return "\n".join(lines)


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    card_id = kwargs.get("card_id")
    description = kwargs.get("description")
    save_original = kwargs.get("save_original", False)

    if not card_id or not description:
        return "Error: card_id and description are required"

    return update_card_description(workspace_root, card_id, description, save_original)
