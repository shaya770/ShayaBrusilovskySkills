"""Skill: ask_questions — create Questions/Answers checklists with questions."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from .config_utils import get_board_config, get_api_credentials, get_tech_level

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


def _detect_language(text: str) -> str:
    """Detect if text is Russian or English.

    Returns: 'ru', 'en', or 'mixed'
    """
    cyrillic_ratio = len([c for c in text if ord(c) >= 0x0400 and ord(c) <= 0x04FF]) / max(len(text), 1)
    if cyrillic_ratio > 0.7:
        return "ru"
    elif cyrillic_ratio < 0.1:
        return "en"
    else:
        return "mixed"


def _is_technical_question(text: str) -> bool:
    """Detect if question is technical.

    Returns True if question contains technical keywords.
    """
    tech_keywords = {
        # Russian
        "язык", "программирование", "код", "алгоритм", "сложность", "оптимизация",
        "базе данных", "бд", "sql", "api", "фреймворк", "библиотека", "npm",
        "модуль", "компонент", "производительность", "нагрузка", "тест",
        "интеграция", "развёртывание", "deploy", "docker", "git", "версия",
        # English
        "code", "programming", "language", "database", "sql", "api", "framework",
        "library", "algorithm", "complexity", "optimization", "performance",
        "testing", "integration", "deployment", "docker", "architecture",
        "scalability", "cache", "concurrency", "async", "protocol",
    }
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in tech_keywords)


def _filter_questions_by_tech_level(questions: list[str], tech_level: int) -> list[str]:
    """Filter questions based on user's technical level.

    tech_level 0: non-technical (skip tech questions)
    tech_level 1: beginner (include all but expert questions)
    tech_level 2: intermediate (include all but most expert)
    tech_level 3: expert (include all questions)
    """
    if tech_level >= 3:
        return questions

    filtered = []
    for q in questions:
        is_tech = _is_technical_question(q)
        # Non-technical level: skip all tech questions
        if tech_level == 0 and is_tech:
            continue
        filtered.append(q)

    return filtered


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
    - Loads user's technical level from current scope config
    - Filters questions based on tech_level (0=non-tech skips tech questions)
    - Creates 'Questions' checklist with filtered questions
    - Creates empty 'Answers' checklist (user fills in)
    - Moves card to Planning

    Workflow rule: Questions/Answers matched by number in item text.
                   Non-technical users (tech_level=0) never get tech questions.
    """
    board = get_board_config(workspace_root)
    if not board:
        return "Error: Trello not configured for any scope"

    credentials = get_api_credentials(workspace_root)
    if not credentials:
        return "Error: Trello API credentials not configured"

    board_id = board.get("board_id")
    api_key, token = credentials
    tech_level = get_tech_level(workspace_root)

    if not board_id or not api_key or not token:
        return "Error: Trello not configured"

    # Filter questions based on user's tech level
    filtered_questions = _filter_questions_by_tech_level(questions, tech_level)
    skipped = len(questions) - len(filtered_questions)

    if not filtered_questions:
        return (
            f"Note: All {len(questions)} questions were filtered out "
            f"(user tech level: {tech_level} / skipped {skipped} technical questions).\n"
            "No Questions checklist created."
        )

    auth = f"key={api_key}&token={token}"

    # 1. Create 'Questions' checklist
    questions_checklist_url = f"https://api.trello.com/1/cards/{card_id}/checklists?{auth}"
    questions_checklist = _api_post(questions_checklist_url, {"name": "Questions"})
    if not questions_checklist:
        return "Error: Failed to create Questions checklist"

    questions_id = questions_checklist.get("id")

    # 2. Add filtered questions to Questions checklist
    for question in filtered_questions:
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
        f"✓ Created 'Questions' checklist with {len(filtered_questions)} question(s)",
    ]
    if skipped > 0:
        level_name = {0: "non-technical", 1: "beginner", 2: "intermediate", 3: "expert"}.get(tech_level, "?")
        lines.append(f"  (skipped {skipped} technical question(s) — user level: {level_name})")
    lines.extend([
        "✓ Created empty 'Answers' checklist (user will fill in)",
        "✓ Moved card to Planning",
        "",
        "Waiting for user to answer questions in 'Answers' checklist.",
    ])

    return "\n".join(lines)


def execute(workspace_root: Path, **kwargs) -> str:
    """Execute the skill."""
    card_id = kwargs.get("card_id")
    questions = kwargs.get("questions", [])

    if not card_id or not questions:
        return "Error: card_id and questions are required"

    return ask_questions(workspace_root, card_id, questions)
