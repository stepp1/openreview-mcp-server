# OpenReview MCP Server

A Model Context Protocol (MCP) server that provides access to OpenReview data for research and analysis. This server allows you to search for users, fetch papers, and export research data from major ML conferences.

## Features

- **User Search**: Find OpenReview profiles by email address
- **Paper Retrieval**: Fetch all papers by a specific author
- **Conference Papers**: Get papers from specific venues (ICLR, NeurIPS, ICML) and years
- **Keyword Search**: Search papers by keywords across multiple conferences
- **JSON Export**: Export search results to JSON files for further analysis

## Installation

```bash
pip install -e .
```

## Configuration

Create a `.env` file with your OpenReview credentials for local development:

```env
OPENREVIEW_USERNAME=your_email@domain.com
OPENREVIEW_PASSWORD=your_password
```

## Usage with Claude Code

Add this server to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "openreview": {
      "command": "python",
      "args": ["-m", "openreview_mcp_server"],
      "env": {
        "OPENREVIEW_USERNAME": "your_email@domain.com",
        "OPENREVIEW_PASSWORD": "your_password"
      }
    }
  }
}
```

## Available Tools

### search_user
Find a user profile by email address.

```
search_user(email="researcher@university.edu", include_publications=true)
```

### get_user_papers
Fetch all papers published by a specific user.

```
get_user_papers(email="researcher@university.edu", format="detailed")
```

### get_conference_papers
Get papers from a specific conference and year.

```
get_conference_papers(venue="ICLR.cc", year="2024", limit=50)
```

### search_papers
Search for papers by keywords across multiple conferences.

```
search_papers(
  query="time series token merging",
  venues=[
    {"venue": "ICLR.cc", "year": "2024"},
    {"venue": "NeurIPS.cc", "year": "2024"}
  ],
  limit=20
)
```

### export_papers
Export search results to JSON files for analysis.

```
export_papers(
  query="neural networks",
  venues=[
    {"venue": "ICLR.cc", "year": "2024"},
    {"venue": "ICML.cc", "year": "2024"}
  ],
  export_dir="./research_exports"
)
```

## Example Workflow

1. Search for papers on a topic of interest:
```
search_papers(query="time series forecasting", venues=[{"venue": "ICLR.cc", "year": "2024"}])
```

2. Export relevant papers to JSON:
```
export_papers(query="time series forecasting", venues=[{"venue": "ICLR.cc", "year": "2024"}])
```

3. Use the exported JSON files with Claude Code to implement methods inspired by the research.

## Supported Conferences

- ICLR (International Conference on Learning Representations)
- NeurIPS (Conference on Neural Information Processing Systems)
- ICML (International Conference on Machine Learning)

## Development

```bash
# Install in development mode
pip install -e ".[dev,test]"

# Run tests
pytest

# Format code
black .
```

## License

MIT License