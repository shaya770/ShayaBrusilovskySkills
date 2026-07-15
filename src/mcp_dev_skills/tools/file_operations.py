"""Skill: safe_read_file.

Reads file contents with sandboxing checks so a path can never escape the
client's workspace.
"""

from __future__ import annotations

from pathlib import Path

from ..security import resolve_in_workspace

NAME = "safe_read_file"

# Guard against pulling huge blobs into the model context.
MAX_BYTES = 512 * 1024

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "Path to the file relative to workspace root",
        }
    },
    "required": ["file_path"],
}


def safe_read_file(workspace_root: Path, file_path: str) -> str:
    """Read ``file_path`` (workspace-relative) after sandbox validation.

    Raises:
        PathEscapeError: if the path escapes the workspace.
        FileNotFoundError: if the target does not exist.
        IsADirectoryError: if the target is a directory.
    """
    target = resolve_in_workspace(file_path, workspace_root)

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
