"""
Search User Tool
===============

Tool for finding OpenReview user profiles by email.
"""

import logging
import mcp.types as types
from typing import Dict, Any, List
from ..client import OpenReviewClient
from ..config import Settings

logger = logging.getLogger(__name__)
settings = Settings()

# Tool definition
search_user_tool = types.Tool(
    name="search_user",
    description="Find an OpenReview user profile by email address",
    inputSchema={
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "Email address of the user to search for"
            },
            "include_publications": {
                "type": "boolean", 
                "description": "Whether to include the user's publications",
                "default": True
            }
        },
        "required": ["email"]
    }
)


async def handle_search_user(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle search_user tool calls."""
    try:
        email = arguments.get("email")
        include_publications = arguments.get("include_publications", True)
        
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
        
        # Search for user
        profile = client.find_user_by_email(email, with_publications=include_publications)
        
        if not profile:
            return [types.TextContent(
                type="text", 
                text=f"No user profile found for email: {email}"
            )]
        
        # Format response
        result = f"User Profile Found:\n"
        result += f"ID: {profile.id}\n"
        result += f"Name: {profile.name or 'N/A'}\n"
        result += f"Emails: {', '.join(profile.emails)}\n"
        
        if profile.relations:
            result += f"\nRelations:\n"
            for relation in profile.relations:
                result += f"  - {relation.get('name', 'N/A')} ({relation.get('relation', 'N/A')})\n"
        
        if include_publications and profile.publications:
            result += f"\nPublications ({len(profile.publications)} total):\n"
            for i, pub in enumerate(profile.publications[:5], 1):  # Show first 5
                result += f"  {i}. {pub.title}\n"
                result += f"     Venue: {pub.venue}\n"
                result += f"     Authors: {', '.join(pub.authors[:3])}{'...' if len(pub.authors) > 3 else ''}\n\n"
            
            if len(profile.publications) > 5:
                result += f"  ... and {len(profile.publications) - 5} more publications\n"
        
        return [types.TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Error in search_user: {str(e)}")
        return [types.TextContent(
            type="text",
            text=f"Error searching for user: {str(e)}"
        )]