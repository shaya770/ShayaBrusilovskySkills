"""Tests for Trello skills structure and validation."""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_dev_skills.config import load_skills_config
from mcp_dev_skills.loader import load_skills


def test_trello_skills_load():
    """Verify all Trello skills load correctly."""
    workspace = Path(__file__).parent.parent
    config = load_skills_config(workspace)
    enabled, disabled = config.get_skill_loading_config()

    # Enable trello skills
    if "development.trello" not in enabled:
        enabled = enabled + ["development.trello"]

    skills = load_skills(workspace, enabled, disabled)

    # Filter for Trello skills
    trello_skills = {
        name: skill for name, (_, skill) in skills.items()
        if skill.get("group") == "development.trello"
    }

    assert len(trello_skills) > 0, "No Trello skills found"
    print(f"OK: Loaded {len(trello_skills)} Trello skills")


def test_smart_skills_exist():
    """Verify smart skills are defined."""
    workspace = Path(__file__).parent.parent
    config = load_skills_config(workspace)
    enabled, disabled = config.get_skill_loading_config()

    if "development.trello" not in enabled:
        enabled = enabled + ["development.trello"]

    skills = load_skills(workspace, enabled, disabled)

    required_smart_skills = {
        "set_plan": "Write plan with auto-backup",
        "ask_questions": "Create Questions/Answers checklists",
        "change_status": "Move card with workflow validation",
    }

    for skill_name, expected_desc_part in required_smart_skills.items():
        assert skill_name in skills, f"Missing smart skill: {skill_name}"
        skill = skills[skill_name][1]
        desc = skill.get("description", "")
        print(f"OK {skill_name}: {desc[:60]}...")


def test_skill_structure():
    """Verify each skill has required fields."""
    workspace = Path(__file__).parent.parent
    config = load_skills_config(workspace)
    enabled, disabled = config.get_skill_loading_config()

    if "development.trello" not in enabled:
        enabled = enabled + ["development.trello"]

    skills = load_skills(workspace, enabled, disabled)

    for skill_name, (mod, skill_dict) in skills.items():
        # Check SKILL dict structure
        assert isinstance(skill_dict, dict), f"{skill_name}: SKILL not a dict"
        assert skill_dict.get("name"), f"{skill_name}: missing 'name'"
        assert skill_dict.get("group"), f"{skill_name}: missing 'group'"
        assert skill_dict.get("description"), f"{skill_name}: missing 'description'"
        assert skill_dict.get("input_schema"), f"{skill_name}: missing 'input_schema'"

        # Check execute function exists
        assert hasattr(mod, "execute"), f"{skill_name}: missing 'execute' function"

    print(f"OK All {len(skills)} skills have correct structure")


def test_workflow_rules_documented():
    """Verify smart skills have workflow rules in docstring."""
    workspace = Path(__file__).parent.parent
    config = load_skills_config(workspace)
    enabled, disabled = config.get_skill_loading_config()

    if "development.trello" not in enabled:
        enabled = enabled + ["development.trello"]

    skills = load_skills(workspace, enabled, disabled)

    smart_skills = ["set_plan", "ask_questions", "change_status"]

    for skill_name in smart_skills:
        assert skill_name in skills, f"Missing smart skill: {skill_name}"
        mod, skill_dict = skills[skill_name]

        # Get the main function docstring (prefer the named function over execute)
        func = getattr(mod, skill_name, None)
        if not func:
            func = getattr(mod, "execute", None)
        assert func, f"{skill_name}: no function found"

        doc = func.__doc__ or ""
        assert len(doc) > 50, f"{skill_name}: docstring too short ({len(doc)} chars)"
        has_rule_doc = (
            "WORKFLOW" in doc or
            "Automatically" in doc or
            "AUTOMATICALLY" in doc or
            "RULE" in doc or
            "CRITICAL" in doc or
            "Workflow rule" in doc
        )
        assert has_rule_doc, f"{skill_name}: missing workflow rule documentation\n{doc[:100]}"

        print(f"OK {skill_name}: documented with workflow rules")


if __name__ == "__main__":
    test_trello_skills_load()
    test_smart_skills_exist()
    test_skill_structure()
    test_workflow_rules_documented()
    print("\nAll tests passed!")
