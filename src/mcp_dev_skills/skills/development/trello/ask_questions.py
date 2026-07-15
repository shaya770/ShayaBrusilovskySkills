"""Skill: ask_questions — create Questions/Answers checklists with questions."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

SKILL = {
    "name": "ask_questions",
    "group": "development.trello",
    "description": (
        "Ask questions on card. Automatically creates 'Questions' and 'Answers' "
        "checklists, adds questions, and moves card to Planning. "
        "Questions/answers matched by number."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "card_id": {
                "type": "string",
                "description": "Trello card ID",
            },
            "questions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of questions (in Russian, numbered: '1) ...', '2) ...')",
            },
        },
        "required": ["card_id", "questions"],
    },
}


def _load_config(workspace_root: Path) -> dict:
    """Load Trello config."""
    config_path = workspace_root / ".claude" / "trello.json"
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return {}


def _api_post(url: str, data: dict) -> dict | None:
    """POST request to Trello API."""
    try:
        body = urllib.parse.urlencode(data).encode("utf-8")
        with urllib.request.urlopen(url, data=body, timeout=10) as resp:
            return json.load(resp)
    except Exception:
        return None


def _api_put(url: str, data: dict) -> dict | None:
    """PUT request to Trello API."""
    try:
        body = urllib.parse.urlencode(data).encode("utf-8")
        request = urllib.request.Request(url, data=body, method="PUT")
        with urllib.request.urlopen(request, timeout=10) as resp:
            return json.load(resp)
    except Exception:
        return None


def _get_json(url: str) -> dict | None:
    """GET request to Trello API."""
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.load(resp)
    except Exception:
        return None


def ask_questions(
    workspace_root: Path, card_id: str, questions: list[str]
) -> str:
    """Create Questions/Answers checklists and add questions.

    AUTOMATICALLY:
    - Creates 'Questions' checklist
    - Adds all questions with numbers
    - Creates empty 'Answers' checklist (user fills in)
    - Moves card to Planning

    Workflow rule: Questions/Answers matched by number in item text.
    """
    config = _load_config(workspace_root)
    board_id = config.get("board_id")
    api_key = config.get("api_key")
    token = config.get("token")

    if not board_id or not api_key or not token:
        return "Error: Trello not configured"

    auth = f"key={api_key}&token={token}"

    # 1. Create 'Questions' checklist
    questions_checklist_url = f"https://api.trello.com/1/cards/{card_id}/checklists?{auth}"
    questions_checklist = _api_post(questions_checklist_url, {"name": "Questions"})
    if not questions_checklist:
        return "Error: Failed to create Questions checklist"

    questions_id = questions_checklist.get("id")

    # 2. Add all questions to Questions checklist
    for question in questions:
        item_url = f"https://api.trello.com/1/checklists/{questions_id}/checkItems?{auth}"
        result = _api_post(item_url, {"name": question})
        if not result:
            return f"Error: Failed to add question: {question}"

    # 3. Create empty 'Answers' checklist
    answers_checklist = _api_post(questions_checklist_url, {"name": "Answers"})
    if not answers_checklist:
        return "Error: Failed to create Answers checklist"

    # 4. Move card to Planning
    lists_url = f"https://api.trello.com/1/boards/{board_id}/lists?fields=name&filter=open&{auth}"
    lists = _get_json(lists_url)
    if not lists:
        return "Error: Failed to fetch board columns"

    planning_id = None
    for lst in lists:
        if lst.get("name") == "Planning":
            planning_id = lst.get("id")
            break

    if planning_id:
        move_url = f"https://api.trello.com/1/cards/{card_id}?{auth}"
        _api_put(move_url, {"idList": planning_id})

    lines = [
        f"✓ Created 'Questions' checklist with {len(questions)} questions",
        "✓ Created empty 'Answers' checklist (user will fill in)",
        "✓ Moved card to Planning",
        "",
        "Waiting for user to answer questions in 'Answers' checklist.",
    ]

    return "\n".join(lines)


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    card_id = kwargs.get("card_id")
    questions = kwargs.get("questions", [])

    if not card_id or not questions:
        return "Error: card_id and questions are required"

    return ask_questions(workspace_root, card_id, questions)
