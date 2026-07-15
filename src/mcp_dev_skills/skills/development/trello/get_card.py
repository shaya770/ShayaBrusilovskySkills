"""Skill: get_card — read full card details."""

from __future__ import annotations

import json
from pathlib import Path

SKILL = {
    "name": "get_card",
    "group": "development.trello",
    "description": "Read full card details: name, description, checklists, comments, labels.",
    "input_schema": {
        "type": "object",
        "properties": {
            "card_id": {
                "type": "string",
                "description": "Trello card ID",
            },
        },
        "required": ["card_id"],
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


def get_card(workspace_root: Path, card_id: str) -> str:
    """Read full card details."""
    config = _load_config(workspace_root)
    api_key = config.get("api_key")
    token = config.get("token")

    if not api_key or not token:
        return "Error: Trello not configured"

    auth = f"key={api_key}&token={token}"

    # 1. Get card basic info
    card_url = (
        f"https://api.trello.com/1/cards/{card_id}"
        f"?fields=name,desc,labels,idList&{auth}"
    )
    card = _get_json(card_url)
    if not card:
        return f"Error: Card {card_id} not found"

    lines = [
        f"📇 Card: {card.get('name', 'Untitled')}",
        "",
    ]

    # 2. Description
    desc = card.get("desc", "")
    if desc:
        lines.append("📝 Description:")
        lines.append(desc)
        lines.append("")

    # 3. Labels
    labels = card.get("labels", [])
    if labels:
        label_names = [l.get("name") for l in labels]
        lines.append(f"🏷️  Labels: {', '.join(label_names)}")
        lines.append("")

    # 4. Checklists
    checklists_url = f"https://api.trello.com/1/cards/{card_id}/checklists?{auth}"
    checklists = _get_json(checklists_url)
    if checklists:
        for checklist in checklists:
            lines.append(f"✓ {checklist.get('name')}:")
            items = checklist.get("checkItems", [])
            if items:
                for item in items:
                    status = "☑️" if item.get("state") == "complete" else "☐"
                    lines.append(f"  {status} {item.get('name')}")
            else:
                lines.append("  (empty)")
            lines.append("")

    # 5. Comments
    comments_url = (
        f"https://api.trello.com/1/cards/{card_id}/actions"
        f"?filter=commentCard&{auth}"
    )
    comments = _get_json(comments_url)
    if comments:
        lines.append("💬 Comments:")
        for comment in comments:
            author = comment.get("memberCreator", {}).get("fullName", "Unknown")
            text = comment.get("data", {}).get("text", "")
            lines.append(f"  {author}: {text}")
        lines.append("")

    return "\n".join(lines)


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    card_id = kwargs.get("card_id")
    if not card_id:
        return "Error: card_id is required"
    return get_card(workspace_root, card_id)
