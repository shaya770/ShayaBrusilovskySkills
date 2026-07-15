"""Skill: analyze_project_structure.

Builds a lightweight tree of a workspace so a model can grasp an unfamiliar
project's architecture without dumping whole files into context. Respects
common ignore patterns (``.git``, ``node_modules``, virtualenvs, build dirs)
and any patterns found in the workspace ``.gitignore``.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path

NAME = "analyze_project_structure"

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "depth": {
            "type": "integer",
            "description": "Max directory depth to scan",
            "default": 3,
            "minimum": 1,
        }
    },
}

# Always-ignored directory names, independent of .gitignore.
_ALWAYS_IGNORE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
    ".eggs",
}

# Extension -> human-readable language, used for structural hints.
_LANG_BY_EXT = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".sh": "Shell",
}

_CONFIG_FILES = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "tsconfig.json",
    "Cargo.toml",
    "go.mod",
    "Dockerfile",
    "docker-compose.yml",
    ".skills.json",
    "Makefile",
}


def _load_gitignore_globs(root: Path) -> list[str]:
    gitignore = root / ".gitignore"
    if not gitignore.is_file():
        return []
    globs: list[str] = []
    for line in gitignore.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        globs.append(stripped.rstrip("/"))
    return globs


def _is_ignored(name: str, globs: list[str]) -> bool:
    if name in _ALWAYS_IGNORE_DIRS:
        return True
    return any(fnmatch.fnmatch(name, pattern) for pattern in globs)


def analyze_project_structure(workspace_root: Path, depth: int = 3) -> str:
    """Return a rendered tree plus structural hints for ``workspace_root``."""
    if depth < 1:
        depth = 1

    globs = _load_gitignore_globs(workspace_root)
    languages: dict[str, int] = {}
    configs_found: set[str] = set()
    lines: list[str] = [f"{workspace_root.name}/"]

    def walk(directory: Path, prefix: str, level: int) -> None:
        if level > depth:
            return
        try:
            entries = sorted(
                directory.iterdir(),
                key=lambda p: (p.is_file(), p.name.lower()),
            )
        except (PermissionError, OSError):
            return

        visible = [e for e in entries if not _is_ignored(e.name, globs)]
        for index, entry in enumerate(visible):
            connector = "└── " if index == len(visible) - 1 else "├── "
            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                extension = "    " if index == len(visible) - 1 else "│   "
                walk(entry, prefix + extension, level + 1)
            else:
                lines.append(f"{prefix}{connector}{entry.name}")
                lang = _LANG_BY_EXT.get(entry.suffix.lower())
                if lang:
                    languages[lang] = languages.get(lang, 0) + 1
                if entry.name in _CONFIG_FILES:
                    configs_found.add(entry.name)

    walk(workspace_root, "", 1)

    lines.append("")
    lines.append("## Structural hints")
    if languages:
        lang_summary = ", ".join(
            f"{lang} ({count})"
            for lang, count in sorted(languages.items(), key=lambda kv: -kv[1])
        )
        lines.append(f"- Languages: {lang_summary}")
    else:
        lines.append("- Languages: none detected within scan depth")
    if configs_found:
        lines.append(f"- Config files: {', '.join(sorted(configs_found))}")
    else:
        lines.append("- Config files: none found within scan depth")
    lines.append(f"- Scan depth: {depth}")

    return "\n".join(lines)
