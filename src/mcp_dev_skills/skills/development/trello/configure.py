"""Skill: configure_trello — interactive Trello board setup."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path

SKILL = {
    "name": "configure_trello",
    "group": "development.trello",
    "description": (
        "Interactive configuration of a Trello board. "
        "Prompts for board URL, API key, and token; validates credentials; "
        "saves config to .claude/trello.json."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "board_url": {
                "type": "string",
                "description": "Full Trello board URL (e.g., https://trello.com/b/68f67984d4331f5a481236bf/board-name)",
            },
            "api_key": {
                "type": "string",
                "description": "Trello API Key (from https://trello.com/app-key)",
            },
            "token": {
                "type": "string",
                "description": "Trello API Token (generated from https://trello.com/app-key)",
            },
        },
        "required": ["board_url", "api_key", "token"],
    },
}


def _extract_board_id(board_url: str) -> str | None:
    """Extract board ID from Trello URL.

    Supports:
    - https://trello.com/b/68f67984d4331f5a481236bf/name
    - https://trello.com/b/68f67984d4331f5a481236bf
    """
    match = re.search(r"/b/([a-z0-9]+)", board_url, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def _validate_credentials(board_id: str, api_key: str, token: str) -> tuple[bool, str, str | None]:
    """Validate Trello credentials by fetching board name.

    Returns: (is_valid, message, board_name)
    """
    auth = f"key={api_key}&token={token}"
    url = f"https://api.trello.com/1/boards/{board_id}?fields=name&{auth}"

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.load(resp)
            board_name = data.get("name", "Unknown")
            return True, f"✓ Connected to board: {board_name}", board_name
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "✗ Invalid API key or token (401)", None
        elif e.code == 404:
            return False, "✗ Board not found (404) — check board ID", None
        else:
            return False, f"✗ HTTP {e.code}: {e.reason}", None
    except urllib.error.URLError as e:
        return False, f"✗ Network error: {e.reason}", None
    except Exception as e:
        return False, f"✗ Error: {e}", None


def configure_trello(
    workspace_root: Path, board_url: str, api_key: str, token: str
) -> str:
    """Validate and save Trello configuration."""
    board_id = _extract_board_id(board_url)
    if not board_id:
        return "❌ Invalid board URL. Expected format: https://trello.com/b/BOARD_ID/name"

    is_valid, message, board_name = _validate_credentials(board_id, api_key, token)
    if not is_valid:
        return f"❌ Validation failed: {message}"

    config = {
        "board_id": board_id,
        "board_url": board_url,
        "board_name": board_name,
        "api_key": api_key,
        "token": token,
    }

    config_dir = workspace_root / ".claude"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "trello.json"
    config_path.write_text(json.dumps(config, indent=2))

    return (
        f"✓ Trello configuration saved to `.claude/trello.json`\n"
        f"\n"
        f"Board: {board_name}\n"
        f"Board ID: {board_id}\n"
        f"URL: {board_url}\n"
        f"\n"
        f"Ready to use Trello skills."
    )


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    board_url = kwargs.get("board_url")
    api_key = kwargs.get("api_key")
    token = kwargs.get("token")

    if not board_url or not api_key or not token:
        return (
            "Error: missing parameters.\n"
            "Required:\n"
            "  - board_url: Full Trello board URL\n"
            "  - api_key: Trello API Key (from https://trello.com/app-key)\n"
            "  - token: Trello API Token (from https://trello.com/app-key)"
        )

    return configure_trello(workspace_root, board_url, api_key, token)
