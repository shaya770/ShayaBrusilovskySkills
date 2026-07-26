"""Core tests: path sandbox (security.py)."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_dev_skills.security import PathEscapeError, get_workspace_root, resolve_in_workspace


def test_get_workspace_root_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert get_workspace_root() == tmp_path.resolve()


def test_get_workspace_root_explicit(tmp_path: Path) -> None:
    assert get_workspace_root(tmp_path) == tmp_path.resolve()


def test_resolve_relative_file_inside_workspace(tmp_path: Path) -> None:
    target = tmp_path / "src" / "app.py"
    target.parent.mkdir()
    target.write_text("x", encoding="utf-8")

    resolved = resolve_in_workspace("src/app.py", tmp_path)
    assert resolved == target.resolve()


def test_resolve_nested_path(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b" / "c.txt"
    nested.parent.mkdir(parents=True)
    nested.write_text("ok", encoding="utf-8")

    resolved = resolve_in_workspace("a/b/c.txt", tmp_path)
    assert resolved == nested.resolve()


def test_reject_parent_traversal(tmp_path: Path) -> None:
    with pytest.raises(PathEscapeError):
        resolve_in_workspace("../outside.txt", tmp_path)


def test_reject_deep_traversal(tmp_path: Path) -> None:
    with pytest.raises(PathEscapeError):
        resolve_in_workspace("safe/../../outside.txt", tmp_path)


def test_absolute_path_treated_as_workspace_relative(tmp_path: Path) -> None:
    """Absolute inputs must not escape; they are joined under the workspace root."""
    # On Windows this becomes workspace / "C:" / "Windows" / ... which stays inside
    # the sandbox after resolve, or raises if it escapes. Either way: not /etc/passwd.
    try:
        resolved = resolve_in_workspace("/etc/passwd", tmp_path)
    except PathEscapeError:
        return
    assert tmp_path.resolve() in resolved.parents or resolved == tmp_path.resolve()
    assert resolved != Path("/etc/passwd").resolve()


def test_workspace_root_itself_allowed(tmp_path: Path) -> None:
    resolved = resolve_in_workspace(".", tmp_path)
    assert resolved == tmp_path.resolve()
