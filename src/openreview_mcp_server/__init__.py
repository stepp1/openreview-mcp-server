"""
OpenReview MCP Server
====================

A Model Context Protocol server for interacting with OpenReview.
"""

import asyncio
from .server import main as async_main


def main():
    """Synchronous wrapper for the async main function."""
    asyncio.run(async_main())


__version__ = "0.1.0"
__all__ = ["main"]
