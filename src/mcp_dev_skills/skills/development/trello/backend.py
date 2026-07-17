"""Board backend abstraction — the seam for leaving Trello.

All workflow skills talk to this interface (lists, cards, comments,
checklists) and never to a concrete API. Today the only implementation is
TrelloBackend. When the own web interface arrives:

1. Implement WebBackend(BoardBackend) here (or next to it),
2. register it in _BACKENDS,
3. set  "backend": "web"  in .claude/trello.json (plus its credentials).

Nothing in trello.py, monitor.py, branching or workflow_state changes.

Normalized data shapes (every backend must return exactly these):
- list:            {"id": str, "name": str}
- card (in list):  {"id": str, "name": str, "labels": [str, ...]}
- card (full):     {"id": str, "name": str, "desc": str,
                    "labels": [str, ...], "list_id": str}
- comment:         {"author": str, "text": str}
- checklist:       {"id": str, "name": str,
                    "items": [{"name": str, "complete": bool}, ...]}
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from mcp_dev_skills.skills.development.trello.errors import BoardAPIError


class BoardBackend(ABC):
    """One configured board of the current scope."""

    board_id: str
    board_name: str

    @abstractmethod
    def get_lists(self) -> list[dict]:
        """All open columns of the board."""

    @abstractmethod
    def create_list(self, name: str) -> dict:
        """Create a column."""

    @abstractmethod
    def get_cards(self, list_id: str) -> list[dict]:
        """Cards in a column (with label names)."""

    @abstractmethod
    def get_card(self, card_id: str) -> dict:
        """Full card: name, desc, labels, list_id."""

    @abstractmethod
    def move_card(self, card_id: str, list_id: str) -> None:
        """Move card to a column."""

    @abstractmethod
    def set_description(self, card_id: str, desc: str) -> None:
        """Overwrite card description."""

    @abstractmethod
    def add_comment(self, card_id: str, text: str) -> None:
        """Add a comment to a card."""

    @abstractmethod
    def get_comments(self, card_id: str) -> list[dict]:
        """Comments on a card."""

    @abstractmethod
    def get_checklists(self, card_id: str) -> list[dict]:
        """Checklists on a card, with items."""

    @abstractmethod
    def create_checklist(self, card_id: str, name: str) -> dict:
        """Create a checklist; returns {"id", "name"}."""

    @abstractmethod
    def add_checklist_item(self, checklist_id: str, text: str) -> None:
        """Append an item to a checklist."""


class TrelloBackend(BoardBackend):
    """Trello REST API implementation."""

    def __init__(self, api_key: str, token: str, board_id: str, board_name: str = "?"):
        self._key = api_key
        self._token = token
        self.board_id = board_id
        self.board_name = board_name

    def _get(self, path: str, params: dict | None = None):
        from mcp_dev_skills.skills.development.trello.trello_api import get
        return get(path, self._key, self._token, params)

    def _post(self, path: str, params: dict | None = None):
        from mcp_dev_skills.skills.development.trello.trello_api import post
        return post(path, self._key, self._token, params)

    def _put(self, path: str, params: dict | None = None):
        from mcp_dev_skills.skills.development.trello.trello_api import put
        return put(path, self._key, self._token, params)

    def get_lists(self) -> list[dict]:
        lists = self._get(f"boards/{self.board_id}/lists", {"fields": "name", "filter": "open"})
        return [{"id": lst["id"], "name": lst["name"]} for lst in lists]

    def create_list(self, name: str) -> dict:
        lst = self._post(f"boards/{self.board_id}/lists", {"name": name})
        return {"id": lst["id"], "name": lst["name"]}

    def get_cards(self, list_id: str) -> list[dict]:
        cards = self._get(f"lists/{list_id}/cards", {"fields": "name,labels"})
        return [
            {
                "id": card["id"],
                "name": card["name"],
                "labels": [label.get("name", "") for label in card.get("labels", [])],
            }
            for card in cards
        ]

    def get_card(self, card_id: str) -> dict:
        card = self._get(f"cards/{card_id}", {"fields": "name,desc,labels,idList"})
        return {
            "id": card["id"],
            "name": card.get("name", ""),
            "desc": card.get("desc", ""),
            "labels": [label.get("name", "") for label in card.get("labels", [])],
            "list_id": card.get("idList", ""),
        }

    def move_card(self, card_id: str, list_id: str) -> None:
        self._put(f"cards/{card_id}", {"idList": list_id})

    def set_description(self, card_id: str, desc: str) -> None:
        self._put(f"cards/{card_id}", {"desc": desc})

    def add_comment(self, card_id: str, text: str) -> None:
        self._post(f"cards/{card_id}/actions/comments", {"text": text})

    def get_comments(self, card_id: str) -> list[dict]:
        actions = self._get(f"cards/{card_id}/actions", {"filter": "commentCard"})
        return [
            {
                "author": action.get("memberCreator", {}).get("fullName", "Unknown"),
                "text": action.get("data", {}).get("text", ""),
            }
            for action in actions or []
        ]

    def get_checklists(self, card_id: str) -> list[dict]:
        checklists = self._get(f"cards/{card_id}/checklists")
        return [
            {
                "id": checklist["id"],
                "name": checklist.get("name", ""),
                "items": [
                    {
                        "name": item.get("name", ""),
                        "complete": item.get("state") == "complete",
                    }
                    for item in checklist.get("checkItems", [])
                ],
            }
            for checklist in checklists or []
        ]

    def create_checklist(self, card_id: str, name: str) -> dict:
        checklist = self._post(f"cards/{card_id}/checklists", {"name": name})
        return {"id": checklist["id"], "name": checklist.get("name", name)}

    def add_checklist_item(self, checklist_id: str, text: str) -> None:
        self._post(f"checklists/{checklist_id}/checkItems", {"name": text})


# Registered backend types; the config's top-level "backend" field selects one.
# Future: "web": WebBackend (own development web interface).
_BACKENDS = {
    "trello": TrelloBackend,
}


def get_backend(workspace_root: Path) -> BoardBackend | None:
    """Build the backend for the current scope, or None if not configured."""
    from mcp_dev_skills.skills.development.trello.config_utils import (
        get_api_credentials,
        get_board_config,
        load_config,
    )

    board = get_board_config(workspace_root)
    credentials = get_api_credentials(workspace_root)
    if not board or not board.get("board_id") or not credentials:
        return None

    backend_type = load_config(workspace_root).get("backend", "trello")
    backend_cls = _BACKENDS.get(backend_type)
    if backend_cls is None:
        raise BoardAPIError(
            f"Unknown backend '{backend_type}'. Available: {', '.join(sorted(_BACKENDS))}"
        )

    api_key, token = credentials
    return backend_cls(api_key, token, board["board_id"], board.get("board_name", "?"))
