"""Skill: project_analyzer — intelligent workspace analysis with language/framework support.

Three-level analysis:
1. Quick overview: Detect language, framework, list logical project parts
2. Part details: Files, functions, classes for selected part
3. File paths: Exact paths and signatures for editing

Also includes tree view (legacy from analyze_project_structure).
"""

from __future__ import annotations

import fnmatch
from pathlib import Path

SKILL = {
    "name": "project_analyzer",
    "group": "development.common",
    "description": (
        "Intelligent workspace analysis: detect language/framework, list project parts, "
        "show details of selected part, provide exact file paths. Three-level analysis "
        "to avoid overwhelming AI with full project structure. Also includes tree view."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "level": {
                "type": "integer",
                "description": "Analysis level: 0 (tree), 1 (overview), 2 (part details), 3 (file paths). Default: 1",
                "default": 1,
                "minimum": 0,
                "maximum": 3,
            },
            "part": {
                "type": "string",
                "description": "For levels 2-3: specific part to analyze (e.g., 'orders', 'authentication')",
            },
            "depth": {
                "type": "integer",
                "description": "For level 0 (tree): max directory depth to scan. Default: 3",
                "default": 3,
                "minimum": 1,
            },
        },
    },
}

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


class ProjectAnalyzer:
    """Intelligent project analyzer with language/framework detection."""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.language = "unknown"
        self.framework = "unknown"
        self.parts = {}

    def detect_language_and_framework(self) -> tuple[str, str]:
        """Detect project language and framework."""
        try:
            files = {f.name for f in self.workspace.rglob("*") if f.is_file()}
        except (PermissionError, OSError):
            return "unknown", "unknown"

        language, framework = "unknown", "unknown"

        # Detect language
        if any(f in files for f in ["requirements.txt", "setup.py", "pyproject.toml", "poetry.lock"]):
            language = "python"
            # Detect Python framework
            try:
                for py_file in list(self.workspace.rglob("*.py"))[:20]:
                    content = py_file.read_text(errors="ignore").lower()
                    if "django" in content:
                        framework = "django"
                        break
                    elif "flask" in content:
                        framework = "flask"
                        break
                    elif "fastapi" in content:
                        framework = "fastapi"
                        break
            except (PermissionError, OSError):
                pass

        elif "package.json" in files:
            language = "javascript"
            try:
                pkg = self.workspace / "package.json"
                if pkg.is_file():
                    content = pkg.read_text(errors="ignore").lower()
                    if '"react"' in content:
                        framework = "react"
                    elif '"vue"' in content:
                        framework = "vue"
            except (PermissionError, OSError):
                pass

        self.language = language
        self.framework = framework
        return language, framework

    def identify_project_parts(self) -> dict[str, list[str]]:
        """Identify logical parts of the project by folder structure."""
        parts = {}
        try:
            workspace_dirs = {
                d.name: d
                for d in self.workspace.iterdir()
                if d.is_dir() and not d.name.startswith(("."))
            }
        except (PermissionError, OSError):
            return {}

        ignore_dirs = {
            "__pycache__",
            "node_modules",
            ".git",
            "venv",
            ".venv",
            "env",
            "build",
            "dist",
            ".eggs",
        }

        for folder_name, folder_path in workspace_dirs.items():
            if folder_name not in ignore_dirs:
                try:
                    py_files = list(folder_path.rglob("*.py"))[:5]
                    js_files = list(folder_path.rglob("*.js")) + list(folder_path.rglob("*.jsx"))[:5]
                    if py_files or js_files:
                        parts[folder_name] = [str(f.relative_to(self.workspace)) for f in (py_files + js_files)]
                except (PermissionError, OSError):
                    pass

        return parts

    def get_overview(self) -> str:
        """Level 1: Quick overview of project."""
        lang, fw = self.detect_language_and_framework()
        parts = self.identify_project_parts()

        overview = f"""# Project Overview

Language: {lang}
Framework: {fw}

Project Parts:
"""
        if parts:
            for i, part_name in enumerate(parts.keys(), 1):
                overview += f"{i}. {part_name}\n"
        else:
            overview += "(No major parts detected)\n"

        return overview

    def get_part_details(self, part_name: str) -> str:
        """Level 2: Details of selected part."""
        parts = self.identify_project_parts()

        if part_name not in parts:
            available = ", ".join(parts.keys()) if parts else "(none detected)"
            return f"Part '{part_name}' not found.\nAvailable: {available}"

        files = parts[part_name]
        details = f"""# Part: {part_name}

Files in this part:
"""
        for f in files:
            details += f"- {f}\n"

        return details

    def get_file_paths(self, part_name: str) -> str:
        """Level 3: Exact file paths for editing."""
        parts = self.identify_project_parts()

        if part_name not in parts:
            return f"Part '{part_name}' not found."

        files = parts[part_name]
        paths = f"""# File Paths for: {part_name}

{len(files)} file(s) to edit:
"""
        for f in files:
            paths += f"- {self.workspace / f}\n"

        return paths

    def analyze(self, level: int = 1, part: str | None = None) -> str:
        """Analyze workspace at specified level."""
        if level == 0:
            return analyze_project_structure(self.workspace)
        elif level == 1:
            return self.get_overview()
        elif level == 2 and part:
            return self.get_part_details(part)
        elif level == 3 and part:
            return self.get_file_paths(part)
        else:
            return self.get_overview()


def execute(workspace_root: Path, level: int = 1, part: str | None = None, depth: int = 3, **kwargs) -> str:
    """Execute the skill."""
    if level == 0:
        return analyze_project_structure(workspace_root, depth=depth)

    analyzer = ProjectAnalyzer(workspace_root)
    return analyzer.analyze(level=level, part=part)
