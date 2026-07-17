"""Skill: create_pr_from_card — create PR from Trello card."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import subprocess
from pathlib import Path

from .config_utils import get_api_credentials, get_board_config
from .git_utils import get_branch_info, get_changed_files, run_git

SKILL = {
    "name": "create_pr_from_card",
    "group": "development.trello",
    "description": (
        "Create PR from Trello card. Gets branch info, creates GitHub/GitLab PR, "
        "updates Trello with PR link, moves card to Review."
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
                "description": "Git branch name (auto-detect from Trello if omitted)",
            },
            "title": {
                "type": "string",
                "description": "PR title (auto-generated from card name if omitted)",
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


def _api_put(url: str, data: dict) -> dict | None:
    """PUT request to Trello API."""
    try:
        body = urllib.parse.urlencode(data).encode("utf-8")
        request = urllib.request.Request(url, data=body, method="PUT")
        with urllib.request.urlopen(request, timeout=10) as resp:
            return json.load(resp)
    except Exception:
        return None


def _extract_branch_from_comment(comment_text: str) -> str | None:
    """Extract branch name from Trello comment."""
    match = re.search(r"📌 Branch: (\S+)", comment_text)
    if match:
        return match.group(1)
    return None


def _push_branch(branch_name: str, workspace_root: Path) -> tuple[bool, str]:
    """Push branch to origin."""
    code, stdout, err = run_git(["push", "-u", "origin", branch_name], workspace_root)
    if code == 0:
        return True, "Branch pushed to origin"
    return False, err or "Failed to push"


def _get_github_repo_url(workspace_root: Path) -> str | None:
    """Get GitHub repo URL from git remote."""
    code, stdout, _ = run_git(["config", "--get", "remote.origin.url"], workspace_root)
    if code == 0:
        url = stdout.strip()
        # Convert to HTTPS if SSH
        if url.startswith("git@github.com:"):
            url = url.replace("git@github.com:", "https://github.com/")
            url = url.replace(".git", "")
        return url
    return None


def _create_github_pr(
    repo_url: str,
    branch_name: str,
    title: str,
    body: str,
) -> tuple[bool, str]:
    """Create GitHub PR using gh CLI.

    Returns: (success, message_or_pr_url)
    """
    try:
        result = subprocess.run(
            [
                "gh", "pr", "create",
                "--title", title,
                "--body", body,
                "--head", branch_name,
                "--base", "main",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if result.returncode == 0:
            # Extract PR URL from output
            for line in result.stdout.split("\n"):
                if "https://github.com" in line and "/pull/" in line:
                    return True, line.strip()
            return True, result.stdout.strip()
        else:
            return False, result.stderr or "Failed to create PR"
    except FileNotFoundError:
        return False, "gh CLI not installed or not in PATH"
    except Exception as e:
        return False, str(e)


def create_pr_from_card(
    workspace_root: Path,
    card_id: str,
    branch_name: str | None = None,
    title: str | None = None,
) -> str:
    """Create PR from Trello card.

    AUTOMATICALLY:
    - Finds branch (by name or from Trello)
    - Pushes branch to origin
    - Creates PR on GitHub/GitLab
    - Updates Trello with PR link
    - Moves card to Review

    Workflow rule: Card → PR link = ready for review.
    """
    credentials = get_api_credentials(workspace_root)
    if not credentials:
        return "Error: Trello not configured"

    board = get_board_config(workspace_root)
    if not board:
        return "Error: Trello board not configured"

    api_key, token = credentials
    auth = f"key={api_key}&token={token}"

    # 1. Get card
    card_url = f"https://api.trello.com/1/cards/{card_id}?fields=name&{auth}"
    card = _get_json(card_url)
    if not card:
        return f"Error: Card {card_id} not found"

    card_name = card.get("name", "Unknown")

    # 2. Find branch name (from param or Trello comment)
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

    # 3. Verify branch exists
    branch_info = get_branch_info(branch_name, workspace_root)
    if not branch_info["exists"]:
        return f"Error: Branch '{branch_name}' does not exist"

    # 4. Push branch
    success, msg = _push_branch(branch_name, workspace_root)
    if not success:
        return f"Error: Failed to push branch. {msg}"

    # 5. Create PR (GitHub for now)
    repo_url = _get_github_repo_url(workspace_root)
    if not repo_url:
        return "Error: Could not determine GitHub repo URL"

    pr_title = title or f"{card_name} ({branch_name})"
    changed_files = get_changed_files(branch_name, workspace_root)

    pr_body = (
        f"## {card_name}\n\n"
        f"**Branch:** {branch_name}\n"
        f"**Trello:** {card_id}\n\n"
        f"### Changes\n\n"
        f"Files changed: {len(changed_files)}\n"
        f"- {chr(10).join(changed_files[:10])}"
        f"{chr(10).join([f'- ... and {len(changed_files) - 10} more']) if len(changed_files) > 10 else ''}\n\n"
        f"### Checklist\n"
        f"- [ ] Tests added/updated\n"
        f"- [ ] Documentation updated\n"
        f"- [ ] No breaking changes\n"
    )

    success, pr_url = _create_github_pr(repo_url, branch_name, pr_title, pr_body)
    if not success:
        return f"Error: Failed to create PR. {pr_url}"

    # 6. Add PR link to Trello
    comment_url = f"https://api.trello.com/1/cards/{card_id}/actions/comments?{auth}"
    comment_text = f"🤖 PR created: {pr_url}"
    _api_post(comment_url, {"text": comment_text})

    # 7. Move card to Review
    lists_url = f"https://api.trello.com/1/boards/{board.get('board_id')}/lists?fields=name&filter=open&{auth}"
    lists = _get_json(lists_url)
    if lists:
        review_id = None
        for lst in lists:
            if lst.get("name") == "Review":
                review_id = lst.get("id")
                break

        if review_id:
            move_url = f"https://api.trello.com/1/cards/{card_id}?{auth}"
            _api_put(move_url, {"idList": review_id})

    lines = [
        f"✓ PR created successfully",
        "",
        f"Card: {card_name}",
        f"Branch: {branch_name}",
        f"PR: {pr_url}",
        f"Status: Moved to Review",
        "",
        f"Next: Wait for review, then merge",
    ]

    return "\n".join(lines)


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    card_id = kwargs.get("card_id")
    branch_name = kwargs.get("branch_name")
    title = kwargs.get("title")

    if not card_id:
        return "Error: card_id is required"

    return create_pr_from_card(workspace_root, card_id, branch_name, title)
