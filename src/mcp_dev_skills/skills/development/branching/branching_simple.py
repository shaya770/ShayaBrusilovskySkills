"""Skill: branching_simple — parallel branch management for AI work.

Parallel branch workflow (independent from current project state):
1. create: Create a new branch (feature/bugfix/refactor) without switching current
2. list: Show all active branches with status
3. finish: Complete branch work (test, push, merge to main)

No Trello integration. Branches work independently from main project.
Config via .skills.json: "branching_mode": "simple" or "disabled"
"""

from __future__ import annotations

import subprocess
from pathlib import Path

SKILL = {
    "name": "branching_simple",
    "group": "development.branching",
    "description": (
        "Parallel branch management for AI work. Actions: create (new branch), "
        "list (active branches), finish (complete + test + push + merge). "
        "No Trello integration. Branches work independently from current project state. "
        "Enable via .skills.json: branching_mode='simple'"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "list", "finish"],
                "description": (
                    "create: Create new parallel branch. "
                    "list: Show all active branches. "
                    "finish: Complete work (test, push, merge to main)."
                ),
            },
            "branch_name": {
                "type": "string",
                "description": "Branch name without type prefix (e.g., 'auth-oauth'). For create action.",
            },
            "branch_type": {
                "type": "string",
                "enum": ["feature", "bugfix", "refactor"],
                "description": "Branch type (creates prefix: feature/, bugfix/, refactor/). For create action.",
            },
            "filter": {
                "type": "string",
                "description": "Filter branches by prefix (e.g., 'feature/'). For list action.",
            },
        },
        "required": ["action"],
    },
}


# ============================================================================
# Git utilities
# ============================================================================


def _run_git(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run git command and return (return_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def _get_current_branch(workspace_root: Path) -> str | None:
    """Get current branch name."""
    code, branch, _ = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], workspace_root)
    return branch if code == 0 else None


def _branch_exists(branch_name: str, workspace_root: Path) -> bool:
    """Check if branch exists."""
    code, _, _ = _run_git(["rev-parse", "--verify", branch_name], workspace_root)
    return code == 0


def _create_branch_isolated(full_branch_name: str, workspace_root: Path) -> tuple[bool, str]:
    """Create branch from main without switching current branch."""
    # Fetch latest
    _run_git(["fetch", "origin"], workspace_root)

    # Create branch from main (don't switch)
    code, _, err = _run_git(["branch", full_branch_name, "origin/main"], workspace_root)
    if code != 0:
        code, _, err = _run_git(["branch", full_branch_name, "main"], workspace_root)
        if code != 0:
            return False, f"Failed to create branch: {err}"

    return True, f"Branch '{full_branch_name}' created (current branch unchanged)"


def _get_branch_commits(branch_name: str, workspace_root: Path) -> int:
    """Get commit count in branch vs main."""
    code, stdout, _ = _run_git(
        ["log", "main.." + branch_name, "--oneline"],
        workspace_root,
    )
    if code == 0:
        return len([line for line in stdout.split("\n") if line.strip()])
    return 0


def _list_all_branches(workspace_root: Path) -> list[tuple[str, int]]:
    """List all local branches with commit counts."""
    code, stdout, _ = _run_git(["branch"], workspace_root)
    if code != 0:
        return []

    branches = []
    for line in stdout.split("\n"):
        line = line.strip()
        if line:
            # Remove leading * if it's current branch
            branch_name = line.lstrip("* ")
            commits = _get_branch_commits(branch_name, workspace_root)
            branches.append((branch_name, commits))

    return branches


def _run_tests(workspace_root: Path) -> tuple[bool, str]:
    """Run tests (pytest if exists, otherwise skip)."""
    test_indicators = ["pytest.ini", "setup.cfg", "pyproject.toml", "requirements.txt"]

    has_pytest = any((workspace_root / f).exists() for f in test_indicators)
    if not has_pytest:
        return True, "No pytest configuration found, skipping tests"

    code, stdout, stderr = _run_git(["stash"], workspace_root)  # Stash any uncommitted changes

    try:
        result = subprocess.run(
            ["pytest", "-q"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        test_ok = result.returncode == 0
        output = result.stdout + result.stderr
        return test_ok, output if output else "Tests passed"
    except FileNotFoundError:
        return True, "pytest not installed, skipping"
    except Exception as e:
        return False, str(e)
    finally:
        _run_git(["stash", "pop"], workspace_root)  # Restore stashed changes


def _finish_branch(branch_name: str, workspace_root: Path) -> tuple[bool, str]:
    """Finish branch: test, push, merge to main."""
    messages = []

    # Test
    messages.append("Running tests...")
    test_ok, test_output = _run_tests(workspace_root)
    messages.append(f"  {'✓' if test_ok else '✗'} Tests: {test_output[:100]}")
    if not test_ok:
        return False, "\n".join(messages)

    # Push
    messages.append("Pushing branch...")
    code, _, err = _run_git(["push", "-u", "origin", branch_name], workspace_root)
    if code != 0:
        messages.append(f"  ✗ Push failed: {err}")
        return False, "\n".join(messages)
    messages.append(f"  ✓ Pushed to origin/{branch_name}")

    # Merge
    messages.append("Merging to main...")
    _run_git(["checkout", "main"], workspace_root)  # Switch to main
    code, _, err = _run_git(["merge", branch_name], workspace_root)
    if code != 0:
        messages.append(f"  ✗ Merge failed: {err}")
        return False, "\n".join(messages)
    messages.append(f"  ✓ Merged {branch_name} into main")

    # Push main
    code, _, err = _run_git(["push", "origin", "main"], workspace_root)
    if code != 0:
        messages.append(f"  ✗ Failed to push main: {err}")
        return False, "\n".join(messages)
    messages.append(f"  ✓ Pushed main to origin")

    return True, "\n".join(messages)


# ============================================================================
# Actions
# ============================================================================


def _action_create(workspace_root: Path, branch_name: str, branch_type: str = "feature") -> str:
    """Create new branch."""
    if not branch_name:
        return "Error: branch_name required"
    if not branch_type:
        branch_type = "feature"

    full_name = f"{branch_type}/{branch_name}"

    if _branch_exists(full_name, workspace_root):
        return f"Error: Branch '{full_name}' already exists"

    success, message = _create_branch_isolated(full_name, workspace_root)
    return message if success else f"Error: {message}"


def _action_list(workspace_root: Path, filter_prefix: str | None = None) -> str:
    """List all active branches."""
    branches = _list_all_branches(workspace_root)

    if not branches:
        return "No branches found"

    if filter_prefix:
        branches = [(name, commits) for name, commits in branches if name.startswith(filter_prefix)]

    if not branches:
        return f"No branches matching '{filter_prefix}'"

    result = "Active branches:\n"
    for name, commits in sorted(branches):
        icon = "●" if commits > 0 else "○"
        result += f"  {icon} {name:30} ({commits} commits)\n"

    return result


def _action_finish(workspace_root: Path, branch_name: str) -> str:
    """Finish branch work: test, push, merge."""
    if not branch_name:
        return "Error: branch_name required"

    if not _branch_exists(branch_name, workspace_root):
        return f"Error: Branch '{branch_name}' does not exist"

    success, message = _finish_branch(branch_name, workspace_root)
    return message


# ============================================================================
# Main
# ============================================================================


def execute(workspace_root: Path, action: str, branch_name: str | None = None,
            branch_type: str = "feature", filter: str | None = None, **kwargs) -> str:
    """Execute branching action."""

    if action == "create":
        return _action_create(workspace_root, branch_name or "", branch_type)

    elif action == "list":
        return _action_list(workspace_root, filter)

    elif action == "finish":
        return _action_finish(workspace_root, branch_name or "")

    else:
        return f"Unknown action: {action}"
