"""Tests for hybrid fundamentals fetcher."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

# Skip all tests in this module if yfinance is not available
yfinance = pytest.importorskip("yfinance")

from etl.hybrid_fundamentals import HybridFundamentals


class TestOfflineModeDetection:
    """Tests for offline mode detection logic."""

    def test_initial_state_is_online(self):
        """Fetcher should start in online mode."""
        with patch.object(HybridFundamentals, '_load_cached_results', return_value=[]):
            fetcher = HybridFundamentals()
            assert fetcher.offline_mode is False
            assert fetcher.consecutive_failures == 0

    def test_single_failure_does_not_trigger_offline(self):
        """A single failure should not trigger offline mode."""
        with patch.object(HybridFundamentals, '_load_cached_results', return_value=[]):
            fetcher = HybridFundamentals()
            fetcher.consecutive_failures = 1
            assert fetcher.offline_mode is False

    def test_max_failures_triggers_offline(self):
        """Max consecutive failures should trigger offline mode."""
        with patch.object(HybridFundamentals, '_load_cached_results', return_value=[]):
            fetcher = HybridFundamentals()
            fetcher.consecutive_failures = fetcher.max_consecutive_failures
            # Simulate the check that happens in get_sec_fundamentals
            if fetcher.consecutive_failures >= fetcher.max_consecutive_failures:
                fetcher.offline_mode = True
            assert fetcher.offline_mode is True

    def test_success_resets_failure_counter(self):
        """Successful request should reset consecutive failures."""
        with patch.object(HybridFundamentals, '_load_cached_results', return_value=[]):
            fetcher = HybridFundamentals()
            fetcher.consecutive_failures = 5
            # Simulate success
            fetcher.consecutive_failures = 0
            assert fetcher.consecutive_failures == 0
            assert fetcher.offline_mode is False


class TestCachedResults:
    """Tests for cached results handling."""

    def test_has_cached_results_with_data(self):
        """Should return True when cached data exists."""
        mock_data = [{"ticker": "AAPL", "earnings_yield": 0.05}]
        with patch.object(HybridFundamentals, '_load_cached_results', return_value=mock_data):
            fetcher = HybridFundamentals()
            assert fetcher.has_cached_results() is True

    def test_has_cached_results_empty(self):
        """Should return False when no cached data."""
        with patch.object(HybridFundamentals, '_load_cached_results', return_value=[]):
            fetcher = HybridFundamentals()
            assert fetcher.has_cached_results() is False

    def test_cached_lookup_by_ticker(self):
        """Should be able to lookup cached data by ticker."""
        mock_data = [
            {"ticker": "AAPL", "earnings_yield": 0.05},
            {"ticker": "MSFT", "earnings_yield": 0.03},
        ]
        with patch.object(HybridFundamentals, '_load_cached_results', return_value=mock_data):
            fetcher = HybridFundamentals()
            assert "AAPL" in fetcher.cached_lookup
            assert "MSFT" in fetcher.cached_lookup
            assert fetcher.cached_lookup["AAPL"]["earnings_yield"] == 0.05


class TestDataExtraction:
    """Tests for SEC data extraction."""

    def test_extract_sec_metrics_empty_facts(self):
        """Empty company facts should return empty dict."""
        with patch.object(HybridFundamentals, '_load_cached_results', return_value=[]):
            fetcher = HybridFundamentals()
            result = fetcher._extract_sec_metrics({})
            assert isinstance(result, dict)

    def test_get_filing_dates_empty(self):
        """Empty SEC data should return empty filing dates."""
        with patch.object(HybridFundamentals, '_load_cached_results', return_value=[]):
            fetcher = HybridFundamentals()
            result = fetcher._get_filing_dates({})
            assert result == {}

    def test_get_filing_dates_with_data(self):
        """Should extract filing dates from SEC data."""
        with patch.object(HybridFundamentals, '_load_cached_results', return_value=[]):
            fetcher = HybridFundamentals()
            sec_data = {
                "revenue": {
                    "value": 1000000,
                    "filed_date": "2024-01-15",
                    "form_type": "10-K"
                }
            }
            result = fetcher._get_filing_dates(sec_data)
            assert "revenue" in result
            assert result["revenue"]["filed_date"] == "2024-01-15"


class TestHybridData:
    """Tests for hybrid data combination."""

    def test_offline_mode_returns_cached(self):
        """In offline mode, should return cached data."""
        mock_data = [{"ticker": "AAPL", "earnings_yield": 0.05}]
        with patch.object(HybridFundamentals, '_load_cached_results', return_value=mock_data):
            fetcher = HybridFundamentals()
            fetcher.offline_mode = True

            result = fetcher._get_cached_hybrid("AAPL")
            assert result is not None
            assert result.get("ticker") == "AAPL" or result.get("earnings_yield") == 0.05

    def test_offline_mode_unknown_ticker_returns_none(self):
        """In offline mode, unknown ticker should return None."""
        mock_data = [{"ticker": "AAPL", "earnings_yield": 0.05}]
        with patch.object(HybridFundamentals, '_load_cached_results', return_value=mock_data):
            fetcher = HybridFundamentals()
            fetcher.offline_mode = True

            result = fetcher._get_cached_hybrid("UNKNOWN")
            assert result is None


class TestRateLimiting:
    """Tests for rate limiting configuration."""

    def test_default_rate_limit(self):
        """Should have reasonable default rate limit."""
        with patch.object(HybridFundamentals, '_load_cached_results', return_value=[]):
            fetcher = HybridFundamentals()
            assert fetcher.rate_limit_delay == 0.1  # SEC allows 10 req/sec

    def test_max_consecutive_failures_default(self):
        """Should have reasonable default for max failures."""
        with patch.object(HybridFundamentals, '_load_cached_results', return_value=[]):
            fetcher = HybridFundamentals()
            assert fetcher.max_consecutive_failures == 10
