"""
Get User Papers Tool
===================

Tool for fetching all papers by a specific user.
"""

import logging
import mcp.types as types
from typing import Dict, Any, List
from ..client import OpenReviewClient
from ..config import Settings

logger = logging.getLogger(__name__)
settings = Settings()

# Tool definition
get_user_papers_tool = types.Tool(
    name="get_user_papers",
    description="Fetch all papers published by a specific user identified by email",
    inputSchema={
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "Email address of the user whose papers to fetch"
            },
            "format": {
                "type": "string",
                "enum": ["summary", "detailed"],
                "description": "Format of the response - summary or detailed",
                "default": "summary"
            }
        },
        "required": ["email"]
    }
)


async def handle_get_user_papers(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle get_user_papers tool calls."""
    try:
        email = arguments.get("email")
        format_type = arguments.get("format", "summary")
        
        if not email:
            return [types.TextContent(
                type="text",
                text="Error: Email address is required"
            )]
        
        # Initialize client
        client = OpenReviewClient(
            username=settings.OPENREVIEW_USERNAME,
            password=settings.OPENREVIEW_PASSWORD,
            base_url=settings.OPENREVIEW_BASE_URL
        )
        
        # Get user papers
        papers = client.get_user_papers(email)
        
        if not papers:
            return [types.TextContent(
                type="text",
                text=f"No papers found for user: {email}"
            )]
        
        # Format response
        result = f"Papers by {email} ({len(papers)} total):\n\n"
        
        for i, paper in enumerate(papers, 1):
            result += f"{i}. {paper.title}\n"
            result += f"   Venue: {paper.venue}\n"
            result += f"   Authors: {', '.join(paper.authors)}\n"
            result += f"   URL: {paper.url}\n"
            
            if format_type == "detailed":
                # Truncate abstract to reasonable length
                abstract = paper.abstract[:300] + "..." if len(paper.abstract) > 300 else paper.abstract
                result += f"   Abstract: {abstract}\n"
            
            result += "\n"
        
        return [types.TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Error in get_user_papers: {str(e)}")
        return [types.TextContent(
            type="text",
            text=f"Error fetching user papers: {str(e)}"
        )]