"""Git utilities for agent-based branch workflow."""

from __future__ import annotations

import subprocess
import json
from pathlib import Path


def run_git(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
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


def get_current_branch(workspace_root: Path) -> str | None:
    """Get currently checked out branch."""
    code, stdout, _ = run_git(["rev-parse", "--abbrev-ref", "HEAD"], workspace_root)
    if code == 0:
        return stdout
    return None


def branch_exists(branch_name: str, workspace_root: Path) -> bool:
    """Check if branch exists locally."""
    code, stdout, _ = run_git(["branch", "--list", branch_name], workspace_root)
    return code == 0 and bool(stdout.strip())


def create_branch(branch_name: str, workspace_root: Path, from_branch: str = "main") -> tuple[bool, str]:
    """Create new branch from specified base branch.

    Returns: (success, message)
    """
    # Ensure we have latest main
    code, _, err = run_git(["fetch", "origin"], workspace_root)
    if code != 0:
        return False, f"Failed to fetch: {err}"

    # Create branch from origin/main (or fallback to local main)
    code, _, err = run_git(["checkout", "-b", branch_name, f"origin/{from_branch}"], workspace_root)
    if code != 0:
        # Try local fallback
        code, _, err = run_git(["checkout", "-b", branch_name, from_branch], workspace_root)
        if code != 0:
            return False, f"Failed to create branch: {err}"

    return True, f"Branch '{branch_name}' created from '{from_branch}'"


def get_branch_commits(branch_name: str, workspace_root: Path, main_branch: str = "main") -> list[dict]:
    """Get commits on branch since it diverged from main.

    Returns: list of {sha, message, author, date}
    """
    # Get commits on branch but not on main
    code, stdout, _ = run_git(
        ["log", f"origin/{main_branch}..{branch_name}", "--pretty=format:%H|%s|%an|%ai"],
        workspace_root,
    )

    if code != 0:
        return []

    commits = []
    for line in stdout.split("\n"):
        if line.strip():
            parts = line.split("|")
            if len(parts) == 4:
                commits.append({
                    "sha": parts[0][:7],  # short sha
                    "message": parts[1],
                    "author": parts[2],
                    "date": parts[3][:10],  # date only
                })

    return commits


def get_branch_info(branch_name: str, workspace_root: Path) -> dict:
    """Get detailed information about a branch.

    Returns: {exists, is_current, commits_count, last_commit, files_changed}
    """
    is_current = get_current_branch(workspace_root) == branch_name
    exists = branch_exists(branch_name, workspace_root)

    if not exists:
        return {
            "exists": False,
            "is_current": False,
            "branch": branch_name,
            "commits_count": 0,
            "commits": [],
            "files_changed": 0,
        }

    commits = get_branch_commits(branch_name, workspace_root)

    # Count changed files (approximation using last commit)
    files_changed = 0
    if commits:
        last_commit_sha = commits[-1]["sha"]
        code, stdout, _ = run_git(["show", "--name-only", "--pretty=format:"], workspace_root)
        files_changed = len([l for l in stdout.split("\n") if l.strip()])

    return {
        "exists": True,
        "is_current": is_current,
        "branch": branch_name,
        "commits_count": len(commits),
        "commits": commits,
        "files_changed": files_changed,
    }


def list_branches(workspace_root: Path) -> list[str]:
    """List all local branches."""
    code, stdout, _ = run_git(["branch", "--format=%(refname:short)"], workspace_root)
    if code == 0:
        return [line.strip() for line in stdout.split("\n") if line.strip()]
    return []


def get_changed_files(branch_name: str, workspace_root: Path, main_branch: str = "main") -> list[str]:
    """Get list of files changed on branch since main."""
    code, stdout, _ = run_git(
        ["diff", "--name-only", f"origin/{main_branch}...{branch_name}"],
        workspace_root,
    )

    if code == 0:
        return [line.strip() for line in stdout.split("\n") if line.strip()]
    return []
