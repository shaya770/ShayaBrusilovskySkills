"""Skill: assign_branch — assign Trello card to git branch and agent."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

from .config_utils import get_api_credentials, get_board_config
from .git_utils import create_branch, get_current_branch, get_branch_info

SKILL = {
    "name": "assign_branch",
    "group": "development.trello",
    "description": (
        "Assign Trello card to git branch and agent. "
        "Creates branch, updates card with branch info, moves to In Progress."
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
                "description": "Git branch name (e.g., 'auth-oauth', 'api-cache')",
            },
            "agent_id": {
                "type": "string",
                "description": "Agent identifier (e.g., 'agent-1', 'claude', 'shaya')",
            },
        },
        "required": ["card_id", "branch_name", "agent_id"],
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


def _api_put(url: str, data: dict) -> dict | None:
    """PUT request to Trello API."""
    try:
        body = urllib.parse.urlencode(data).encode("utf-8")
        request = urllib.request.Request(url, data=body, method="PUT")
        with urllib.request.urlopen(request, timeout=10) as resp:
            return json.load(resp)
    except Exception:
        return None


def assign_branch(
    workspace_root: Path,
    card_id: str,
    branch_name: str,
    agent_id: str,
) -> str:
    """Assign card to branch and create git branch.

    AUTOMATICALLY:
    - Validates branch name format
    - Creates git branch from main
    - Adds Trello comment with branch info
    - Moves card to In Progress
    - Stores branch metadata in comment

    Workflow rule: Card assignment = git branch creation.
                   Agent tracks work via branch commits.
    """
    # Validate inputs
    if not branch_name or not branch_name.replace("-", "").replace("_", "").isalnum():
        return "Error: Invalid branch name. Use alphanumeric, dash, underscore."

    if not agent_id or not agent_id.replace("-", "").replace("_", "").isalnum():
        return "Error: Invalid agent ID. Use alphanumeric, dash, underscore."

    credentials = get_api_credentials(workspace_root)
    if not credentials:
        return "Error: Trello not configured"

    board = get_board_config(workspace_root)
    if not board:
        return "Error: Trello board not configured"

    api_key, token = credentials
    auth = f"key={api_key}&token={token}"

    # 1. Verify card exists
    card_url = f"https://api.trello.com/1/cards/{card_id}?fields=name,desc&{auth}"
    card = _get_json(card_url)
    if not card:
        return f"Error: Card {card_id} not found"

    card_name = card.get("name", "Unknown")

    # 2. Create git branch
    success, git_msg = create_branch(branch_name, workspace_root, "main")
    if not success:
        return f"Error: Failed to create branch. {git_msg}"

    # 3. Get branch info
    branch_info = get_branch_info(branch_name, workspace_root)

    # 4. Add comment to Trello with branch info
    comment_url = f"https://api.trello.com/1/cards/{card_id}/actions/comments?{auth}"
    comment_text = (
        f"🤖 Assigned to: {agent_id}\n"
        f"📌 Branch: {branch_name}\n"
        f"📊 Status: In Progress\n"
        f"📝 Commits: 0"
    )
    result = _api_post(comment_url, {"text": comment_text})
    if not result:
        return f"Error: Failed to add comment to card"

    # 5. Move card to "In Progress"
    lists_url = f"https://api.trello.com/1/boards/{board.get('board_id')}/lists?fields=name&filter=open&{auth}"
    lists = _get_json(lists_url)
    if lists:
        in_progress_id = None
        for lst in lists:
            if lst.get("name") == "In Progress":
                in_progress_id = lst.get("id")
                break

        if in_progress_id:
            move_url = f"https://api.trello.com/1/cards/{card_id}?{auth}"
            _api_put(move_url, {"idList": in_progress_id})

    lines = [
        f"✓ Card assigned to branch",
        "",
        f"Card: {card_name}",
        f"Branch: {branch_name}",
        f"Agent: {agent_id}",
        f"Status: In Progress",
        "",
        f"Next steps:",
        f"  1. git checkout {branch_name}",
        f"  2. Make changes and commit",
        f"  3. Update progress: update_branch_status(card_id='{card_id}')",
        f"  4. When done: create_pr_from_card(card_id='{card_id}')",
    ]

    return "\n".join(lines)


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    card_id = kwargs.get("card_id")
    branch_name = kwargs.get("branch_name")
    agent_id = kwargs.get("agent_id")

    if not card_id or not branch_name or not agent_id:
        return (
            "Error: missing parameters.\n"
            "Required:\n"
            "  - card_id: Trello card ID\n"
            "  - branch_name: Git branch name (e.g., 'auth-oauth')\n"
            "  - agent_id: Agent ID (e.g., 'agent-1', 'claude')"
        )

    return assign_branch(workspace_root, card_id, branch_name, agent_id)
