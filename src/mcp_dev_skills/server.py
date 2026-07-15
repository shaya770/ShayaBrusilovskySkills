"""MCP server: tool registration, dynamic discovery, and request routing."""

from __future__ import annotations

from pathlib import Path

import mcp.types as types
from mcp.server import Server

from .config import SkillsConfig, load_skills_config
from .security import PathEscapeError, get_workspace_root
from .tools import file_operations, project_analyzer

# Static registry of every skill this server knows how to run. Exposure is
# decided per-request by the workspace's .skills.json (see build_server).
_TOOL_DEFINITIONS: dict[str, types.Tool] = {
    project_analyzer.NAME: types.Tool(
        name=project_analyzer.NAME,
        description=(
            "Recursively scan the workspace and return a lightweight tree plus "
            "structural hints (languages, config files). Respects .gitignore."
        ),
        inputSchema=project_analyzer.INPUT_SCHEMA,
    ),
    file_operations.NAME: types.Tool(
        name=file_operations.NAME,
        description="Safely read a workspace file's contents (path-sandboxed).",
        inputSchema=file_operations.INPUT_SCHEMA,
    ),
}


def _run_tool(name: str, arguments: dict, workspace_root: Path) -> str:
    if name == project_analyzer.NAME:
        depth = arguments.get("depth", 3)
        return project_analyzer.analyze_project_structure(workspace_root, depth=depth)
    if name == file_operations.NAME:
        return file_operations.safe_read_file(
            workspace_root, arguments["file_path"]
        )
    raise ValueError(f"Unknown tool: {name}")


def build_server(workspace_root: Path | None = None) -> Server:
    """Construct the MCP server bound to a workspace sandbox."""
    root = get_workspace_root(workspace_root)
    server: Server = Server("mcp-dev-skills")

    def current_config() -> SkillsConfig:
        # Re-read on each request so config edits take effect without restart.
        return load_skills_config(root)

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        config = current_config()
        return [
            tool
            for name, tool in _TOOL_DEFINITIONS.items()
            if config.is_enabled(name)
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        config = current_config()

        if name not in _TOOL_DEFINITIONS:
            raise ValueError(f"Unknown tool: {name}")

        if not config.is_enabled(name):
            raise ValueError(
                f"Tool [{name}] is disabled by the current project's "
                f"configuration (.skills.json)"
            )

        try:
            result = _run_tool(name, arguments or {}, root)
        except PathEscapeError as exc:
            raise ValueError(f"Sandbox violation: {exc}") from exc

        return [types.TextContent(type="text", text=result)]

    return server
