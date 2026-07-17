"""Skill: switch_scope — switch between configured Trello boards."""

from __future__ import annotations

import json
from pathlib import Path

SKILL = {
    "name": "switch_scope",
    "group": "development.trello",
    "description": (
        "Switch active Trello board scope. List all known scopes (configured and planned). "
        "Mark scopes as known to track all your applications."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "scope": {
                "type": "string",
                "description": "Scope to switch to (e.g., 'rental', 'crm'). Omit to list all known scopes.",
            },
            "mark_known": {
                "type": "string",
                "description": "Mark a scope as known (planned). Comma-separated: 'rental,crm,clinic'",
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


def switch_scope(
    workspace_root: Path,
    scope: str | None = None,
    mark_known: str | None = None,
) -> str:
    """Switch to a different Trello board scope or manage known scopes.

    AUTOMATICALLY:
    - Updates current_scope in config
    - Validates scope exists
    - Shows board details for new scope
    - Maintains list of known scopes (planned applications)

    Args:
        scope: Scope to switch to. Omit to list all.
        mark_known: Comma-separated scopes to mark as known (e.g., 'rental,crm,clinic')
    """
    config = _load_config(workspace_root)

    # Initialize config structure if needed
    if "boards" not in config:
        config["boards"] = {}
    if "known_scopes" not in config:
        config["known_scopes"] = []

    # Mark new scopes as known
    if mark_known:
        new_scopes = [s.strip() for s in mark_known.split(",") if s.strip()]
        known_scopes = config.get("known_scopes", [])

        for s in new_scopes:
            if not s or not s.replace("_", "").replace("-", "").isalnum():
                return f"Error: Invalid scope name '{s}'. Use alphanumeric, dash, underscore."
            if s not in known_scopes:
                known_scopes.append(s)

        config["known_scopes"] = sorted(known_scopes)
        config_path = workspace_root / ".claude" / "trello.json"
        config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))

        lines = [
            f"✓ Marked as known: {', '.join(new_scopes)}",
            "",
            "Known scopes (planned applications):",
            "  " + ", ".join(sorted(config["known_scopes"])),
        ]
        return "\n".join(lines)

    # List all known and configured scopes if no specific scope requested
    if not scope:
        configured_scopes = sorted(config["boards"].keys())
        known_scopes = sorted(config.get("known_scopes", []))
        current_scope = config.get("current_scope", "default")

        lines = []

        # Show configured scopes
        if configured_scopes:
            lines.extend([
                "Configured Trello boards:",
                "",
            ])
            for s in configured_scopes:
                board = config["boards"][s]
                is_current = " ← current" if s == current_scope else ""
                lines.append(f"  ✓ {s}{is_current}")
                lines.append(f"      Board: {board.get('board_name', '?')}")
                level_name = {0: "non-technical", 1: "beginner", 2: "intermediate", 3: "expert"}.get(
                    board.get("tech_level", 1), "?"
                )
                lines.append(f"      Tech level: {level_name}")
            lines.append("")

        # Show known (planned) scopes not yet configured
        unconfigured = [s for s in known_scopes if s not in configured_scopes]
        if unconfigured:
            lines.extend([
                "Known scopes (not yet configured):",
                "",
            ])
            for s in unconfigured:
                lines.append(f"  ○ {s} (run: configure_trello(..., scope='{s}', ...))")
            lines.append("")

        # Show how to add more known scopes
        if not known_scopes or not unconfigured:
            lines.append("Add known scopes: switch_scope(mark_known='rental,crm,clinic')")

        if not lines:
            lines.append("No Trello boards configured. Run configure_trello() first.")

        return "\n".join(lines)

    # Switch to requested scope
    if scope not in config.get("boards", {}):
        known = config.get("known_scopes", [])
        if scope not in known:
            return (
                f"Error: Scope '{scope}' not configured.\n"
                f"Run: configure_trello(..., scope='{scope}', ...)\n\n"
                f"Or mark as known first: switch_scope(mark_known='{scope}')"
            )
        return (
            f"Error: Scope '{scope}' is known but not configured yet.\n"
            f"Run: configure_trello(..., scope='{scope}', ...)"
        )

    # Update config to switch scope
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
    mark_known = kwargs.get("mark_known")
    return switch_scope(workspace_root, scope, mark_known)
