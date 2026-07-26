"""Core tests: hierarchical skill discovery (loader.py)."""

from __future__ import annotations

from pathlib import Path

from mcp_dev_skills.loader import load_skills, list_available_skills


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_load_development_common() -> None:
    skills = load_skills(_repo_root(), ["development.common"], [])
    names = set(skills)
    assert "project_analyzer" in names
    assert "file_operations" in names
    assert "setup_skills" in names
    # Trello pack lives under development/trello/, not common/
    assert "trello" not in names
    assert "workflow_state" not in names


def test_trello_not_loaded_unless_path_enabled() -> None:
    skills = load_skills(
        _repo_root(),
        [
            "development.common",
            "development.branching",
            "development.local_dev",
            "development.development_rules",
            "development.server_development",
        ],
        [],
    )
    assert "trello" not in skills
    assert "workflow_state" not in skills


def test_trello_loads_when_explicitly_enabled() -> None:
    skills = load_skills(_repo_root(), ["development.trello"], [])
    assert "trello" in skills
    assert "workflow_state" in skills
    desc = skills["trello"][1].get("description", "")
    assert "LEGACY" in desc.upper() or "FROZEN" in desc.upper()


def test_disabled_skills_excluded() -> None:
    skills = load_skills(
        _repo_root(),
        ["development.common"],
        disabled_skills=["setup_skills"],
    )
    assert "project_analyzer" in skills
    assert "setup_skills" not in skills


def test_wildcard_development_star() -> None:
    skills = load_skills(_repo_root(), ["development.*"], [])
    # Wildcard enables the whole development tree, including frozen Trello code
    assert "project_analyzer" in skills
    assert "trello" in skills
    assert "branching_simple" in skills


def test_skill_contract_on_common() -> None:
    skills = load_skills(_repo_root(), ["development.common"], [])
    for name, (mod, skill_dict) in skills.items():
        assert skill_dict.get("name") == name or skill_dict.get("name")
        assert skill_dict.get("group")
        assert skill_dict.get("description")
        assert skill_dict.get("input_schema")
        assert callable(getattr(mod, "execute", None)), f"{name} missing execute()"


def test_list_available_skills_includes_frozen_trello() -> None:
    """Inventory still sees Trello code; default config simply does not enable it."""
    all_skills = list_available_skills()
    assert "trello" in all_skills
    assert "project_analyzer" in all_skills
