"""
Tests for OpenReview client functionality.
"""

import pytest
from unittest.mock import Mock, patch
from openreview_mcp_server.client import OpenReviewClient, Paper, Profile


class TestOpenReviewClient:
    """Test cases for OpenReviewClient."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = OpenReviewClient()
    
    def test_extract_value_dict(self):
        """Test _extract_value with dict input."""
        field = {"value": "test_value"}
        result = self.client._extract_value(field)
        assert result == "test_value"
    
    def test_extract_value_string(self):
        """Test _extract_value with string input."""
        field = "test_value"
        result = self.client._extract_value(field)
        assert result == "test_value"
    
    def test_normalize_text(self):
        """Test text normalization."""
        text = "Time Series Token-Merging! 123"
        result = self.client._normalize_text(text)
        assert result == "time series token merging  123"
    
    def test_extract_keywords(self):
        """Test keyword extraction."""
        text = "Neural Networks and Deep Learning"
        result = self.client._extract_keywords(text)
        expected = {"neural", "networks", "and", "deep", "learning"}
        assert result == expected
    
    def test_paper_to_dict(self):
        """Test Paper to dict conversion."""
        paper = Paper(
            id="test_id",
            title="Test Paper",
            authors=["Author 1", "Author 2"],
            abstract="Test abstract",
            venue="Test Venue"
        )
        result = self.client._paper_to_dict(paper)
        expected = {
            'title': "Test Paper",
            'authors': ["Author 1", "Author 2"],
            'abstract': "Test abstract",
            'venue': "Test Venue"
        }
        assert result == expected


class TestSearchFunctionality:
    """Test search functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = OpenReviewClient()
        self.test_submissions = {
            "paper1": {
                "title": "Neural Networks for Time Series",
                "authors": ["Alice", "Bob"],
                "abstract": "This paper presents neural networks for time series forecasting.",
                "venue": "ICLR.cc/2024"
            },
            "paper2": {
                "title": "Deep Learning Applications", 
                "authors": ["Charlie", "David"],
                "abstract": "Applications of deep learning in various domains.",
                "venue": "NeurIPS.cc/2024"
            }
        }
    
    def test_search_any_match(self):
        """Test search with 'any' match mode."""
        results = self.client._search_submissions_dict(
            self.test_submissions,
            "neural networks",
            match_mode="any"
        )
        
        assert len(results) == 2  # Both papers should match
        assert "paper1" in results
        assert "paper2" in results
    
    def test_search_all_match(self):
        """Test search with 'all' match mode."""
        results = self.client._search_submissions_dict(
            self.test_submissions,
            "neural time",
            match_mode="all"
        )
        
        assert len(results) == 1  # Only paper1 should match
        assert "paper1" in results
    
    def test_search_exact_match(self):
        """Test search with 'exact' match mode."""
        results = self.client._search_submissions_dict(
            self.test_submissions,
            "time series",
            match_mode="exact"
        )
        
        assert len(results) == 1  # Only paper1 should match
        assert "paper1" in results
    
    def test_search_no_results(self):
        """Test search with no matches."""
        results = self.client._search_submissions_dict(
            self.test_submissions,
            "quantum computing",
            match_mode="any"
        )
        
        assert len(results) == 0