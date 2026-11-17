"""Tests for web_search and safe_web_search_wrapper in agent/tools.py."""
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.modules.setdefault("wmi", MagicMock())

from agent.schema import WebSearchInput
from agent.tools import web_search, safe_web_search_wrapper, tools


class TestWebSearchCore:
    """Unit tests for web_search and safe_web_search_wrapper."""

    def test_web_search_wrapper_pydantic_input(self):
        fake_results = [{"title": "Test Title", "content": "Test snippet", "url": "https://example.com"}]
        with patch("agent.tools.web_search", return_value=fake_results) as mock_ws:
            res = safe_web_search_wrapper(WebSearchInput(query="Python 3.12"))
        mock_ws.assert_called_once_with("Python 3.12")
        assert res == fake_results

    def test_web_search_wrapper_dict_input(self):
        fake_results = [{"title": "Search Result"}]
        with patch("agent.tools.web_search", return_value=fake_results) as mock_ws:
            res = safe_web_search_wrapper({"query": "AI news"})
        mock_ws.assert_called_once_with("AI news")
        assert res == fake_results

    def test_web_search_wrapper_string_fallback(self):
        fake_results = [{"title": "Fallback Result"}]
        with patch("agent.tools.web_search", return_value=fake_results) as mock_ws:
            res = safe_web_search_wrapper("Windows 11 updates")
        mock_ws.assert_called_once_with("Windows 11 updates")
        assert res == fake_results

    def test_web_search_tool_registered(self):
        tool = next((t for t in tools if t.name == "WebSearch"), None)
        assert tool is not None
        assert tool.name == "WebSearch"
        assert tool.args_schema == WebSearchInput

    def test_web_search_tool_invokable_with_dict(self):
        fake_results = [{"title": "LangChain", "url": "https://langchain.com"}]
        tool = next((t for t in tools if t.name == "WebSearch"), None)
        with patch("agent.tools.web_search", return_value=fake_results):
            res = tool.invoke({"query": "LangChain tutorial"})
        assert res == fake_results

    def test_web_search_exception_propagates_to_caller(self):
        """Documents that web_search lacks an internal try/except, bubbling errors to ToolNode."""
        with patch("agent.tools.TavilySearchResults.invoke", side_effect=Exception("API key expired")):
            with pytest.raises(Exception) as exc_info:
                web_search("test query")
            assert "API key expired" in str(exc_info.value)
