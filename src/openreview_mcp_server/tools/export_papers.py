"""
Export Papers Tool
=================

Tool for exporting papers to JSON files for further analysis.
"""

import json
import logging
import os
from datetime import datetime
import mcp.types as types
from typing import Dict, Any, List
from ..client import OpenReviewClient
from ..config import Settings

logger = logging.getLogger(__name__)
settings = Settings()

# Tool definition
export_papers_tool = types.Tool(
    name="export_papers",
    description="Export papers to JSON files for further analysis and code development",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Keywords to search for before export"
            },
            "venues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "venue": {
                            "type": "string",
                            "description": "Conference venue (e.g., 'ICLR.cc', 'NeurIPS.cc', 'ICML.cc')"
                        },
                        "year": {
                            "type": "string",
                            "description": "Conference year (e.g., '2024', '2025')"
                        }
                    },
                    "required": ["venue", "year"]
                },
                "description": "List of conference venues and years to export from",
                "minItems": 1
            },
            "export_dir": {
                "type": "string",
                "description": "Directory to export JSON files to",
                "default": "./openreview_exports"
            },
            "filename": {
                "type": "string",
                "description": "Base filename for the export (without extension)",
                "default": None
            },
            "include_abstracts": {
                "type": "boolean",
                "description": "Whether to include full abstracts in export",
                "default": True
            },
            "min_score": {
                "type": "number",
                "description": "Minimum match score for search results (0.0 to 1.0)",
                "default": 0.2,
                "minimum": 0.0,
                "maximum": 1.0
            }
        },
        "required": ["query", "venues"]
    }
)


async def handle_export_papers(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle export_papers tool calls."""
    try:
        query = arguments.get("query")
        venues = arguments.get("venues", [])
        export_dir = arguments.get("export_dir", settings.DEFAULT_EXPORT_DIR)
        filename = arguments.get("filename")
        include_abstracts = arguments.get("include_abstracts", True)
        min_score = arguments.get("min_score", 0.2)
        
        if not query:
            return [types.TextContent(
                type="text",
                text="Error: Search query is required"
            )]
        
        if not venues:
            return [types.TextContent(
                type="text",
                text="Error: At least one venue must be specified"
            )]
        
        # Create export directory if it doesn't exist
        os.makedirs(export_dir, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            query_safe = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
            query_safe = query_safe.replace(' ', '_')[:50]  # Limit length
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"openreview_{query_safe}_{timestamp}"
        
        # Initialize client
        client = OpenReviewClient(
            username=settings.OPENREVIEW_USERNAME,
            password=settings.OPENREVIEW_PASSWORD,
            base_url=settings.OPENREVIEW_BASE_URL
        )
        
        export_data = {
            "query": query,
            "search_date": datetime.now().isoformat(),
            "venues": venues,
            "min_score": min_score,
            "papers": []
        }
        
        total_papers = 0
        
        # Search in each venue
        for venue_config in venues:
            venue = venue_config.get("venue")
            year = venue_config.get("year")
            
            if not venue or not year:
                continue
            
            logger.info(f"Searching and exporting from {venue} {year}")
            
            # Get papers from this venue
            papers = client.get_conference_papers(venue, year)
            
            if not papers:
                continue
            
            # Search within these papers
            search_results = client.search_papers(
                query=query,
                papers=papers,
                search_fields=["title", "abstract"],
                match_mode="any"
            )
            
            # Filter by minimum score and prepare for export
            venue_papers = []
            for paper_id, result in search_results.items():
                if result['match_score'] >= min_score:
                    paper_data = {
                        "id": paper_id,
                        "title": result['title'],
                        "authors": result['authors'],
                        "venue": f"{venue} {year}",
                        "url": f"https://openreview.net/forum?id={paper_id}",
                        "pdf_url": f"https://openreview.net/pdf?id={paper_id}",
                        "match_score": result['match_score'],
                        "matched_terms": result['matched_terms'],
                        "matched_fields": list(result['matches'].keys())
                    }
                    
                    if include_abstracts:
                        paper_data["abstract"] = result['abstract']
                    
                    venue_papers.append(paper_data)
                    total_papers += 1
            
            # Sort venue papers by match score
            venue_papers.sort(key=lambda x: x['match_score'], reverse=True)
            export_data["papers"].extend(venue_papers)
        
        if not export_data["papers"]:
            return [types.TextContent(
                type="text",
                text=f"No papers found matching query '{query}' with minimum score {min_score}"
            )]
        
        # Sort all papers by match score
        export_data["papers"].sort(key=lambda x: x['match_score'], reverse=True)
        
        # Write to JSON file
        json_file = os.path.join(export_dir, f"{filename}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        # Create a summary file for quick reference
        summary_data = {
            "query": query,
            "total_papers": len(export_data["papers"]),
            "venues_searched": venues,
            "top_papers": [
                {
                    "title": paper["title"],
                    "venue": paper["venue"],
                    "match_score": paper["match_score"],
                    "url": paper["url"]
                }
                for paper in export_data["papers"][:10]  # Top 10
            ],
            "export_file": json_file,
            "created_at": datetime.now().isoformat()
        }
        
        summary_file = os.path.join(export_dir, f"{filename}_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        # Format response
        result = f"Export completed successfully!\n\n"
        result += f"Query: '{query}'\n"
        result += f"Papers found: {total_papers}\n"
        result += f"Venues searched: {', '.join([f"{v['venue']} {v['year']}" for v in venues])}\n"
        result += f"Min match score: {min_score}\n\n"
        result += f"Files created:\n"
        result += f"- Main export: {json_file}\n"
        result += f"- Summary: {summary_file}\n\n"
        result += f"Top 5 papers by relevance:\n"
        
        for i, paper in enumerate(export_data["papers"][:5], 1):
            result += f"{i}. {paper['title']} (Score: {paper['match_score']:.3f})\n"
            result += f"   {paper['venue']}\n\n"
        
        result += f"Use these JSON files with Claude Code to implement methods inspired by the papers!"
        
        return [types.TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Error in export_papers: {str(e)}")
        return [types.TextContent(
            type="text",
            text=f"Error exporting papers: {str(e)}"
        )]