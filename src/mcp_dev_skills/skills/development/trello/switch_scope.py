"""Skill: switch_scope — switch between configured Trello boards."""

from __future__ import annotations

import json
from pathlib import Path

SKILL = {
    "name": "switch_scope",
    "group": "development.trello",
    "description": (
        "Switch active Trello board scope. Use when working with multiple projects. "
        "Shows all configured scopes and switches active one."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "scope": {
                "type": "string",
                "description": "Scope to switch to (e.g., 'rental', 'crm'). Omit to list all scopes.",
            },
        },
        "required": [],
    },
}


def _load_config(workspace_root: Path) -> dict:
    """Load Trello config."""
    config_path = workspace_root / ".claude" / "trello.json"
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return {}


def switch_scope(workspace_root: Path, scope: str | None = None) -> str:
    """Switch to a different Trello board scope.

    If scope is None, lists all configured scopes.

    AUTOMATICALLY:
    - Updates current_scope in config
    - Validates scope exists
    - Shows board details for new scope
    """
    config = _load_config(workspace_root)

    if not config.get("boards"):
        return "Error: No Trello boards configured. Run configure_trello() first."

    available_scopes = sorted(config["boards"].keys())
    current_scope = config.get("current_scope", "default")

    # List all scopes if no specific scope requested
    if not scope:
        lines = [
            "Available Trello scopes:",
            "",
        ]
        for s in available_scopes:
            board = config["boards"][s]
            is_current = " (current)" if s == current_scope else ""
            lines.append(f"  {s}{is_current}")
            lines.append(f"    Board: {board.get('board_name', '?')}")
            level_name = {0: "non-technical", 1: "beginner", 2: "intermediate", 3: "expert"}.get(
                board.get("tech_level", 1), "?"
            )
            lines.append(f"    Tech level: {level_name}")
            lines.append("")

        lines.append(f"To switch: switch_scope(scope='rental')")
        return "\n".join(lines)

    # Switch to requested scope
    if scope not in available_scopes:
        return f"Error: Scope '{scope}' not found.\nAvailable: {', '.join(available_scopes)}"

    # Update config
    config["current_scope"] = scope
    config_path = workspace_root / ".claude" / "trello.json"
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))

    board = config["boards"][scope]
    level_name = {0: "non-technical", 1: "beginner", 2: "intermediate", 3: "expert"}.get(
        board.get("tech_level", 1), "?"
    )

    lines = [
        f"✓ Switched to scope: '{scope}'",
        "",
        f"Board: {board.get('board_name', '?')}",
        f"Tech level: {level_name}",
        f"Language: {board.get('language', 'auto')}",
        "",
        "Ready to use Trello skills for this scope.",
    ]

    return "\n".join(lines)


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    scope = kwargs.get("scope")
    return switch_scope(workspace_root, scope)
