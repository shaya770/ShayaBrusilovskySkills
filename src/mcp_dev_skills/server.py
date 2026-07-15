"""MCP server: tool registration, dynamic discovery, and request routing."""

from __future__ import annotations

from pathlib import Path

import mcp.types as types
from mcp.server import Server

from .config import load_skills_config
from .loader import load_skills
from .security import PathEscapeError, get_workspace_root


def build_server(workspace_root: Path | None = None) -> Server:
    """Construct the MCP server bound to a workspace sandbox."""
    root = get_workspace_root(workspace_root)
    server: Server = Server("mcp-dev-skills")

    def current_skills() -> dict[str, tuple]:
        # Re-read config on each request so changes take effect without restart
        config = load_skills_config(root)
        enabled_paths, disabled_skills = config.get_skill_loading_config()
        return load_skills(root, enabled_paths, disabled_skills)

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        skills = current_skills()
        tools = []
        for skill_name, (mod, skill_dict) in skills.items():
            tool = types.Tool(
                name=skill_name,
                description=skill_dict.get("description", ""),
                inputSchema=skill_dict.get("input_schema", {}),
            )
            tools.append(tool)
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        skills = current_skills()

        if name not in skills:
            raise ValueError(f"Unknown or disabled skill: {name}")

        mod, skill_dict = skills[name]

        try:
            result = mod.execute(root, **(arguments or {}))
        except PathEscapeError as exc:
            raise ValueError(f"Sandbox violation: {exc}") from exc
        except (FileNotFoundError, IsADirectoryError) as exc:
            raise ValueError(str(exc)) from exc

        return [types.TextContent(type="text", text=result)]

    return server
