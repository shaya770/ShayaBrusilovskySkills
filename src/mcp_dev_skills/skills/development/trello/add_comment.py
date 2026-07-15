"""Skill: add_comment — add comment to card."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

SKILL = {
    "name": "add_comment",
    "group": "development.trello",
    "description": (
        "Add comment to card. Claude comments automatically prefixed with '🤖 '."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "card_id": {
                "type": "string",
                "description": "Trello card ID",
            },
            "text": {
                "type": "string",
                "description": "Comment text",
            },
            "prefix_bot": {
                "type": "boolean",
                "description": "If true, prefix with '🤖 '",
                "default": True,
            },
        },
        "required": ["card_id", "text"],
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


def add_comment(
    workspace_root: Path, card_id: str, text: str, prefix_bot: bool = True
) -> str:
    """Add comment to card."""
    config = _load_config(workspace_root)
    api_key = config.get("api_key")
    token = config.get("token")

    if not api_key or not token:
        return "Error: Trello not configured"

    auth = f"key={api_key}&token={token}"

    # Prepare comment text
    comment_text = text
    if prefix_bot:
        comment_text = f"🤖 {text}"

    # Add comment
    comment_url = f"https://api.trello.com/1/cards/{card_id}/actions/comments?{auth}"
    result = _api_post(comment_url, {"text": comment_text})
    if not result:
        return "Error: Failed to add comment"

    return f"✓ Comment added"


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    card_id = kwargs.get("card_id")
    text = kwargs.get("text")
    prefix_bot = kwargs.get("prefix_bot", True)

    if not card_id or not text:
        return "Error: card_id and text are required"

    return add_comment(workspace_root, card_id, text, prefix_bot)
