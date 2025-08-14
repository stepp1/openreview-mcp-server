# OpenReview MCP server

A Model Context Protocol (MCP) server that provides access to OpenReview data for research and analysis. This server allows you to search for users, fetch papers, and export research data from major ML conferences (ICML, ICLR, NeurIPS).

## Features

- **User search**: Find OpenReview profiles by email address
- **Paper retrieval**: Fetch all papers by a specific author
- **Conference papers**: Get papers from specific venues (ICLR, NeurIPS, ICML) and years
- **Keyword search**: Search papers by keywords across multiple conferences
- **JSON&PDF export**: Export search results to PDF and JSON files for convenient reading or further analysis and coding assistant usage

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

From the command line:

```sh
claude mcp add-json openreview '{"command":"openreview-mcp-server","cwd":"/install/dir/openreview-mcp-server","env":{"OPENREVIEW_USERNAME":"username","OPENREVIEW_PASSWORD":"password","OPENREVIEW_BASE_URL":"https://api2.openreview.net","OPENREVIEW_DEFAULT_EXPORT_DIR":"./openreview_exports"}}'
```

Then run the query:

```
Can you please use search_papers tool from the openreview mcp with keywords "time series token merging", match mode "all", venues ICLR and ICML 2025?
...
Please export the contents of this paper.
```
 
## Example output

![Example Output](public/output.jpg)

## Available tools

### search_user
Find a user profile by email address.

```python
search_user(email="researcher@university.edu", include_publications=true)
```

### get_user_papers
Fetch all papers published by a specific user.

```python
get_user_papers(email="researcher@university.edu", format="detailed")
```

### get_conference_papers
Get papers from a specific conference and year.

```python
get_conference_papers(venue="ICLR.cc", year="2024", limit=50)
```

### search_papers
Search for papers by keywords across multiple conferences.

```python
search_papers(
  query="time series token merging",
  match_mode="all",
  venues=[
    {"venue": "ICLR.cc", "year": "2024"},
    {"venue": "NeurIPS.cc", "year": "2024"}
  ],
  limit=20
)
```

### export_papers
Export search results to JSON files for analysis.

```python
export_papers(
  query="neural networks",
  venues=[
    {"venue": "ICLR.cc", "year": "2024"},
    {"venue": "ICML.cc", "year": "2024"}
  ],
  max_papers=1, 
  download_pdfs=true, 
  include_abstracts=true,
  export_dir="./research_exports"
)
```

## Example workflow

1. Search for papers on a topic of interest:
```python
search_papers(query="time series forecasting", match_mode="all", venues=[{"venue": "ICLR.cc", "year": "2024"}])
```

2. Export relevant papers to JSON:
```python
export_papers(query="time series token merging", venues=[{"venue":"ICML.cc","year":"2025"}], max_papers=1, download_pdfs=true, include_abstracts=true)
```

3. Use the exported JSON files with Claude Code to implement methods inspired by the research.

## Supported conferences

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