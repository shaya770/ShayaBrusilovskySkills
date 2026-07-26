"""Core tests: .skills.json loading (config.py)."""

from __future__ import annotations

import json
from pathlib import Path

from mcp_dev_skills.config import CONFIG_FILENAME, DEFAULT_SAFE_PATHS, load_skills_config


def test_missing_config_uses_safe_defaults(tmp_path: Path) -> None:
    cfg = load_skills_config(tmp_path)
    assert cfg.config_present is False
    assert cfg.enabled_paths == list(DEFAULT_SAFE_PATHS)
    assert cfg.disabled_skills == []
    assert DEFAULT_SAFE_PATHS == ("development.common",)


def test_empty_enabled_paths_loads_nothing(tmp_path: Path) -> None:
    (tmp_path / CONFIG_FILENAME).write_text(
        json.dumps({"enabled_paths": [], "disabled_skills": []}),
        encoding="utf-8",
    )
    cfg = load_skills_config(tmp_path)
    assert cfg.config_present is True
    assert cfg.enabled_paths == []
    enabled, disabled = cfg.get_skill_loading_config()
    assert enabled == []
    assert disabled == []


def test_loads_enabled_paths_and_disabled(tmp_path: Path) -> None:
    (tmp_path / CONFIG_FILENAME).write_text(
        json.dumps(
            {
                "enabled_paths": ["development.common", "development.branching"],
                "disabled_skills": ["branching_simple"],
            }
        ),
        encoding="utf-8",
    )
    cfg = load_skills_config(tmp_path)
    assert cfg.config_present is True
    assert cfg.enabled_paths == ["development.common", "development.branching"]
    assert cfg.disabled_skills == ["branching_simple"]


def test_ignores_unknown_keys(tmp_path: Path) -> None:
    (tmp_path / CONFIG_FILENAME).write_text(
        json.dumps(
            {
                "enabled_paths": ["development.common"],
                "disabled_skills": [],
                "notes": {"development.trello": "LEGACY/FROZEN"},
            }
        ),
        encoding="utf-8",
    )
    cfg = load_skills_config(tmp_path)
    assert cfg.enabled_paths == ["development.common"]


def test_null_lists_become_empty(tmp_path: Path) -> None:
    (tmp_path / CONFIG_FILENAME).write_text(
        json.dumps({"enabled_paths": None, "disabled_skills": None}),
        encoding="utf-8",
    )
    cfg = load_skills_config(tmp_path)
    assert cfg.enabled_paths == []
    assert cfg.disabled_skills == []
