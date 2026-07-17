"""Tests for skill structure after the Trello consolidation."""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_dev_skills.config import load_skills_config
from mcp_dev_skills.loader import load_skills


def _load_all_skills():
    workspace = Path(__file__).parent.parent
    config = load_skills_config(workspace)
    enabled, disabled = config.get_skill_loading_config()
    for path in ("development.trello", "development.common"):
        if path not in enabled:
            enabled = enabled + [path]
    return load_skills(workspace, enabled, disabled)


def test_trello_skill_loads():
    """The consolidated 'trello' skill replaces the 12 old ones."""
    skills = _load_all_skills()

    assert "trello" in skills, "Consolidated 'trello' skill not found"

    # None of the old per-operation skills should be registered anymore
    old_names = [
        "configure_trello", "set_plan", "ask_questions", "change_status",
        "monitor_trello_board", "switch_scope", "get_card", "add_comment",
        "add_checklist_item", "create_checklist", "move_card",
        "update_card_description",
    ]
    leftovers = [name for name in old_names if name in skills]
    assert not leftovers, f"Old Trello skills still registered: {leftovers}"

    print("OK: single 'trello' skill, no leftovers")


def test_trello_actions_in_schema():
    """All actions are declared in the input schema enum."""
    skills = _load_all_skills()
    schema = skills["trello"][1]["input_schema"]

    actions = schema["properties"]["action"]["enum"]
    expected = {
        "configure", "switch_scope", "check_board", "get_card", "set_plan",
        "ask_questions", "change_status", "add_comment", "create_checklist",
        "add_checklist_item",
    }
    assert expected == set(actions), f"Action mismatch: {expected ^ set(actions)}"
    assert "action" in schema.get("required", []), "'action' must be required"

    print(f"OK: {len(actions)} actions declared")


def test_workflow_state_loads():
    """workflow_state snapshot skill is available."""
    skills = _load_all_skills()
    assert "workflow_state" in skills, "'workflow_state' skill not found"
    print("OK: workflow_state loads")


def test_skill_structure():
    """Every enabled skill has required fields and an execute function."""
    skills = _load_all_skills()

    for skill_name, (mod, skill_dict) in skills.items():
        assert isinstance(skill_dict, dict), f"{skill_name}: SKILL not a dict"
        assert skill_dict.get("name"), f"{skill_name}: missing 'name'"
        assert skill_dict.get("group"), f"{skill_name}: missing 'group'"
        assert skill_dict.get("description"), f"{skill_name}: missing 'description'"
        assert skill_dict.get("input_schema"), f"{skill_name}: missing 'input_schema'"
        assert hasattr(mod, "execute"), f"{skill_name}: missing 'execute' function"

    print(f"OK: all {len(skills)} skills have correct structure")


def test_workflow_rules_enforced():
    """change_status transition table forbids Claude moving to Approved/Done."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from mcp_dev_skills.skills.development.trello.trello import CLAUDE_TRANSITIONS

    for target_lists in CLAUDE_TRANSITIONS.values():
        assert "Approved" not in target_lists, "Claude must not move cards to Approved"
        assert "Done" not in target_lists, "Claude must not move cards to Done"

    assert CLAUDE_TRANSITIONS["Inbox"] == ["Planning"]
    assert CLAUDE_TRANSITIONS["Approved"] == ["In Progress"]
    assert CLAUDE_TRANSITIONS["In Progress"] == ["Review"]

    print("OK: workflow transitions locked down")


def test_backend_interface_complete():
    """TrelloBackend implements every BoardBackend method (ABC enforces on instantiation)."""
    from mcp_dev_skills.skills.development.trello.backend import (
        _BACKENDS,
        BoardBackend,
        TrelloBackend,
    )
    from mcp_dev_skills.skills.development.trello.errors import BoardAPIError
    from mcp_dev_skills.skills.development.trello.trello_api import TrelloAPIError

    backend = TrelloBackend("key", "token", "board123", "Test Board")
    assert isinstance(backend, BoardBackend)
    assert backend.board_id == "board123"
    assert _BACKENDS.get("trello") is TrelloBackend

    # Skills catch the neutral error; Trello's error must be a subclass
    assert issubclass(TrelloAPIError, BoardAPIError)

    print("OK: TrelloBackend implements the full BoardBackend interface")


if __name__ == "__main__":
    test_trello_skill_loads()
    test_trello_actions_in_schema()
    test_workflow_state_loads()
    test_skill_structure()
    test_workflow_rules_enforced()
    test_backend_interface_complete()
    print("\nAll tests passed!")
