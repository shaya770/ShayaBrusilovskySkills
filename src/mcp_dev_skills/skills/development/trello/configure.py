"""Skill: configure_trello — interactive Trello board setup."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SKILL = {
    "name": "configure_trello",
    "group": "development.trello",
    "description": (
        "Configure a Trello board: validate credentials, verify board exists, "
        "create missing columns (Inbox, Planning, Approved, In Progress, Review, Done). "
        "Saves config to .claude/trello.json."
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
            "scope": {
                "type": "string",
                "description": (
                    "Application/project scope (e.g., 'rental', 'crm', 'clinic'). "
                    "Allows multiple Trello boards in one workspace. "
                    "Default: 'default'."
                ),
            },
            "tech_level": {
                "type": "integer",
                "enum": [0, 1, 2, 3],
                "description": (
                    "User's technical level: 0=Non-technical (no tech questions), "
                    "1=Beginner, 2=Intermediate, 3=Expert. Affects question filtering."
                ),
            },
        },
        "required": ["board_url", "api_key", "token"],
    },
}

# Required columns (in order)
REQUIRED_COLUMNS = [
    "Inbox",
    "Planning",
    "Approved",
    "In Progress",
    "Review",
    "Done",
]


def _extract_board_id(board_url: str) -> str | None:
    """Extract board ID from Trello URL."""
    match = re.search(r"/b/([a-z0-9]+)", board_url, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def _api_get(url: str) -> dict | None:
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


def _validate_and_setup_board(
    board_id: str, api_key: str, token: str
) -> tuple[bool, str, str | None]:
    """Validate credentials and ensure all required columns exist.

    Returns: (success, message, board_name)
    """
    auth = f"key={api_key}&token={token}"

    # 1. Get board info
    board_url = f"https://api.trello.com/1/boards/{board_id}?fields=name&{auth}"
    board_data = _api_get(board_url)
    if not board_data:
        return False, "Failed to connect to board. Check credentials.", None

    board_name = board_data.get("name", "Unknown")

    # 2. Get existing lists
    lists_url = f"https://api.trello.com/1/boards/{board_id}/lists?fields=name&filter=open&{auth}"
    lists_data = _api_get(lists_url)
    if lists_data is None:
        return False, "Failed to fetch board columns.", None

    existing_columns = {lst["name"] for lst in lists_data}
    messages = [f"Board: {board_name}"]

    # 3. Check & create missing columns
    for col_name in REQUIRED_COLUMNS:
        if col_name in existing_columns:
            messages.append(f"  ✓ {col_name}")
        else:
            # Create column
            create_url = f"https://api.trello.com/1/boards/{board_id}/lists?{auth}"
            result = _api_post(create_url, {"name": col_name})
            if result:
                messages.append(f"  + {col_name} (created)")
            else:
                messages.append(f"  ✗ {col_name} (failed to create)")

    return True, "\n".join(messages), board_name


def configure_trello(
    workspace_root: Path,
    board_url: str,
    api_key: str,
    token: str,
    scope: str = "default",
    tech_level: int = 1,
) -> str:
    """Validate and configure Trello board for a specific scope.

    Args:
        workspace_root: Project root
        board_url: Full Trello board URL
        api_key: Trello API key
        token: Trello API token
        scope: Application/project scope (e.g., 'rental', 'crm', 'clinic')
        tech_level: User's technical level (0-3). Affects question filtering.
                    0 = non-technical (skip tech questions)
                    1 = beginner (simple tech questions)
                    2 = intermediate (moderate tech questions)
                    3 = expert (all questions)
    """
    board_id = _extract_board_id(board_url)
    if not board_id:
        return "Error: Invalid board URL. Expected: https://trello.com/b/BOARD_ID/name"

    if not 0 <= tech_level <= 3:
        return "Error: tech_level must be 0-3"

    if not scope or not scope.replace("_", "").replace("-", "").isalnum():
        return "Error: scope must be alphanumeric (letters, numbers, dash, underscore)"

    success, message, board_name = _validate_and_setup_board(board_id, api_key, token)
    if not success:
        return f"Error: {message}"

    # Load existing config or create new
    config_dir = workspace_root / ".claude"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "trello.json"

    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        config = {
            "api_key": api_key,
            "token": token,
            "current_scope": scope,
            "boards": {},
        }

    # Update API credentials (shared across all boards)
    config["api_key"] = api_key
    config["token"] = token
    config["current_scope"] = scope

    # Add/update this board under the scope
    config.setdefault("boards", {})
    config["boards"][scope] = {
        "board_id": board_id,
        "board_url": board_url,
        "board_name": board_name,
        "tech_level": tech_level,
        "language": "auto",
    }

    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))

    level_names = {0: "Non-technical", 1: "Beginner", 2: "Intermediate", 3: "Expert"}
    lines = [
        f"✓ Trello board configured for scope: '{scope}'",
        "",
        message,
        "",
        f"Technical level: {level_names.get(tech_level, '?')}",
    ]

    # Show all configured scopes
    if len(config["boards"]) > 1:
        scopes = ", ".join(sorted(config["boards"].keys()))
        lines.append(f"Configured scopes: {scopes}")
        lines.append(f"Currently active: '{scope}'")

    lines.append("")
    lines.append("Ready to use Trello skills.")

    return "\n".join(lines)


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    board_url = kwargs.get("board_url")
    api_key = kwargs.get("api_key")
    token = kwargs.get("token")
    scope = kwargs.get("scope", "default")
    tech_level = kwargs.get("tech_level", 1)

    if not board_url or not api_key or not token:
        return (
            "Error: missing parameters.\n"
            "Required:\n"
            "  - board_url: Full Trello board URL\n"
            "  - api_key: Trello API Key (from https://trello.com/app-key)\n"
            "  - token: Trello API Token (from https://trello.com/app-key)\n"
            "Optional:\n"
            "  - scope: Application scope like 'rental', 'crm', 'clinic' (default: 'default')\n"
            "  - tech_level: 0=non-technical, 1=beginner, 2=intermediate, 3=expert (default: 1)"
        )

    return configure_trello(workspace_root, board_url, api_key, token, scope, tech_level)
