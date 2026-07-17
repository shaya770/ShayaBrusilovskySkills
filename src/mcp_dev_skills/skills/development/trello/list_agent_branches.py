"""Skill: list_agent_branches — show all active agent branches."""

from __future__ import annotations

from pathlib import Path

from .git_utils import list_branches, get_branch_info, get_current_branch

SKILL = {
    "name": "list_agent_branches",
    "group": "development.trello",
    "description": (
        "List all active agent branches. Shows branch status, commits, current branch."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "filter": {
                "type": "string",
                "description": "Filter branches by prefix (e.g., 'crm-' shows crm-auth, crm-cache)",
            },
        },
        "required": [],
    },
}


def list_agent_branches(workspace_root: Path, filter_prefix: str | None = None) -> str:
    """List all local agent branches with status.

    AUTOMATICALLY:
    - Lists branches (excluding main/master)
    - Gets commit count for each
    - Shows which is current
    - Filters by prefix if provided
    """
    all_branches = list_branches(workspace_root)
    current = get_current_branch(workspace_root)

    # Filter out main branches
    branches = [b for b in all_branches if b not in ("main", "master", "develop")]

    # Apply filter if provided
    if filter_prefix:
        branches = [b for b in branches if b.startswith(filter_prefix)]

    if not branches:
        if filter_prefix:
            return f"No branches found with prefix '{filter_prefix}'"
        return "No agent branches found (only main/master/develop)"

    # Get info for each branch
    branch_data = []
    for branch in sorted(branches):
        info = get_branch_info(branch, workspace_root)
        is_current = branch == current
        branch_data.append({
            "name": branch,
            "commits": info["commits_count"],
            "is_current": is_current,
            "last_commit": info["commits"][0]["message"] if info["commits"] else "N/A",
        })

    # Format output
    lines = ["Active Agent Branches", ""]

    if filter_prefix:
        lines.append(f"Filter: {filter_prefix}*")
        lines.append("")

    for data in branch_data:
        current_marker = " ← current" if data["is_current"] else ""
        lines.append(f"  {data['name']}{current_marker}")
        lines.append(f"    Commits: {data['commits']}")
        lines.append(f"    Last: {data['last_commit'][:60]}")
        lines.append("")

    lines.append(f"Total: {len(branch_data)} branch(es)")

    return "\n".join(lines)


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    filter_prefix = kwargs.get("filter")
    return list_agent_branches(workspace_root, filter_prefix)
