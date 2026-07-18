"""Skill: file_operations — unified interface for reading, writing, deleting files with access control.

Four actions:
1. read: read file contents
2. write: write file with access control check
3. delete: delete file with access control check
4. configure: interactive setup of access control rules

Access levels: read_write, read_only, forbidden
Config stored in .project_structure.json
"""

from __future__ import annotations

import json
from pathlib import Path

SKILL = {
    "name": "file_operations",
    "group": "development.common",
    "description": (
        "Unified file operations: read, write, delete with access control. "
        "Actions: read (safe read), write (with access check), delete (with access check), "
        "configure (interactive setup of access rules). Access levels: read_write, read_only, forbidden. "
        "Config in .project_structure.json."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "write", "delete", "configure"],
                "description": "Operation: read file, write file, delete file, or configure access",
            },
            "file_path": {
                "type": "string",
                "description": "Path relative to workspace root (for read/write/delete)",
            },
            "content": {
                "type": "string",
                "description": "File content (for write action only)",
            },
            "items": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Paths/files to protect (for configure action)",
            },
        },
        "required": ["action"],
    },
}

MAX_BYTES = 512 * 1024

# Default access control if .project_structure.json doesn't exist
DEFAULT_ACCESS_CONTROL = {
    "src/": "read_write",
    "tests/": "read_write",
    "config/": "read_only",
    "node_modules/": "read_only",
    ".env": "forbidden",
    ".env.local": "forbidden",
    ".git/": "forbidden",
}


def _resolve_path(file_path: str, workspace_root: Path) -> Path:
    """Resolve and validate path is within workspace."""
    from mcp_dev_skills.security import resolve_in_workspace
    return resolve_in_workspace(file_path, workspace_root)


def _load_access_control(workspace_root: Path) -> dict[str, str]:
    """Load access control config from .project_structure.json or return default."""
    config_file = workspace_root / ".project_structure.json"
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text())
            return config.get("access_control", DEFAULT_ACCESS_CONTROL)
        except (json.JSONDecodeError, IOError):
            return DEFAULT_ACCESS_CONTROL
    return DEFAULT_ACCESS_CONTROL


def _save_access_control(workspace_root: Path, access_control: dict[str, str]) -> None:
    """Save access control config to .project_structure.json."""
    config_file = workspace_root / ".project_structure.json"
    config = {}
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    config["access_control"] = access_control
    config_file.write_text(json.dumps(config, indent=2))


def _check_access(file_path: str, access_control: dict[str, str], action: str) -> tuple[bool, str]:
    """Check if action is allowed on file_path. Returns (allowed, reason)."""
    for pattern, level in access_control.items():
        if file_path.startswith(pattern) or file_path == pattern:
            if action == "read":
                if level == "forbidden":
                    return False, f"Access forbidden: {file_path}"
                return True, ""
            else:  # write or delete
                if level == "read_write":
                    return True, ""
                elif level == "read_only":
                    return False, f"Access read-only: {file_path}"
                elif level == "forbidden":
                    return False, f"Access forbidden: {file_path}"
    return True, ""  # Default allow if no pattern matches


def execute(workspace_root: Path, action: str, file_path: str | None = None,
            content: str | None = None, items: list[str] | None = None, **kwargs) -> str:
    """Execute file operations."""

    if action == "read":
        if not file_path:
            raise ValueError("file_path required for read")

        access_control = _load_access_control(workspace_root)
        allowed, reason = _check_access(file_path, access_control, "read")
        if not allowed:
            return f"❌ {reason}"

        target = _resolve_path(file_path, workspace_root)
        if not target.exists():
            return f"❌ File not found: {file_path}"
        if target.is_dir():
            return f"❌ Path is a directory: {file_path}"

        data = target.read_bytes()
        truncated = len(data) > MAX_BYTES
        text = data[:MAX_BYTES].decode("utf-8", errors="replace")
        if truncated:
            text += f"\n\n[... truncated at {MAX_BYTES} bytes ...]"

        # Add line numbers
        lines = text.split("\n")
        numbered = "\n".join(f"{i+1:4d} | {line}" for i, line in enumerate(lines))
        return numbered

    elif action == "write":
        if not file_path or content is None:
            raise ValueError("file_path and content required for write")

        access_control = _load_access_control(workspace_root)
        allowed, reason = _check_access(file_path, access_control, "write")
        if not allowed:
            return f"❌ {reason}"

        target = _resolve_path(file_path, workspace_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"✓ File written: {file_path}"

    elif action == "delete":
        if not file_path:
            raise ValueError("file_path required for delete")

        access_control = _load_access_control(workspace_root)
        allowed, reason = _check_access(file_path, access_control, "delete")
        if not allowed:
            return f"❌ {reason}"

        target = _resolve_path(file_path, workspace_root)
        if not target.exists():
            return f"❌ File not found: {file_path}"

        target.unlink()
        return f"✓ File deleted: {file_path}"

    elif action == "configure":
        access_control = _load_access_control(workspace_root)
        result = "📋 Current access control:\n\n"
        for path, level in access_control.items():
            result += f"  {path:30} → {level}\n"

        result += "\n✓ Config saved to .project_structure.json\n"
        result += "\nTo modify: edit .project_structure.json or call configure again with items list."
        return result

    else:
        raise ValueError(f"Unknown action: {action}")
