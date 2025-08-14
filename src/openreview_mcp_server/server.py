"""
OpenReview MCP Server
====================

This module implements an MCP server for interacting with OpenReview.
"""

import logging
import mcp.types as types
from typing import Dict, Any, List
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
from mcp.server.stdio import stdio_server
from .config import Settings
from .tools import (
    handle_search_user, search_user_tool,
    handle_get_user_papers, get_user_papers_tool,
    handle_get_conference_papers, get_conference_papers_tool,
    handle_search_papers, search_papers_tool,
    handle_export_papers, export_papers_tool
)

settings = Settings()
logger = logging.getLogger("openreview-mcp-server")
logger.setLevel(logging.INFO)
server = Server(settings.app_name)


@server.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available OpenReview research tools."""
    return [
        search_user_tool,
        get_user_papers_tool,
        get_conference_papers_tool,
        search_papers_tool,
        export_papers_tool
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls for OpenReview research functionality."""
    logger.debug(f"Calling tool {name} with arguments {arguments}")
    try:
        if name == "search_user":
            return await handle_search_user(arguments)
        elif name == "get_user_papers":
            return await handle_get_user_papers(arguments)
        elif name == "get_conference_papers":
            return await handle_get_conference_papers(arguments)
        elif name == "search_papers":
            return await handle_search_papers(arguments)
        elif name == "export_papers":
            return await handle_export_papers(arguments)
        else:
            return [types.TextContent(type="text", text=f"Error: Unknown tool {name}")]
    except Exception as e:
        logger.error(f"Tool error: {str(e)}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the server async context."""
    async with stdio_server() as streams:
        await server.run(
            streams[0],
            streams[1],
            InitializationOptions(
                server_name=settings.app_name,
                server_version=settings.app_version,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(resources_changed=True),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())