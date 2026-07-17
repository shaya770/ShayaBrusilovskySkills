"""Skill: branching_simple — simple git branching workflow.

Complete workflow for agent branch isolation:
1. assign_branch: create git branch for Trello card
2. update_branch_status: sync git status to Trello
3. list_branches: show all active branches

All functions in one place for easy customization and selection.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

SKILL = {
    "name": "branching_simple",
    "group": "development.branching",
    "description": (
        "Simple git branching workflow: assign card to branch, update status, list branches. "
        "Complete workflow for agent branch isolation."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["assign", "update_status", "list"],
                "description": (
                    "assign: create git branch for card. "
                    "update_status: sync git status to Trello. "
                    "list: show all active branches."
                ),
            },
            "card_id": {
                "type": "string",
                "description": "Trello card ID (for assign and update_status)",
            },
            "branch_name": {
                "type": "string",
                "description": "Git branch name (e.g., 'auth-oauth'). For assign action.",
            },
            "agent_id": {
                "type": "string",
                "description": "Agent ID (e.g., 'claude', 'agent-1'). For assign action.",
            },
            "filter": {
                "type": "string",
                "description": "Filter branches by prefix (e.g., 'crm-'). For list action.",
            },
        },
        "required": ["action"],
    },
}


# ============================================================================
# Git utilities
# ============================================================================


def _run_git(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run git command and return (return_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def _create_branch(branch_name: str, workspace_root: Path) -> tuple[bool, str]:
    """Create new branch from main."""
    # Ensure we have latest main
    _run_git(["fetch", "origin"], workspace_root)

    # Create branch
    code, _, err = _run_git(["checkout", "-b", branch_name, "origin/main"], workspace_root)
    if code != 0:
        code, _, err = _run_git(["checkout", "-b", branch_name, "main"], workspace_root)
        if code != 0:
            return False, f"Failed to create branch: {err}"

    return True, f"Branch '{branch_name}' created"


def _get_branch_info(branch_name: str, workspace_root: Path) -> dict:
    """Get information about a branch."""
    code, stdout, _ = _run_git(
        ["log", "main..HEAD", "--pretty=format:%h|%s"],
        workspace_root,
    )

    commits = []
    if code == 0:
        for line in stdout.split("\n"):
            if line.strip():
                parts = line.split("|")
                if len(parts) == 2:
                    commits.append({"sha": parts[0], "message": parts[1]})

    return {
        "exists": True,
        "commits_count": len(commits),
        "commits": commits,
    }


def _list_branches(workspace_root: Path) -> list[str]:
    """List all local branches."""
    code, stdout, _ = _run_git(["branch", "--format=%(refname:short)"], workspace_root)
    if code == 0:
        return [line.strip() for line in stdout.split("\n") if line.strip()]
    return []


# ============================================================================
# Trello utilities
# ============================================================================


def _get_backend(workspace_root: Path):
    """Board backend for the current scope, or None if not configured."""
    from mcp_dev_skills.skills.development.trello.backend import get_backend

    return get_backend(workspace_root)


# ============================================================================
# Actions
# ============================================================================


def _action_assign(workspace_root: Path, card_id: str, branch_name: str, agent_id: str) -> str:
    """Assign card to branch and create git branch."""
    if not branch_name or not branch_name.replace("-", "").replace("_", "").isalnum():
        return "Error: Invalid branch name. Use alphanumeric, dash, underscore."

    if not agent_id or not agent_id.replace("-", "").replace("_", "").isalnum():
        return "Error: Invalid agent ID. Use alphanumeric, dash, underscore."

    backend = _get_backend(workspace_root)
    if backend is None:
        return "Error: Trello not configured"

    # 1. Verify card exists
    card = backend.get_card(card_id)
    card_name = card["name"] or "Unknown"

    # 2. Create git branch
    success, git_msg = _create_branch(branch_name, workspace_root)
    if not success:
        return f"Error: {git_msg}"

    # 3. Add comment to the board
    comment_text = (
        f"🤖 Assigned to: {agent_id}\n"
        f"📌 Branch: {branch_name}\n"
        f"📊 Status: In Progress\n"
        f"📝 Commits: 0"
    )
    backend.add_comment(card_id, comment_text)

    # 4. Move card to "In Progress"
    for lst in backend.get_lists():
        if lst["name"] == "In Progress":
            backend.move_card(card_id, lst["id"])
            break

    return (
        f"✓ Card assigned to branch\n"
        f"Card: {card_name}\n"
        f"Branch: {branch_name}\n"
        f"Agent: {agent_id}\n"
        f"Status: In Progress\n\n"
        f"Next: git checkout {branch_name}"
    )


def _action_update_status(workspace_root: Path, card_id: str, branch_name: str | None = None) -> str:
    """Update Trello card with current branch status."""
    backend = _get_backend(workspace_root)
    if backend is None:
        return "Error: Trello not configured"

    # 1. Get card
    card = backend.get_card(card_id)
    card_name = card["name"] or "Unknown"

    # 2. Find branch name if not provided
    if not branch_name:
        for comment in backend.get_comments(card_id):
            match = re.search(r"📌 Branch: (\S+)", comment["text"])
            if match:
                branch_name = match.group(1)
                break

    if not branch_name:
        return "Error: Could not find branch name. Provide branch_name parameter."

    # 3. Get git info
    info = _get_branch_info(branch_name, workspace_root)
    commits = info["commits"]
    commits_count = info["commits_count"]

    # 4. Add comment to Trello
    commit_list = "\n".join(
        [f"  • {c['sha']}: {c['message'][:50]}" for c in reversed(commits)]
    ) or "No commits yet"

    comment_text = (
        f"🤖 Branch Status Update\n"
        f"📌 Branch: {branch_name}\n"
        f"📊 Status: In Progress ({commits_count} commits)\n\n"
        f"Recent commits:\n{commit_list}"
    )
    backend.add_comment(card_id, comment_text)

    return (
        f"✓ Branch status updated\n"
        f"Card: {card_name}\n"
        f"Branch: {branch_name}\n"
        f"Commits: {commits_count}"
    )


def _action_list(workspace_root: Path, filter_prefix: str | None = None) -> str:
    """List all active branches."""
    all_branches = _list_branches(workspace_root)
    branches = [b for b in all_branches if b not in ("main", "master", "develop")]

    if filter_prefix:
        branches = [b for b in branches if b.startswith(filter_prefix)]

    if not branches:
        if filter_prefix:
            return f"No branches found with prefix '{filter_prefix}'"
        return "No active branches"

    lines = ["Active Branches:\n"]
    for branch in sorted(branches):
        info = _get_branch_info(branch, workspace_root)
        commits = info["commits_count"]
        lines.append(f"  {branch} ({commits} commits)")

    lines.append(f"\nTotal: {len(branches)} branch(es)")
    return "\n".join(lines)


# ============================================================================
# Main entry point
# ============================================================================


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    from mcp_dev_skills.skills.development.trello.errors import BoardAPIError

    action = kwargs.get("action")

    if not action:
        return "Error: action is required (assign, update_status, list)"

    try:
        return _dispatch(workspace_root, action, kwargs)
    except BoardAPIError as exc:
        return f"Error: {exc}"


def _dispatch(workspace_root: Path, action: str, kwargs: dict) -> str:
    if action == "assign":
        card_id = kwargs.get("card_id")
        branch_name = kwargs.get("branch_name")
        agent_id = kwargs.get("agent_id")

        if not card_id or not branch_name or not agent_id:
            return "Error: assign requires card_id, branch_name, and agent_id"

        return _action_assign(workspace_root, card_id, branch_name, agent_id)

    elif action == "update_status":
        card_id = kwargs.get("card_id")
        branch_name = kwargs.get("branch_name")

        if not card_id:
            return "Error: update_status requires card_id"

        return _action_update_status(workspace_root, card_id, branch_name)

    elif action == "list":
        filter_prefix = kwargs.get("filter")
        return _action_list(workspace_root, filter_prefix)

    else:
        return f"Error: Unknown action '{action}'. Use: assign, update_status, list"
