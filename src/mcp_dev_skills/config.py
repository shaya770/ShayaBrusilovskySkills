"""Workspace discovery and ``.skills.json`` parsing.

The configuration file living in the client's workspace decides which tools
are exposed. This keeps dangerous tools dormant in sensitive projects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_FILENAME = ".skills.json"

# Tools that are always safe to expose when no config file is present.
DEFAULT_SAFE_SKILLS: tuple[str, ...] = ("analyze_project_structure",)


@dataclass
class SkillsConfig:
    """Resolved view of a workspace's tool policy."""

    enabled_skills: list[str] = field(default_factory=list)
    disabled_skills: list[str] = field(default_factory=list)
    config_present: bool = False

    def is_enabled(self, skill_name: str) -> bool:
        """Return whether ``skill_name`` may be exposed/called."""
        if skill_name in self.disabled_skills:
            return False
        return skill_name in self.enabled_skills


def load_skills_config(workspace_root: Path) -> SkillsConfig:
    """Load ``.skills.json`` from ``workspace_root``.

    When the file is absent, fall back to the default read-only safe toolset.
    When present, only skills listed under ``enabled_skills`` (and not in
    ``disabled_skills``) are considered enabled.
    """
    config_path = workspace_root / CONFIG_FILENAME
    if not config_path.is_file():
        return SkillsConfig(
            enabled_skills=list(DEFAULT_SAFE_SKILLS),
            disabled_skills=[],
            config_present=False,
        )

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    enabled = list(raw.get("enabled_skills", []) or [])
    disabled = list(raw.get("disabled_skills", []) or [])
    return SkillsConfig(
        enabled_skills=enabled,
        disabled_skills=disabled,
        config_present=True,
    )
