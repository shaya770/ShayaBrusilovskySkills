"""Skill: setup_skills — interactive skill installer."""

from __future__ import annotations

import json
from pathlib import Path

SKILL = {
    "name": "setup_skills",
    "group": "разработка.общее",
    "description": (
        "List available skill groups and generate .skills.json configuration. "
        "Use this to interactively select which skill groups to enable."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list_tree", "generate_config"],
                "description": "Action: 'list_tree' to show available skills, 'generate_config' to create .skills.json",
            },
            "enabled_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of dot-notation paths to enable (for generate_config action)",
            },
        },
        "required": ["action"],
    },
}


def _build_tree_text(tree_dict: dict, indent: int = 0) -> str:
    """Render skill tree as formatted text."""
    lines = []
    prefix = "  " * indent

    if tree_dict.get("type") == "skill":
        lines.append(
            f"{prefix}📝 {tree_dict['name']}"
        )
        if desc := tree_dict.get("description"):
            lines.append(f"{prefix}   {desc[:60]}")
    else:
        icon = "📦" if indent == 0 else "📁"
        lines.append(f"{prefix}{icon} {tree_dict['name']}/")

    for child in tree_dict.get("children", []):
        lines.extend(_build_tree_text(child, indent + 1))

    return "\n".join(lines)


def list_available_skills(workspace_root: Path) -> str:
    """Return formatted tree of all available skills."""
    from mcp_dev_skills.loader import build_skill_tree

    tree = build_skill_tree()
    return _build_tree_text(tree)


def generate_config(workspace_root: Path, enabled_paths: list[str]) -> str:
    """Generate and write .skills.json file."""
    config = {
        "enabled_paths": enabled_paths,
        "disabled_skills": [],
    }
    config_path = workspace_root / ".skills.json"
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))
    return f"✓ Created .skills.json with {len(enabled_paths)} enabled path(s):\n" + "\n".join(
        f"  - {p}" for p in enabled_paths
    )


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    action = kwargs.get("action", "list_tree")

    if action == "list_tree":
        return list_available_skills(workspace_root)
    elif action == "generate_config":
        enabled_paths = kwargs.get("enabled_paths", [])
        if not enabled_paths:
            raise ValueError("enabled_paths is required for generate_config action")
        return generate_config(workspace_root, enabled_paths)
    else:
        raise ValueError(f"Unknown action: {action}")
