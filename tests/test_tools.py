"""
Tests for MCP tools functionality.
"""

import pytest
import tempfile
import json
import os
from unittest.mock import Mock, patch, AsyncMock
import mcp.types as types

# Import tools to test
from openreview_mcp_server.tools.search_papers import handle_search_papers
from openreview_mcp_server.tools.export_papers import handle_export_papers


class TestSearchPapersTool:
    """Test search_papers tool functionality."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock OpenReview client."""
        client = Mock()

        # Mock search results
        mock_papers = {
            "paper1": {
                "title": "Neural Networks for Time Series Analysis",
                "authors": ["Alice Smith", "Bob Johnson"],
                "abstract": "This paper presents neural networks for time series forecasting using transformers.",
                "venue": "ICLR.cc/2024",
                "match_score": 0.95,
                "matched_terms": ["neural", "networks", "time", "series"],
                "matches": {
                    "title": ["neural", "networks"],
                    "abstract": ["time", "series"],
                },
            },
            "paper2": {
                "title": "Deep Learning Applications in Computer Vision",
                "authors": ["Charlie Brown", "Diana Lee"],
                "abstract": "Applications of deep learning neural networks in computer vision tasks.",
                "venue": "NeurIPS.cc/2024",
                "match_score": 0.8,
                "matched_terms": ["neural", "networks"],
                "matches": {"title": ["deep"], "abstract": ["neural", "networks"]},
            },
        }

        client.search_papers.return_value = mock_papers
        return client

    @patch("openreview_mcp_server.tools.search_papers.OpenReviewClient")
    @pytest.mark.asyncio
    async def test_search_papers_basic(self, mock_client_class):
        """Test basic search_papers functionality."""
        # Setup mock
        mock_client = Mock()
        mock_client.search_papers.return_value = {
            "paper1": {
                "title": "Neural Networks for Time Series",
                "authors": ["Alice", "Bob"],
                "abstract": "This paper presents neural networks.",
                "venue": "ICLR.cc/2024",
                "match_score": 0.95,
                "matched_terms": ["neural", "networks"],
                "matches": {"title": ["neural", "networks"]},
            }
        }
        mock_client_class.return_value = mock_client

        # Test arguments
        arguments = {
            "query": "neural networks",
            "venues": [{"venue": "ICLR.cc", "year": "2024"}],
            "search_fields": ["title", "abstract"],
            "match_mode": "any",
            "max_results": 10,
        }

        # Execute test
        result = await handle_search_papers(arguments)

        # Verify results
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)

        response_text = result[0].text
        assert "found 1 papers" in response_text
        assert "Neural Networks for Time Series" in response_text
        assert "0.950" in response_text

    @patch("openreview_mcp_server.tools.search_papers.OpenReviewClient")
    @pytest.mark.asyncio
    async def test_search_papers_no_results(self, mock_client_class):
        """Test search_papers with no results."""
        # Setup mock
        mock_client = Mock()
        mock_client.search_papers.return_value = {}
        mock_client_class.return_value = mock_client

        # Test arguments
        arguments = {
            "query": "quantum computing",
            "venues": [{"venue": "ICLR.cc", "year": "2024"}],
        }

        # Execute test
        result = await handle_search_papers(arguments)

        # Verify results
        assert len(result) == 1
        response_text = result[0].text
        assert "No papers found" in response_text

    @pytest.mark.asyncio
    async def test_search_papers_missing_query(self):
        """Test search_papers with missing query."""
        arguments = {"venues": [{"venue": "ICLR.cc", "year": "2024"}]}

        result = await handle_search_papers(arguments)

        assert len(result) == 1
        response_text = result[0].text
        assert "Error: Search query is required" in response_text


class TestExportPapersTool:
    """Test export_papers tool functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test exports."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @patch("openreview_mcp_server.tools.export_papers.OpenReviewClient")
    @patch("openreview_mcp_server.tools.export_papers.download_pdf")
    @patch("openreview_mcp_server.tools.export_papers.extract_up_to_references")
    @pytest.mark.asyncio
    async def test_export_papers_without_pdfs(
        self, mock_extract, mock_download, mock_client_class, temp_dir
    ):
        """Test export_papers functionality without PDF download."""
        # Setup mocks
        mock_client = Mock()
        mock_papers = [
            Mock(
                id="paper1",
                title="Test Paper",
                authors=["Alice"],
                abstract="Test abstract",
                venue="ICLR.cc/2024",
            )
        ]
        mock_client.get_conference_papers.return_value = mock_papers
        mock_client.search_papers.return_value = {
            "paper1": {
                "title": "Test Paper",
                "authors": ["Alice"],
                "abstract": "Test abstract",
                "venue": "ICLR.cc/2024",
                "match_score": 0.9,
                "matched_terms": ["test"],
                "matches": {"title": ["test"]},
            }
        }
        mock_client_class.return_value = mock_client

        # Test arguments
        arguments = {
            "query": "test",
            "venues": [{"venue": "ICLR.cc", "year": "2024"}],
            "export_dir": temp_dir,
            "filename": "test_export",
            "download_pdfs": False,
            "max_papers": 2,
        }

        # Execute test
        result = await handle_export_papers(arguments)

        # Verify results
        assert len(result) == 1
        response_text = result[0].text
        assert "Export completed successfully!" in response_text
        assert "Papers exported: 1 (limited to top 2)" in response_text
        assert "PDFs downloaded: No" in response_text

        # Check files were created
        json_file = os.path.join(temp_dir, "test_export.json")
        summary_file = os.path.join(temp_dir, "test_export_summary.json")
        assert os.path.exists(json_file)
        assert os.path.exists(summary_file)

        # Verify JSON content
        with open(json_file, "r") as f:
            data = json.load(f)
        assert data["query"] == "test"
        assert len(data["papers"]) == 1
        assert data["papers"][0]["title"] == "Test Paper"

    @patch("openreview_mcp_server.tools.export_papers.OpenReviewClient")
    @patch("openreview_mcp_server.tools.export_papers.download_pdf")
    @patch("openreview_mcp_server.tools.export_papers.extract_up_to_references")
    @pytest.mark.asyncio
    async def test_export_papers_with_pdfs(
        self, mock_extract, mock_download, mock_client_class, temp_dir
    ):
        """Test export_papers functionality with PDF download."""
        # Setup mocks
        mock_client = Mock()
        mock_papers = [
            Mock(
                id="paper1",
                title="Test Paper",
                authors=["Alice"],
                abstract="Test abstract",
                venue="ICLR.cc/2024",
            )
        ]
        mock_client.get_conference_papers.return_value = mock_papers
        mock_client.search_papers.return_value = {
            "paper1": {
                "title": "Test Paper",
                "authors": ["Alice"],
                "abstract": "Test abstract",
                "venue": "ICLR.cc/2024",
                "match_score": 0.9,
                "matched_terms": ["test"],
                "matches": {"title": ["test"]},
            }
        }
        mock_client_class.return_value = mock_client

        # Mock PDF processing
        pdf_path = os.path.join(temp_dir, "paper1.pdf")
        mock_download.return_value = pdf_path
        mock_extract.return_value = (
            "Extracted text content from the paper up to references."
        )

        # Create a fake PDF file
        with open(pdf_path, "wb") as f:
            f.write(b"fake pdf content")

        # Test arguments
        arguments = {
            "query": "test",
            "venues": [{"venue": "ICLR.cc", "year": "2024"}],
            "export_dir": temp_dir,
            "filename": "test_export_pdfs",
            "download_pdfs": True,
            "max_papers": 1,
        }

        # Execute test
        result = await handle_export_papers(arguments)

        # Verify results
        assert len(result) == 1
        response_text = result[0].text
        assert "Export completed successfully!" in response_text
        assert "PDFs downloaded: Yes" in response_text
        assert "PDF: paper1.pdf" in response_text
        assert "Text: paper1_text.json" in response_text

        # Verify PDF processing was called
        mock_download.assert_called_once_with("paper1", temp_dir)
        mock_extract.assert_called_once_with(pdf_path)

        # Check text extraction file was created
        text_file = os.path.join(temp_dir, "paper1_text.json")
        assert os.path.exists(text_file)

        with open(text_file, "r") as f:
            text_data = json.load(f)
        assert text_data["paper_id"] == "paper1"
        assert (
            text_data["extracted_text"]
            == "Extracted text content from the paper up to references."
        )

    @pytest.mark.asyncio
    async def test_export_papers_missing_query(self):
        """Test export_papers with missing query."""
        arguments = {"venues": [{"venue": "ICLR.cc", "year": "2024"}]}

        result = await handle_export_papers(arguments)

        assert len(result) == 1
        response_text = result[0].text
        assert "Error: Search query is required" in response_text

    @pytest.mark.asyncio
    async def test_export_papers_missing_venues(self):
        """Test export_papers with missing venues."""
        arguments = {"query": "test"}

        result = await handle_export_papers(arguments)

        assert len(result) == 1
        response_text = result[0].text
        assert "Error: At least one venue must be specified" in response_text


if __name__ == "__main__":
    pytest.main([__file__])
