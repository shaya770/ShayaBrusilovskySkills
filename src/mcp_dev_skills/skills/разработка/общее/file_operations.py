"""Skill: safe_read_file."""

from __future__ import annotations

import sys
from pathlib import Path

SKILL = {
    "name": "safe_read_file",
    "group": "разработка.общее",
    "description": "Safely read a workspace file's contents (path-sandboxed).",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file relative to workspace root",
            }
        },
        "required": ["file_path"],
    },
}

# Guard against pulling huge blobs into the model context.
MAX_BYTES = 512 * 1024


def _resolve_in_workspace(file_path: str, workspace_root: Path) -> Path:
    """Resolve path and ensure it stays in workspace (inline to avoid import issues)."""
    # Import here to avoid circular/relative import issues during dynamic loading
    from mcp_dev_skills.security import resolve_in_workspace
    return resolve_in_workspace(file_path, workspace_root)


def safe_read_file(workspace_root: Path, file_path: str) -> str:
    """Read ``file_path`` (workspace-relative) after sandbox validation.

    Raises:
        PathEscapeError: if the path escapes the workspace.
        FileNotFoundError: if the target does not exist.
        IsADirectoryError: if the target is a directory.
    """
    target = _resolve_in_workspace(file_path, workspace_root)

    if not target.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if target.is_dir():
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")

    data = target.read_bytes()
    truncated = len(data) > MAX_BYTES
    text = data[:MAX_BYTES].decode("utf-8", errors="replace")
    if truncated:
        text += f"\n\n[... truncated at {MAX_BYTES} bytes ...]"
    return text


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    file_path = kwargs.get("file_path")
    if not file_path:
        raise ValueError("file_path is required")
    return safe_read_file(workspace_root, file_path)
