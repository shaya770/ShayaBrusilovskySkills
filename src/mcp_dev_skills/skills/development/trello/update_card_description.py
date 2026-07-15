"""Skill: update_card_description — write plan to card (DRAFT)."""

from __future__ import annotations

SKILL = {
    "name": "update_card_description",
    "group": "development.trello",
    "description": "Update card description (plan). Saves original to comment if first write.",
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


def execute(workspace_root, **kwargs) -> str:
    """Execute the skill (DRAFT)."""
    card_id = kwargs.get("card_id")
    description = kwargs.get("description")
    save_original = kwargs.get("save_original", False)
    # TODO: Implement description update
    return f"TODO: update_card_description for {card_id}"
