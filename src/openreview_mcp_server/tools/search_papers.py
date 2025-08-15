"""
Search Papers Tool
=================

Tool for searching papers by keywords within conference venues.
"""

import logging
import mcp.types as types
from typing import Dict, Any, List
from ..client import OpenReviewClient
from ..config import Settings

logger = logging.getLogger(__name__)
settings = Settings()

# Tool definition
search_papers_tool = types.Tool(
    name="search_papers",
    description="Search for papers by keywords within specific conference venues",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Keywords to search for (e.g., 'time series token merging', 'neural networks')",
            },
            "venues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "venue": {
                            "type": "string",
                            "description": "Conference venue (e.g., 'ICLR.cc', 'NeurIPS.cc', 'ICML.cc')",
                        },
                        "year": {
                            "type": "string",
                            "description": "Conference year (e.g., '2024', '2025')",
                        },
                    },
                    "required": ["venue", "year"],
                },
                "description": "List of conference venues and years to search in",
                "minItems": 1,
            },
            "search_fields": {
                "type": "array",
                "items": {"type": "string", "enum": ["title", "abstract", "authors"]},
                "description": "Fields to search in",
                "default": ["title", "abstract"],
            },
            "match_mode": {
                "type": "string",
                "enum": ["any", "all", "exact"],
                "description": "Match any keyword, all keywords, or exact phrase",
                "default": "all",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 20,
                "minimum": 1,
                "maximum": 100,
            },
            "min_score": {
                "type": "number",
                "description": "Minimum match score (0.0 to 1.0)",
                "default": 0.1,
                "minimum": 0.0,
                "maximum": 1.0,
            },
        },
        "required": ["query", "venues"],
    },
)


async def handle_search_papers(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle search_papers tool calls."""
    try:
        query = arguments.get("query")
        venues = arguments.get("venues", [])
        search_fields = arguments.get("search_fields", ["title", "abstract"])
        match_mode = arguments.get("match_mode", "any")
        limit = arguments.get("limit", 20)
        min_score = arguments.get("min_score", 0.1)

        if not query:
            return [
                types.TextContent(type="text", text="Error: Search query is required")
            ]

        if not venues:
            return [
                types.TextContent(
                    type="text", text="Error: At least one venue must be specified"
                )
            ]

        # Initialize client
        client = OpenReviewClient(
            username=settings.openreview_username,
            password=settings.openreview_password,
            base_url=settings.openreview_base_url,
        )

        all_results = []

        # Search in each venue
        for venue_config in venues:
            venue = venue_config.get("venue")
            year = venue_config.get("year")

            if not venue or not year:
                continue

            logger.info(f"Searching in {venue} {year}")

            # Get papers from this venue
            papers = client.get_conference_papers(venue, year)

            if not papers:
                continue

            # Search within these papers
            search_results = client.search_papers(
                query=query,
                papers=papers,
                search_fields=search_fields,
                match_mode=match_mode,
            )

            # Filter by minimum score and add venue context
            for paper_id, result in search_results.items():
                if result["match_score"] >= min_score:
                    result["venue_year"] = f"{venue} {year}"
                    result["paper_id"] = paper_id
                    all_results.append(result)

        if not all_results:
            return [
                types.TextContent(
                    type="text",
                    text=f"No papers found matching query '{query}' in the specified venues",
                )
            ]

        # Sort by match score and apply limit
        all_results.sort(key=lambda x: x["match_score"], reverse=True)
        all_results = all_results[:limit]

        # Format response
        result = f"Search Results for '{query}' (found {len(all_results)} papers):\n\n"

        for i, paper_result in enumerate(all_results, 1):
            result += f"{i}. {paper_result['title']}\n"
            result += f"   Venue: {paper_result['venue_year']}\n"
            result += f"   Authors: {', '.join(paper_result['authors'][:3])}{'...' if len(paper_result['authors']) > 3 else ''}\n"
            result += f"   Match Score: {paper_result['match_score']:.3f}\n"
            result += f"   Matched Terms: {', '.join(paper_result['matched_terms'])}\n"
            result += (
                f"   Matched Fields: {', '.join(paper_result['matches'].keys())}\n"
            )
            result += (
                f"   URL: https://openreview.net/forum?id={paper_result['paper_id']}\n"
            )

            # Show snippet of abstract if it was searched
            if "abstract" in paper_result["matches"]:
                abstract_snippet = (
                    paper_result["abstract"][:150] + "..."
                    if len(paper_result["abstract"]) > 150
                    else paper_result["abstract"]
                )
                result += f"   Abstract: {abstract_snippet}\n"

            result += "\n"

        return [types.TextContent(type="text", text=result)]

    except Exception as e:
        logger.error(f"Error in search_papers: {str(e)}")
        return [
            types.TextContent(type="text", text=f"Error searching papers: {str(e)}")
        ]
