"""Skill: update_branch_status — sync git branch status to Trello."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from mcp_dev_skills.skills.development.trello.config_utils import get_api_credentials, get_board_config
from mcp_dev_skills.skills.development.branching.git_utils import get_branch_info, list_branches, get_changed_files

SKILL = {
    "name": "update_branch_status",
    "group": "development.branching",
    "description": (
        "Update Trello card with current git branch status. "
        "Reads git commits, files changed; updates card comment."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "card_id": {
                "type": "string",
                "description": "Trello card ID",
            },
            "branch_name": {
                "type": "string",
                "description": "Git branch name (auto-detect if omitted)",
            },
        },
        "required": ["card_id"],
    },
}


def _get_json(url: str) -> dict | None:
    """GET request to Trello API."""
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.load(resp)
    except Exception:
        return None


def _api_post(url: str, data: dict) -> dict | None:
    """POST request to Trello API."""
    try:
        body = urllib.parse.urlencode(data).encode("utf-8")
        with urllib.request.urlopen(url, data=body, timeout=10) as resp:
            return json.load(resp)
    except Exception:
        return None


def _extract_branch_from_comment(comment_text: str) -> str | None:
    """Extract branch name from Trello comment."""
    match = re.search(r"📌 Branch: (\S+)", comment_text)
    if match:
        return match.group(1)
    return None


def _format_commit_list(commits: list[dict]) -> str:
    """Format commit list for Trello comment."""
    if not commits:
        return "No commits yet"

    lines = []
    for commit in commits:
        short_msg = commit["message"][:50]
        lines.append(f"  • {commit['sha']}: {short_msg}")

    return "\n".join(lines)


def update_branch_status(
    workspace_root: Path,
    card_id: str,
    branch_name: str | None = None,
) -> str:
    """Update Trello card with current branch status.

    AUTOMATICALLY:
    - Finds branch (by name or from Trello comment)
    - Gets git info (commits, files changed)
    - Updates Trello comment with status
    - Shows commit log

    Workflow rule: Git branch = source of truth.
                   Trello = mirror of git status.
    """
    credentials = get_api_credentials(workspace_root)
    if not credentials:
        return "Error: Trello not configured"

    api_key, token = credentials
    auth = f"key={api_key}&token={token}"

    # 1. Get card and find branch name
    card_url = f"https://api.trello.com/1/cards/{card_id}?fields=name&{auth}"
    card = _get_json(card_url)
    if not card:
        return f"Error: Card {card_id} not found"

    card_name = card.get("name", "Unknown")

    # 2. If branch_name not provided, try to extract from comment
    if not branch_name:
        actions_url = f"https://api.trello.com/1/cards/{card_id}/actions?filter=commentCard&{auth}"
        actions = _get_json(actions_url)
        if actions:
            for action in actions:
                comment = action.get("data", {}).get("text", "")
                extracted = _extract_branch_from_comment(comment)
                if extracted:
                    branch_name = extracted
                    break

    if not branch_name:
        return "Error: Could not find branch name. Provide branch_name parameter."

    # 3. Get git branch info
    branch_info = get_branch_info(branch_name, workspace_root)

    if not branch_info["exists"]:
        return f"Error: Branch '{branch_name}' does not exist"

    commits = branch_info["commits"]
    commits_count = branch_info["commits_count"]

    # 4. Get changed files
    changed_files = get_changed_files(branch_name, workspace_root)

    # 5. Create updated comment
    commit_list = _format_commit_list(reversed(commits))  # newest first

    status_text = "In Progress"
    if commits_count == 0:
        status_text = "No commits yet"
    elif commits_count > 0:
        status_text = f"In Progress ({commits_count} commits)"

    comment_text = (
        f"🤖 Branch Status Update\n"
        f"📌 Branch: {branch_name}\n"
        f"📊 Status: {status_text}\n"
        f"📝 Commits: {commits_count}\n"
        f"📁 Files changed: {len(changed_files)}\n"
        f"\nRecent commits:\n"
        f"{commit_list}\n"
        f"\nFiles: {', '.join(changed_files[:5])}"
        f"{' +more' if len(changed_files) > 5 else ''}"
    )

    # 6. Add comment to Trello
    comment_url = f"https://api.trello.com/1/cards/{card_id}/actions/comments?{auth}"
    result = _api_post(comment_url, {"text": comment_text})
    if not result:
        return "Error: Failed to update Trello comment"

    lines = [
        f"✓ Branch status updated",
        "",
        f"Card: {card_name}",
        f"Branch: {branch_name}",
        f"Commits: {commits_count}",
        f"Files changed: {len(changed_files)}",
    ]

    if changed_files:
        lines.append("")
        lines.append("Changed files:")
        for f in changed_files[:10]:
            lines.append(f"  • {f}")
        if len(changed_files) > 10:
            lines.append(f"  ... and {len(changed_files) - 10} more")

    return "\n".join(lines)


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    card_id = kwargs.get("card_id")
    branch_name = kwargs.get("branch_name")

    if not card_id:
        return "Error: card_id is required"

    return update_branch_status(workspace_root, card_id, branch_name)
