"""
OpenReview MCP Server Configuration
=================================

Configuration settings for the OpenReview MCP server.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuration settings for OpenReview MCP server."""

    app_name: str = "openreview-mcp-server"
    app_version: str = "0.1.0"
    openreview_base_url: str = "https://api2.openreview.net"
    openreview_username: Optional[str] = None
    openreview_password: Optional[str] = None

    # Default venues to support
    default_venues: list = ["ICLR.cc", "NeurIPS.cc", "ICML.cc"]

    # Cache settings
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour

    # Export settings
    default_export_dir: str = "./openreview_exports"

    class Config:
        env_file = ".env"
        env_prefix = "OPENREVIEW_"
