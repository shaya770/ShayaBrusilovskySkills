"""Skill: get_card — read card details (DRAFT)."""

from __future__ import annotations

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


def execute(workspace_root, **kwargs) -> str:
    """Execute the skill (DRAFT)."""
    card_id = kwargs.get("card_id")
    # TODO: Implement card reading
    return f"TODO: get_card implementation for {card_id}"
