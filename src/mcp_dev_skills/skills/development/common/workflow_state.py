"""Skill: workflow_state — one-shot snapshot of the whole working context.

Answers "where am I?" after a session restart in a single call:
current Trello scope and board, cards in the working columns, and the
local git state (branch, dirty files, recent commits).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

SKILL = {
    "name": "workflow_state",
    "group": "development.common",
    "description": (
        "Full workflow snapshot in one call: current Trello scope/board, "
        "cards in Inbox/Approved/In Progress/Review, git branch, dirty files, "
        "recent commits. Use at session start to restore context."
    ),
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

# Columns worth showing in the snapshot (Done/Planning are not active work)
SNAPSHOT_LISTS = ["Inbox", "Planning", "Approved", "In Progress", "Review"]


def _git(workspace_root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None


def _git_section(workspace_root: Path) -> list[str]:
    branch = _git(workspace_root, "rev-parse", "--abbrev-ref", "HEAD")
    if branch is None:
        return ["## Git", "  Not a git repository (or git unavailable)"]

    lines = ["## Git", f"  Branch: {branch}"]

    status = _git(workspace_root, "status", "--porcelain")
    dirty = len(status.splitlines()) if status else 0
    lines.append(f"  Uncommitted changes: {dirty} file(s)" if dirty else "  Working tree: clean")

    log = _git(workspace_root, "log", "--oneline", "-3")
    if log:
        lines.append("  Recent commits:")
        for line in log.splitlines():
            lines.append(f"    {line}")

    return lines


def _trello_section(workspace_root: Path) -> list[str]:
    from mcp_dev_skills.skills.development.trello.backend import get_backend
    from mcp_dev_skills.skills.development.trello.config_utils import get_current_scope
    from mcp_dev_skills.skills.development.trello.errors import BoardAPIError

    backend = get_backend(workspace_root)
    if backend is None:
        return ["## Trello", "  Not configured (run trello action='configure')"]

    scope = get_current_scope(workspace_root)
    lines = [
        "## Trello",
        f"  Scope: {scope}",
        f"  Board: {backend.board_name}",
    ]

    try:
        by_name = {lst["name"]: lst["id"] for lst in backend.get_lists()}
        any_cards = False
        for list_name in SNAPSHOT_LISTS:
            list_id = by_name.get(list_name)
            if not list_id:
                continue
            cards = backend.get_cards(list_id)
            if not cards:
                continue
            any_cards = True
            lines.append(f"  [{list_name}]")
            for card in cards:
                lines.append(f"    - {card['name']} (id: {card['id']})")
        if not any_cards:
            lines.append("  No cards in working columns")
    except BoardAPIError as exc:
        lines.append(f"  ⚠️ Board unreachable: {exc}")

    return lines


def execute(workspace_root: Path, **kwargs) -> str:
    """Build the snapshot."""
    lines = ["# Workflow State", ""]
    lines.extend(_trello_section(workspace_root))
    lines.append("")
    lines.extend(_git_section(workspace_root))
    return "\n".join(lines)
