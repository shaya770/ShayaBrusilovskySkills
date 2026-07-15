"""Entry point: stdio transport initialization and server lifecycle."""

from __future__ import annotations

import asyncio

from mcp.server.stdio import stdio_server

from .server import build_server


async def _run() -> None:
    server = build_server()
    init_options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)


def main() -> None:
    """Console-script entry point."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
