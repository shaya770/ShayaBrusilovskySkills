"""Entry point: stdio transport initialization, server lifecycle, and CLI."""

from __future__ import annotations

import asyncio
import sys

from mcp.server.stdio import stdio_server

from .server import build_server


async def _run_server() -> None:
    """Run the MCP server over stdio."""
    server = build_server()
    init_options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)


def main() -> None:
    """Console-script entry point."""
    # If first argument is 'setup', run the interactive CLI instead of server
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        from .setup import run_setup
        run_setup()
    else:
        asyncio.run(_run_server())


if __name__ == "__main__":
    main()
