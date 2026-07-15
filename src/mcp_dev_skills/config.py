"""Workspace discovery and ``.skills.json`` parsing.

The configuration file living in the client's workspace decides which skills
are exposed. This keeps dangerous skills dormant in sensitive projects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_FILENAME = ".skills.json"

# Paths that are always safe to expose when no config file is present.
DEFAULT_SAFE_PATHS: tuple[str, ...] = ("development.common",)


@dataclass
class SkillsConfig:
    """Resolved view of a workspace's skill policy."""

    enabled_paths: list[str] = field(default_factory=list)
    disabled_skills: list[str] = field(default_factory=list)
    config_present: bool = False

    def get_skill_loading_config(self) -> tuple[list[str], list[str]]:
        """Return (enabled_paths, disabled_skills) for loader."""
        return self.enabled_paths, self.disabled_skills


def load_skills_config(workspace_root: Path) -> SkillsConfig:
    """Load ``.skills.json`` from ``workspace_root``.

    When the file is absent, fall back to the default read-only safe skill paths.
    When present, only skills under listed paths (and not in ``disabled_skills``)
    are considered enabled.

    Example .skills.json:
        {
          "enabled_paths": [
            "development.common",
            "development.trello",
            "deployment.docker"
          ],
          "disabled_skills": ["dangerous_skill"]
        }
    """
    config_path = workspace_root / CONFIG_FILENAME
    if not config_path.is_file():
        return SkillsConfig(
            enabled_paths=list(DEFAULT_SAFE_PATHS),
            disabled_skills=[],
            config_present=False,
        )

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    enabled_paths = list(raw.get("enabled_paths", []) or [])
    disabled = list(raw.get("disabled_skills", []) or [])
    return SkillsConfig(
        enabled_paths=enabled_paths,
        disabled_skills=disabled,
        config_present=True,
    )
