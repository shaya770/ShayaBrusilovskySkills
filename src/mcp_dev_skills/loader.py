"""Dynamic skill discovery and loading from hierarchical directory structure.

Skills are organized in a tree under src/mcp_dev_skills/skills/, e.g.:

    skills/
    ├── development/
    │   ├── common/
    │   │   ├── project_analyzer.py
    │   │   └── file_operations.py
    │   ├── trello/
    │   │   ├── trello.py
    │   │   └── ...
    │   └── ...
    └── deployment/
        ├── docker/
        └── ...

Each .py file should define:
  - SKILL: dict with name, group, description, input_schema
  - execute(workspace_root, **kwargs): function that runs the skill

The loader discovers all skills and filters them by dot-notation paths:
  - "development.common" → all skills in skills/development/common/
  - "development.*" → all skills under skills/development/
  - "*" → all skills
"""

from __future__ import annotations

import fnmatch
import importlib.util
import sys
from pathlib import Path
from typing import Any

SkillModule = Any  # A module with SKILL dict and execute() function


def _skills_root() -> Path:
    """Return the root directory of all skills."""
    return Path(__file__).parent / "skills"


def _path_to_module_path(dot_path: str) -> tuple[Path, list[str]]:
    """Convert 'development.common' to (skills_root, ['development', 'common'])."""
    parts = dot_path.split(".")
    return _skills_root(), parts


def _walk_skills(base_path: Path, path_parts: list[str], depth: int = 0) -> list[SkillModule]:
    """Recursively walk the skill tree and yield modules matching path_parts.

    If path_parts is ["development", "common"], walk only that branch.
    If path_parts is ["development", "*"], walk all under development.
    If path_parts is ["*"], walk everything.
    """
    modules: list[SkillModule] = []

    if not base_path.is_dir():
        return modules

    if depth >= len(path_parts):
        # We've matched all parts; collect all .py modules in this dir and below,
        # so a path prefix (or "*") enables the whole subtree
        for item in sorted(base_path.iterdir()):
            if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
                try:
                    mod = _load_module_from_file(item)
                    if mod and hasattr(mod, "SKILL") and hasattr(mod, "execute"):
                        modules.append(mod)
                except Exception as e:
                    print(f"Warning: failed to load {item}: {e}", file=sys.stderr)
            elif item.is_dir() and not item.name.startswith("_"):
                modules.extend(_walk_skills(item, path_parts, depth))
        return modules

    part = path_parts[depth]

    # If this part is wildcard, recurse into all directories
    if part == "*":
        for item in sorted(base_path.iterdir()):
            if item.is_dir() and not item.name.startswith("_"):
                modules.extend(_walk_skills(item, path_parts, depth + 1))
    else:
        # Recurse into the specific directory
        next_dir = base_path / part
        if next_dir.is_dir():
            modules.extend(_walk_skills(next_dir, path_parts, depth + 1))

    return modules


def _load_module_from_file(file_path: Path) -> SkillModule | None:
    """Dynamically import a Python module from file_path."""
    # Build a unique module name from the file path (replace slashes, remove .py)
    module_name = f"_skill_{file_path.stem}_{id(file_path)}"

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    return None


def load_skills(
    workspace_root: Path,
    enabled_paths: list[str],
    disabled_skills: list[str] | None = None,
) -> dict[str, tuple[SkillModule, dict]]:
    """Load skills from enabled paths and return {skill_name: (module, SKILL)}.

    Args:
        workspace_root: The client's workspace directory (used for skill execution).
        enabled_paths: List of dot-notation paths to enable, e.g.
                      ["development.common", "development.trello", "deployment.*"]
        disabled_skills: Specific skill names to exclude.

    Returns:
        Dict mapping skill name to (module, SKILL dict) for all enabled skills
        minus any in disabled_skills.
    """
    if disabled_skills is None:
        disabled_skills = []

    all_skills: dict[str, tuple[SkillModule, dict]] = {}

    for dot_path in enabled_paths:
        root, parts = _path_to_module_path(dot_path)
        modules = _walk_skills(root, parts, depth=0)
        for mod in modules:
            skill_dict = mod.SKILL
            skill_name = skill_dict.get("name")
            if skill_name and skill_name not in disabled_skills:
                all_skills[skill_name] = (mod, skill_dict)

    return all_skills


def list_available_skills() -> dict[str, dict]:
    """Return all available skills (name -> SKILL dict) without filtering."""
    all_skills: dict[str, dict] = {}
    modules = _walk_skills(_skills_root(), ["*"], depth=0)
    for mod in modules:
        skill_dict = mod.SKILL
        skill_name = skill_dict.get("name")
        if skill_name:
            all_skills[skill_name] = skill_dict
    return all_skills


def build_skill_tree() -> dict[str, Any]:
    """Return the full directory tree of available skills."""
    root = _skills_root()

    def build_dict(path: Path, name: str = "skills") -> dict:
        result = {"name": name, "type": "dir", "children": []}
        if not path.is_dir():
            return result
        for item in sorted(path.iterdir()):
            if item.name.startswith("_"):
                continue
            if item.is_dir():
                result["children"].append(
                    build_dict(item, item.name)
                )
            elif item.suffix == ".py" and item.name != "__init__.py":
                try:
                    mod = _load_module_from_file(item)
                    if mod and hasattr(mod, "SKILL"):
                        skill = mod.SKILL
                        result["children"].append({
                            "name": skill.get("name", item.stem),
                            "type": "skill",
                            "group": skill.get("group"),
                            "description": skill.get("description"),
                        })
                except Exception:
                    pass
        return result

    return build_dict(root, "skills")
