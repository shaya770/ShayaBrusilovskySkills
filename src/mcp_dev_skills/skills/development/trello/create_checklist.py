"""Skill: create_checklist — add checklist to card (DRAFT)."""

from __future__ import annotations

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


def execute(workspace_root, **kwargs) -> str:
    """Execute the skill (DRAFT)."""
    card_id = kwargs.get("card_id")
    name = kwargs.get("name")
    # TODO: Implement checklist creation
    return f"TODO: create_checklist '{name}' on {card_id}"
