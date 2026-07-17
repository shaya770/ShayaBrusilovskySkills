"""Skill: trello — all board operations in one tool, dispatched by action.

Workflow rules are enforced in code:
- Claude may move: Inbox→Planning, Approved→In Progress, In Progress→Review
- Only the user moves: Planning→Approved, Review→Done
- set_plan backs up the original task to a comment before overwriting
- ask_questions filters technical questions by the user's tech_level

All actions (except `configure`, which is backend-specific onboarding) talk to
the BoardBackend abstraction — see backend.py. Swapping Trello for the own web
interface later means adding a backend there, not touching this file.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from mcp_dev_skills.skills.development.trello.backend import BoardBackend, get_backend
from mcp_dev_skills.skills.development.trello.config_utils import (
    get_tech_level,
    load_config,
)
from mcp_dev_skills.skills.development.trello.errors import BoardAPIError

SKILL = {
    "name": "trello",
    "group": "development.trello",
    "description": (
        "All Trello operations in one tool. Actions: "
        "configure (set up board + columns), switch_scope (list/switch boards), "
        "check_board (one-shot check for work in Inbox/Approved; for continuous "
        "monitoring launch `python -m mcp_dev_skills.monitor --workspace <path>` "
        "as a background process — silent until work appears, then prints and exits), "
        "get_card (full card details), set_plan (write plan, auto-backup original), "
        "ask_questions (Questions/Answers checklists, tech-level filtered), "
        "change_status (move card with workflow validation), "
        "add_comment, create_checklist, add_checklist_item. "
        "Workflow: Claude moves Inbox→Planning, Approved→In Progress, "
        "In Progress→Review; only the user moves cards to Approved/Done."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "configure",
                    "switch_scope",
                    "check_board",
                    "get_card",
                    "set_plan",
                    "ask_questions",
                    "change_status",
                    "add_comment",
                    "create_checklist",
                    "add_checklist_item",
                ],
                "description": "Operation to perform",
            },
            "card_id": {
                "type": "string",
                "description": "Card ID (get_card, set_plan, ask_questions, change_status, add_comment, create_checklist)",
            },
            "plan": {
                "type": "string",
                "description": "Plan text for set_plan (any language)",
            },
            "questions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Numbered questions for ask_questions, e.g. ['1) ...', '2) ...']",
            },
            "new_status": {
                "type": "string",
                "enum": ["Inbox", "Planning", "Approved", "In Progress", "Review", "Done"],
                "description": "Target column for change_status",
            },
            "text": {
                "type": "string",
                "description": "Text for add_comment or add_checklist_item",
            },
            "name": {
                "type": "string",
                "description": "Checklist name for create_checklist (e.g. 'Questions')",
            },
            "checklist_id": {
                "type": "string",
                "description": "Checklist ID for add_checklist_item",
            },
            "board_url": {
                "type": "string",
                "description": "configure: full Trello board URL",
            },
            "api_key": {
                "type": "string",
                "description": "configure: Trello API key (https://trello.com/app-key)",
            },
            "token": {
                "type": "string",
                "description": "configure: Trello API token",
            },
            "scope": {
                "type": "string",
                "description": "configure/switch_scope: app scope name (e.g. 'rental', 'crm')",
            },
            "tech_level": {
                "type": "integer",
                "enum": [0, 1, 2, 3],
                "description": "configure: user's tech level (0=non-technical … 3=expert)",
            },
            "mark_known": {
                "type": "string",
                "description": "switch_scope: comma-separated scopes to register as planned",
            },
        },
        "required": ["action"],
    },
}

# Columns every board must have, in order
REQUIRED_COLUMNS = ["Inbox", "Planning", "Approved", "In Progress", "Review", "Done"]

# Transitions Claude is allowed to make; everything else belongs to the user
CLAUDE_TRANSITIONS = {
    "Inbox": ["Planning"],
    "Planning": [],
    "Approved": ["In Progress"],
    "In Progress": ["Review"],
    "Review": [],
    "Done": [],
}

# Columns that mean "there is work for Claude"
ACTIONABLE_LISTS = {"Approved", "Inbox"}

LEVEL_NAMES = {0: "non-technical", 1: "beginner", 2: "intermediate", 3: "expert"}


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _config_path(workspace_root: Path) -> Path:
    return workspace_root / ".claude" / "trello.json"


def _save_config(workspace_root: Path, config: dict) -> None:
    path = _config_path(workspace_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def _find_list_id(lists: list[dict], name: str) -> str | None:
    for lst in lists:
        if lst.get("name") == name:
            return lst.get("id")
    return None


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _detect_language(text: str) -> str:
    """Return 'ru', 'en', or 'mixed' by Cyrillic ratio."""
    cyrillic_ratio = len([c for c in text if 0x0400 <= ord(c) <= 0x04FF]) / max(len(text), 1)
    if cyrillic_ratio > 0.7:
        return "ru"
    if cyrillic_ratio < 0.1:
        return "en"
    return "mixed"


_TECH_KEYWORDS = {
    # Russian
    "язык", "программирование", "код", "алгоритм", "сложность", "оптимизация",
    "базе данных", "бд", "sql", "api", "фреймворк", "библиотека", "npm",
    "модуль", "компонент", "производительность", "нагрузка", "тест",
    "интеграция", "развёртывание", "deploy", "docker", "git", "версия",
    # English
    "code", "programming", "language", "database", "framework",
    "library", "algorithm", "complexity", "optimization", "performance",
    "testing", "integration", "deployment", "architecture",
    "scalability", "cache", "concurrency", "async", "protocol",
}


def _is_technical_question(text: str) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in _TECH_KEYWORDS)


def _filter_questions_by_tech_level(questions: list[str], tech_level: int) -> list[str]:
    if tech_level >= 3:
        return questions
    return [q for q in questions if not (tech_level == 0 and _is_technical_question(q))]


# ---------------------------------------------------------------------------
# Backend-specific onboarding (Trello only)
# ---------------------------------------------------------------------------

def _action_configure(
    workspace_root: Path,
    board_url: str,
    api_key: str,
    token: str,
    scope: str = "default",
    tech_level: int = 1,
) -> str:
    from mcp_dev_skills.skills.development.trello.trello_api import get as api_get

    match = re.search(r"/b/([a-z0-9]+)", board_url, re.IGNORECASE)
    if not match:
        return "Error: Invalid board URL. Expected: https://trello.com/b/BOARD_ID/name"
    board_id = match.group(1)

    if not 0 <= tech_level <= 3:
        return "Error: tech_level must be 0-3"
    if not scope or not scope.replace("_", "").replace("-", "").isalnum():
        return "Error: scope must be alphanumeric (letters, numbers, dash, underscore)"

    # Validate credentials, then ensure columns exist via the backend interface
    board_data = api_get(f"boards/{board_id}", api_key, token, {"fields": "name"})
    board_name = board_data.get("name", "Unknown")

    from mcp_dev_skills.skills.development.trello.backend import TrelloBackend

    backend = TrelloBackend(api_key, token, board_id, board_name)
    existing = {lst["name"] for lst in backend.get_lists()}

    messages = [f"Board: {board_name}"]
    for col_name in REQUIRED_COLUMNS:
        if col_name in existing:
            messages.append(f"  ✓ {col_name}")
        else:
            backend.create_list(col_name)
            messages.append(f"  + {col_name} (created)")

    config = load_config(workspace_root)
    config["api_key"] = api_key
    config["token"] = token
    config["current_scope"] = scope
    config.setdefault("backend", "trello")
    config.setdefault("boards", {})
    config.setdefault("known_scopes", [])
    config["boards"][scope] = {
        "board_id": board_id,
        "board_url": board_url,
        "board_name": board_name,
        "tech_level": tech_level,
        "language": "auto",
    }
    if scope not in config["known_scopes"]:
        config["known_scopes"] = sorted(config["known_scopes"] + [scope])
    _save_config(workspace_root, config)

    lines = [
        f"✓ Trello board configured for scope: '{scope}'",
        "",
        *messages,
        "",
        f"Technical level: {LEVEL_NAMES.get(tech_level, '?')}",
    ]
    if len(config["boards"]) > 1:
        lines.append(f"Configured scopes: {', '.join(sorted(config['boards']))}")
        lines.append(f"Currently active: '{scope}'")
    return "\n".join(lines)


def _action_switch_scope(
    workspace_root: Path,
    scope: str | None = None,
    mark_known: str | None = None,
) -> str:
    config = load_config(workspace_root)
    config.setdefault("boards", {})
    config.setdefault("known_scopes", [])

    if mark_known:
        new_scopes = [s.strip() for s in mark_known.split(",") if s.strip()]
        for s in new_scopes:
            if not s.replace("_", "").replace("-", "").isalnum():
                return f"Error: Invalid scope name '{s}'. Use alphanumeric, dash, underscore."
            if s not in config["known_scopes"]:
                config["known_scopes"].append(s)
        config["known_scopes"] = sorted(config["known_scopes"])
        _save_config(workspace_root, config)
        return (
            f"✓ Marked as known: {', '.join(new_scopes)}\n\n"
            f"Known scopes: {', '.join(config['known_scopes'])}"
        )

    if not scope:
        configured = sorted(config["boards"])
        current = config.get("current_scope", "default")
        lines = []
        if configured:
            lines.append("Configured Trello boards:")
            for s in configured:
                board = config["boards"][s]
                marker = " ← current" if s == current else ""
                level = LEVEL_NAMES.get(board.get("tech_level", 1), "?")
                lines.append(f"  ✓ {s}{marker} — {board.get('board_name', '?')} (tech: {level})")
        unconfigured = [s for s in config["known_scopes"] if s not in configured]
        if unconfigured:
            lines.append("Known scopes (not yet configured):")
            for s in unconfigured:
                lines.append(f"  ○ {s}")
        if not lines:
            lines.append("No Trello boards configured. Run trello(action='configure', ...) first.")
        return "\n".join(lines)

    if scope not in config["boards"]:
        if scope in config["known_scopes"]:
            return (
                f"Error: Scope '{scope}' is known but not configured yet.\n"
                f"Run trello(action='configure', scope='{scope}', ...)"
            )
        return (
            f"Error: Scope '{scope}' not found.\n"
            f"Run trello(action='configure', scope='{scope}', ...) "
            f"or trello(action='switch_scope', mark_known='{scope}')"
        )

    config["current_scope"] = scope
    _save_config(workspace_root, config)
    board = config["boards"][scope]
    level = LEVEL_NAMES.get(board.get("tech_level", 1), "?")
    return (
        f"✓ Switched to scope: '{scope}'\n\n"
        f"Board: {board.get('board_name', '?')}\n"
        f"Tech level: {level}\n"
        f"Language: {board.get('language', 'auto')}"
    )


# ---------------------------------------------------------------------------
# Backend-agnostic actions
# ---------------------------------------------------------------------------

def _action_check_board(backend: BoardBackend) -> str:
    """One-shot check for actionable cards. No polling — the loop belongs to the client."""
    work: list[str] = []
    for lst in backend.get_lists():
        if lst["name"] not in ACTIONABLE_LISTS:
            continue
        for card in backend.get_cards(lst["id"]):
            if "wait" not in card["labels"]:
                work.append(f"  [{lst['name']}] {card['name']} (id: {card['id']})")

    if not work:
        return "No work found in Inbox/Approved."
    return "🚨 WORK FOUND:\n" + "\n".join(work)


def _action_get_card(backend: BoardBackend, card_id: str) -> str:
    card = backend.get_card(card_id)

    lines = [f"📇 Card: {card['name'] or 'Untitled'}", ""]

    if card["desc"]:
        lines.extend(["📝 Description:", card["desc"], ""])

    if card["labels"]:
        lines.append(f"🏷️  Labels: {', '.join(card['labels'])}")
        lines.append("")

    for checklist in backend.get_checklists(card_id):
        lines.append(f"✓ {checklist['name']} (id: {checklist['id']}):")
        if checklist["items"]:
            for item in checklist["items"]:
                status = "☑️" if item["complete"] else "☐"
                lines.append(f"  {status} {item['name']}")
        else:
            lines.append("  (empty)")
        lines.append("")

    comments = backend.get_comments(card_id)
    if comments:
        lines.append("💬 Comments:")
        for comment in comments:
            lines.append(f"  {comment['author']}: {comment['text']}")

    return "\n".join(lines)


def _action_set_plan(workspace_root: Path, backend: BoardBackend, card_id: str, plan: str) -> str:
    card = backend.get_card(card_id)
    original_desc = card["desc"]

    detected_lang = _detect_language(original_desc or card["name"] or "")

    # One-time backup of the original task before overwriting
    if original_desc:
        backend.add_comment(card_id, f"🤖 Original task:\n{original_desc}")

    backend.set_description(card_id, plan)

    # Remember detected language in the scope config
    config = load_config(workspace_root)
    current_scope = config.get("current_scope", "default")
    if current_scope in config.get("boards", {}):
        config["boards"][current_scope]["language"] = detected_lang
        _save_config(workspace_root, config)

    lines = ["✓ Plan written to card"]
    if original_desc:
        lines.append("✓ Original task saved to comment")
    lang_display = {"ru": "Russian", "en": "English", "mixed": "Mixed"}.get(detected_lang, "?")
    lines.append(f"✓ Task language detected: {lang_display}")
    return "\n".join(lines)


def _action_ask_questions(
    workspace_root: Path, backend: BoardBackend, card_id: str, questions: list[str]
) -> str:
    tech_level = get_tech_level(workspace_root)
    filtered = _filter_questions_by_tech_level(questions, tech_level)
    skipped = len(questions) - len(filtered)

    if not filtered:
        return (
            f"Note: All {len(questions)} questions were filtered out "
            f"(user tech level: {tech_level}). No Questions checklist created."
        )

    questions_checklist = backend.create_checklist(card_id, "Questions")
    for question in filtered:
        backend.add_checklist_item(questions_checklist["id"], question)

    backend.create_checklist(card_id, "Answers")

    planning_id = _find_list_id(backend.get_lists(), "Planning")
    if planning_id:
        backend.move_card(card_id, planning_id)

    lines = [f"✓ Created 'Questions' checklist with {len(filtered)} question(s)"]
    if skipped > 0:
        lines.append(
            f"  (skipped {skipped} technical question(s) — "
            f"user level: {LEVEL_NAMES.get(tech_level, '?')})"
        )
    lines.extend([
        "✓ Created empty 'Answers' checklist (user will fill in)",
        "✓ Moved card to Planning",
        "",
        "Waiting for user to answer questions in 'Answers' checklist.",
    ])
    return "\n".join(lines)


def _action_change_status(backend: BoardBackend, card_id: str, new_status: str) -> str:
    card = backend.get_card(card_id)
    lists = backend.get_lists()

    current_status = None
    target_list_id = None
    for lst in lists:
        if lst["id"] == card["list_id"]:
            current_status = lst["name"]
        if lst["name"] == new_status:
            target_list_id = lst["id"]

    if not current_status:
        return "Error: Could not determine card's current column"
    if not target_list_id:
        available = ", ".join(lst["name"] for lst in lists)
        return f"Error: Column '{new_status}' not found. Available: {available}"

    allowed = CLAUDE_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        if new_status in ("Approved", "Done"):
            return f"⚠️ Cannot move to {new_status} (user decision). Currently in: {current_status}"
        return f"Invalid transition: {current_status}→{new_status}"

    backend.move_card(card_id, target_list_id)
    return f"✓ Card moved: {current_status} → {new_status}"


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def execute(workspace_root: Path, **kwargs) -> str:
    """Dispatch to the requested action."""
    action = kwargs.get("action")
    if not action:
        return "Error: action is required"

    try:
        # configure and switch_scope work without an existing backend
        if action == "configure":
            board_url = kwargs.get("board_url")
            api_key = kwargs.get("api_key")
            token = kwargs.get("token")
            if not board_url or not api_key or not token:
                return "Error: configure requires board_url, api_key, token"
            return _action_configure(
                workspace_root, board_url, api_key, token,
                kwargs.get("scope", "default"), kwargs.get("tech_level", 1),
            )

        if action == "switch_scope":
            return _action_switch_scope(
                workspace_root, kwargs.get("scope"), kwargs.get("mark_known")
            )

        backend = get_backend(workspace_root)
        if backend is None:
            return "Error: Trello not configured. Run trello(action='configure', ...) first."

        if action == "check_board":
            return _action_check_board(backend)

        card_id = kwargs.get("card_id")

        if action == "get_card":
            if not card_id:
                return "Error: get_card requires card_id"
            return _action_get_card(backend, card_id)

        if action == "set_plan":
            plan = kwargs.get("plan")
            if not card_id or not plan:
                return "Error: set_plan requires card_id and plan"
            return _action_set_plan(workspace_root, backend, card_id, plan)

        if action == "ask_questions":
            questions = kwargs.get("questions")
            if not card_id or not questions:
                return "Error: ask_questions requires card_id and questions"
            return _action_ask_questions(workspace_root, backend, card_id, questions)

        if action == "change_status":
            new_status = kwargs.get("new_status")
            if not card_id or not new_status:
                return "Error: change_status requires card_id and new_status"
            return _action_change_status(backend, card_id, new_status)

        if action == "add_comment":
            text = kwargs.get("text")
            if not card_id or not text:
                return "Error: add_comment requires card_id and text"
            backend.add_comment(card_id, f"🤖 {text}")
            return "✓ Comment added"

        if action == "create_checklist":
            name = kwargs.get("name")
            if not card_id or not name:
                return "Error: create_checklist requires card_id and name"
            checklist = backend.create_checklist(card_id, name)
            return f"✓ Checklist '{name}' created (id: {checklist['id']})"

        if action == "add_checklist_item":
            checklist_id = kwargs.get("checklist_id")
            text = kwargs.get("text")
            if not checklist_id or not text:
                return "Error: add_checklist_item requires checklist_id and text"
            backend.add_checklist_item(checklist_id, text)
            return "✓ Item added to checklist"

        return f"Error: Unknown action '{action}'"

    except BoardAPIError as exc:
        return f"Error: {exc}"
