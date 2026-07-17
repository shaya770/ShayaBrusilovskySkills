"""Wait-for-work Trello monitor — run as a BACKGROUND PROCESS, not as an MCP tool.

Launch (Claude runs this via its shell in background mode):

    python -m mcp_dev_skills.monitor --workspace <path> [--interval 30]

Behavior (silence is the mechanism):
- Polls the current scope's board every --interval seconds.
- Prints NOTHING while there is no work → the background runner stays quiet,
  Claude is not woken up, zero tokens are spent on idle checks.
- When actionable cards appear in Inbox/Approved (without the 'wait' label),
  prints them to stdout and EXITS with code 0 → the runner notifies Claude,
  who reads the output and starts working on the cards.
- After finishing the work, relaunch the monitor.

Errors: missing config exits immediately with code 1; transient API errors
are retried silently, but 10 consecutive failures exit with code 1 so the
monitor never spins dead forever.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from mcp_dev_skills.skills.development.trello.backend import get_backend
from mcp_dev_skills.skills.development.trello.config_utils import get_current_scope
from mcp_dev_skills.skills.development.trello.errors import BoardAPIError

ACTIONABLE_LISTS = {"Approved", "Inbox"}
MAX_CONSECUTIVE_FAILURES = 10


def check_once(workspace_root: Path) -> list[dict]:
    """One board pass. Returns actionable cards (no 'wait' label)."""
    backend = get_backend(workspace_root)
    if backend is None:
        raise BoardAPIError("Trello not configured (run trello action='configure' first)")

    work: list[dict] = []
    for lst in backend.get_lists():
        if lst["name"] not in ACTIONABLE_LISTS:
            continue
        for card in backend.get_cards(lst["id"]):
            if "wait" not in card["labels"]:
                work.append({"column": lst["name"], "name": card["name"], "id": card["id"]})
    return work


def run(workspace_root: Path, interval: int) -> int:
    failures = 0
    while True:
        try:
            work = check_once(workspace_root)
            failures = 0
        except BoardAPIError as exc:
            if "not configured" in str(exc):
                print(f"Monitor error: {exc}")
                return 1
            failures += 1
            if failures >= MAX_CONSECUTIVE_FAILURES:
                print(f"Monitor stopped after {failures} consecutive API failures: {exc}")
                return 1
            time.sleep(interval)
            continue

        if work:
            scope = get_current_scope(workspace_root)
            print(f"🚨 WORK FOUND (scope: {scope}):")
            for card in work:
                print(f"  [{card['column']}] {card['name']} (id: {card['id']})")
            print()
            print("Process the cards, then relaunch the monitor:")
            print(f"  python -m mcp_dev_skills.monitor --workspace {workspace_root} --interval {interval}")
            return 0

        time.sleep(interval)


def main() -> None:
    # Windows consoles may default to cp1251 — emoji/Cyrillic must survive
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Silent wait-for-work Trello monitor")
    parser.add_argument("--workspace", required=True, help="Workspace root path")
    parser.add_argument("--interval", type=int, default=30, help="Poll interval, seconds (min 5)")
    args = parser.parse_args()

    workspace_root = Path(args.workspace).resolve()
    if not workspace_root.is_dir():
        print(f"Workspace not found: {workspace_root}")
        sys.exit(1)

    sys.exit(run(workspace_root, max(args.interval, 5)))


if __name__ == "__main__":
    main()
