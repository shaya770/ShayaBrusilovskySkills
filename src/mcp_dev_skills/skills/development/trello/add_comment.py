"""Skill: add_comment — add comment to card (DRAFT)."""

from __future__ import annotations

SKILL = {
    "name": "add_comment",
    "group": "development.trello",
    "description": "Add comment to card. Claude comments start with '🤖 '.",
    "input_schema": {
        "type": "object",
        "properties": {
            "card_id": {
                "type": "string",
                "description": "Trello card ID",
            },
            "text": {
                "type": "string",
                "description": "Comment text (will be prefixed with '🤖 ' if from Claude)",
            },
            "is_bot": {
                "type": "boolean",
                "description": "If true, prefix with '🤖 '",
                "default": True,
            },
        },
        "required": ["card_id", "text"],
    },
}


def execute(workspace_root, **kwargs) -> str:
    """Execute the skill (DRAFT)."""
    card_id = kwargs.get("card_id")
    text = kwargs.get("text")
    is_bot = kwargs.get("is_bot", True)
    # TODO: Implement comment adding
    return f"TODO: add_comment for {card_id}"
