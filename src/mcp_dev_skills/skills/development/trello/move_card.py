"""Skill: move_card — move card to column (DRAFT)."""

from __future__ import annotations

SKILL = {
    "name": "move_card",
    "group": "development.trello",
    "description": "Move card to another column (list).",
    "input_schema": {
        "type": "object",
        "properties": {
            "card_id": {
                "type": "string",
                "description": "Trello card ID",
            },
            "target_column": {
                "type": "string",
                "description": "Target column name (e.g., 'In Progress', 'Review')",
            },
        },
        "required": ["card_id", "target_column"],
    },
}


def execute(workspace_root, **kwargs) -> str:
    """Execute the skill (DRAFT)."""
    card_id = kwargs.get("card_id")
    target_column = kwargs.get("target_column")
    # TODO: Implement card movement
    return f"TODO: move_card {card_id} to {target_column}"
