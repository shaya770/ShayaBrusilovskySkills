"""Path sandboxing utilities.

Every tool that accepts a filesystem path MUST route it through
:func:`resolve_in_workspace` so that operations can never escape the
client's working directory (``process.cwd()`` equivalent).
"""

from __future__ import annotations

import os
from pathlib import Path


class PathEscapeError(ValueError):
    """Raised when a supplied path resolves outside the allowed workspace."""


def get_workspace_root(explicit: str | os.PathLike[str] | None = None) -> Path:
    """Return the sandbox root.

    Resolves to ``explicit`` when provided, otherwise the current working
    directory of the server process (the client's workspace when launched
    over stdio).
    """
    root = Path(explicit) if explicit is not None else Path.cwd()
    return root.resolve()


def resolve_in_workspace(
    file_path: str | os.PathLike[str],
    workspace_root: str | os.PathLike[str] | None = None,
) -> Path:
    """Resolve ``file_path`` and guarantee it stays inside the workspace.

    ``file_path`` is interpreted relative to the workspace root. Absolute
    paths and traversal sequences (``..``) that escape the root are rejected.

    Raises:
        PathEscapeError: if the resolved target lies outside the workspace.
    """
    root = get_workspace_root(workspace_root)

    candidate = Path(file_path)
    # Treat absolute inputs as workspace-relative to avoid silent escapes such
    # as "/etc/passwd"; join then resolve, then verify containment below.
    combined = (root / candidate).resolve()

    if combined != root and root not in combined.parents:
        raise PathEscapeError(
            f"Path '{file_path}' escapes the workspace sandbox ({root})"
        )

    return combined
