"""
Get Conference Papers Tool
=========================

Tool for fetching papers from specific conferences and years.
"""

import logging
import mcp.types as types
from typing import Dict, Any, List
from ..client import OpenReviewClient
from ..config import Settings

logger = logging.getLogger(__name__)
settings = Settings()

# Tool definition
get_conference_papers_tool = types.Tool(
    name="get_conference_papers",
    description="Fetch all accepted papers from a specific conference venue and year",
    inputSchema={
        "type": "object",
        "properties": {
            "venue": {
                "type": "string",
                "description": "Conference venue (e.g., 'ICLR.cc', 'NeurIPS.cc', 'ICML.cc')",
                "enum": ["ICLR.cc", "NeurIPS.cc", "ICML.cc"]
            },
            "year": {
                "type": "string",
                "description": "Conference year (e.g., '2024', '2025')",
                "pattern": "^20[0-9]{2}$"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of papers to return",
                "default": 50,
                "minimum": 1,
                "maximum": 1000
            },
            "format": {
                "type": "string",
                "enum": ["summary", "detailed"],
                "description": "Format of the response - summary or detailed",
                "default": "summary"
            }
        },
        "required": ["venue", "year"]
    }
)


async def handle_get_conference_papers(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle get_conference_papers tool calls."""
    try:
        venue = arguments.get("venue")
        year = arguments.get("year")
        limit = arguments.get("limit", 50)
        format_type = arguments.get("format", "summary")
        
        if not venue or not year:
            return [types.TextContent(
                type="text",
                text="Error: Both venue and year are required"
            )]
        
        # Initialize client
        client = OpenReviewClient(
            username=settings.OPENREVIEW_USERNAME,
            password=settings.OPENREVIEW_PASSWORD,
            base_url=settings.OPENREVIEW_BASE_URL
        )
        
        # Get conference papers
        papers = client.get_conference_papers(venue, year)
        
        if not papers:
            return [types.TextContent(
                type="text",
                text=f"No papers found for {venue} {year}"
            )]
        
        # Apply limit
        papers = papers[:limit]
        
        # Format response
        result = f"Papers from {venue} {year} (showing {len(papers)} papers):\n\n"
        
        for i, paper in enumerate(papers, 1):
            result += f"{i}. {paper.title}\n"
            result += f"   Authors: {', '.join(paper.authors[:5])}{'...' if len(paper.authors) > 5 else ''}\n"
            result += f"   URL: {paper.url}\n"
            
            if format_type == "detailed":
                # Truncate abstract to reasonable length
                abstract = paper.abstract[:200] + "..." if len(paper.abstract) > 200 else paper.abstract
                result += f"   Abstract: {abstract}\n"
            
            result += "\n"
        
        total_papers = len(papers)
        if limit < total_papers:
            result += f"Note: Showing first {limit} papers out of {total_papers} total papers.\n"
        
        return [types.TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Error in get_conference_papers: {str(e)}")
        return [types.TextContent(
            type="text",
            text=f"Error fetching conference papers: {str(e)}"
        )]