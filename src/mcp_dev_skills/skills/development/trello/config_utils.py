"""Shared Trello config utilities for scope-aware operations."""

from __future__ import annotations

import json
from pathlib import Path


def load_config(workspace_root: Path) -> dict:
    """Load Trello config."""
    config_path = workspace_root / ".claude" / "trello.json"
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return {}


def get_board_config(workspace_root: Path) -> dict | None:
    """Get current board config for active scope.

    Returns board config dict with: board_id, board_url, board_name, tech_level, language
    Returns None if Trello not configured.
    """
    config = load_config(workspace_root)

    if not config.get("boards"):
        return None

    current_scope = config.get("current_scope", "default")
    board = config["boards"].get(current_scope)

    if not board:
        # Fallback to first available board if current_scope not found
        board = next(iter(config["boards"].values()), None)

    return board


def get_api_credentials(workspace_root: Path) -> tuple[str, str] | None:
    """Get API key and token from config.

    Returns: (api_key, token) or None if not configured.
    """
    config = load_config(workspace_root)
    api_key = config.get("api_key")
    token = config.get("token")

    if api_key and token:
        return api_key, token

    return None


def get_tech_level(workspace_root: Path) -> int:
    """Get current scope's tech level.

    Returns: 0-3, default 1 if not configured.
    """
    board = get_board_config(workspace_root)
    if board:
        return board.get("tech_level", 1)
    return 1


def get_current_scope(workspace_root: Path) -> str:
    """Get currently active scope.

    Returns: scope name or 'default'.
    """
    config = load_config(workspace_root)
    return config.get("current_scope", "default")
