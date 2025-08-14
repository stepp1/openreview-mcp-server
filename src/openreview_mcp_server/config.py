"""
OpenReview MCP Server Configuration
=================================

Configuration settings for the OpenReview MCP server.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuration settings for OpenReview MCP server."""
    
    APP_NAME: str = "openreview-mcp-server"
    APP_VERSION: str = "0.1.0"
    
    # OpenReview API settings
    OPENREVIEW_BASE_URL: str = "https://api2.openreview.net"
    OPENREVIEW_USERNAME: Optional[str] = None
    OPENREVIEW_PASSWORD: Optional[str] = None
    
    # Default venues to support
    DEFAULT_VENUES: list = [
        "ICLR.cc",
        "NeurIPS.cc", 
        "ICML.cc"
    ]
    
    # Cache settings
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    
    # Export settings
    DEFAULT_EXPORT_DIR: str = "./openreview_exports"
    
    class Config:
        env_file = ".env"
        env_prefix = "OPENREVIEW_"