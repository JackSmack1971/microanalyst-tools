"""
Unit tests for CoinGecko API client.

Following London (Mockist) TDD approach:
- Mock external HTTP dependencies
- Test error handling and retry logic
- Verify rate limiting behavior
- Test API response parsing
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import requests
from src.microanalyst.providers.coingecko import CoinGeckoClient


class TestCoinGeckoClientInitialization:
    """Tests for CoinGecko client initialization."""
    
    def test_client_initializes_with_defaults(self):
        """Test client creates session and sets rate limit."""
        client = CoinGeckoClient()
        
        assert client.session is not None
        assert isinstance(client.session, requests.Session)
        assert client.request_interval == 6.0
        assert client.last_request_time == 0


class TestCoinGeckoRateLimiting:
    """Tests for rate limiting behavior."""
    
    def test_rate_limit_enforced_between_requests(self):
        """Test that client waits between consecutive requests."""
        client = CoinGeckoClient()
        
        # Mock the actual HTTP request
        with patch.object(client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"id": "bitcoin"}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            # First request
            start_time = time.time()
            client._request("coins/bitcoin")
            
            # Second request should be delayed
            client._request("coins/ethereum")
            elapsed = time.time() - start_time
            
            # Should have waited at least request_interval seconds
            assert elapsed >= client.request_interval
    
    def test_rate_limit_reset_after_wait(self):
        """Test that rate limit properly tracks time."""
        client = CoinGeckoClient()
        client.request_interval = 0.1  # Short interval for testing
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            client._request("test")
            initial_time = client.last_request_time
            
            time.sleep(0.15)  # Wait longer than interval
            client._request("test2")
            
            assert client.last_request_time > initial_time


class TestCoinGeckoRequestMethod:
    """Tests for internal _request method."""
    
    def test_request_returns_json_on_success(self):
        """Test successful request returns parsed JSON."""
        client = CoinGeckoClient()
        expected_data = {"id": "bitcoin", "symbol": "btc"}
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = expected_data
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            result = client._request("coins/bitcoin")
            
            assert result == expected_data
            mock_get.assert_called_once()
    
    def test_request_handles_timeout(self):
        """Test request handles timeout gracefully."""
        client = CoinGeckoClient()
        
        with patch.object(client.session, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()
            
            result = client._request("coins/bitcoin")
            
            assert result is None
    
    def test_request_handles_http_error(self):
        """Test request handles HTTP errors."""
        client = CoinGeckoClient()
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
            mock_get.return_value = mock_response
            
            result = client._request("coins/invalid")
            
            assert result is None
    
    @patch('src.microanalyst.providers.coingecko.time.sleep')  # Patch at module level
    def test_request_retries_on_429(self, mock_sleep):
        """Test that 429 rate limit triggers retry after wait."""
        client = CoinGeckoClient()
        
        with patch.object(client.session, 'get') as mock_get:
            # First call returns 429, second succeeds
            mock_429 = Mock()
            mock_429.status_code = 429
            mock_429.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_429)
            
            mock_success = Mock()
            mock_success.json.return_value = {"success": True}
            mock_success.raise_for_status = Mock()
            
            mock_get.side_effect = [mock_429, mock_success]
            
            result = client._request("coins/bitcoin")
            
            assert result == {"success": True}
            assert mock_get.call_count == 2
            # Should sleep for 60s retry plus _wait_for_rate_limit calls
            assert mock_sleep.call_count >= 1


class TestCoinGeckoGetTokenData:
    """Tests for get_token_data method."""
    
    def test_get_token_data_returns_parsed_response(self):
        """Test get_token_data returns market data."""
        client = CoinGeckoClient()
        expected_data = {
            "id": "bitcoin",
            "symbol": "btc",
            "market_data": {
                "current_price": {"usd": 50000}
            }
        }
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = expected_data
            
            result = client.get_token_data("bitcoin")
            
            assert result == expected_data
            mock_request.assert_called_once()
            # Verify endpoint called
            args = mock_request.call_args[0]
            assert "coins/bitcoin" in args[0]
    
    def test_get_token_data_passes_correct_params(self):
        """Test that correct parameters are passed to API."""
        client = CoinGeckoClient()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {}
            
            client.get_token_data("ethereum")
            
            # Check that endpoint is correct
            args = mock_request.call_args[0]
            assert "coins/ethereum" in args[0]
            # Params are passed as second positional arg
            if len(args) > 1:
                params = args[1]
                assert params.get("localization") == "false"
                assert params.get("market_data") == "true"


class TestCoinGeckoGetMarketChart:
    """Tests for get_market_chart method."""
    
    def test_get_market_chart_returns_ohlcv_data(self):
        """Test get_market_chart returns historical data."""
        client = CoinGeckoClient()
        expected_data = {
            "prices": [[1000, 50000], [2000, 51000]],
            "total_volumes": [[1000, 1000000], [2000, 1100000]]
        }
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = expected_data
            
            result = client.get_market_chart("bitcoin", days="30")
            
            assert result == expected_data
            mock_request.assert_called_once()
    
    def test_get_market_chart_uses_default_days(self):
        """Test default parameter for days."""
        client = CoinGeckoClient()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {}
            
            client.get_market_chart("bitcoin")
            
            args = mock_request.call_args[0]
            if len(args) > 1:
                params = args[1]
                assert params.get("days") == "30"
                assert params.get("vs_currency") == "usd"


class TestCoinGeckoGetSimplePrice:
    """Tests for get_simple_price method."""
    
    def test_get_simple_price_returns_price_data(self):
        """Test get_simple_price returns current prices."""
        client = CoinGeckoClient()
        expected_data = {
            "bitcoin": {"usd": 50000, "usd_market_cap": 1000000000},
            "ethereum": {"usd": 3000, "usd_market_cap": 400000000}
        }
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = expected_data
            
            result = client.get_simple_price(["bitcoin", "ethereum"])
            
            assert result == expected_data
    
    def test_get_simple_price_joins_multiple_ids(self):
        """Test that multiple token IDs are properly formatted."""
        client = CoinGeckoClient()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {}
            
            client.get_simple_price(["bitcoin", "ethereum", "solana"])
            
            args = mock_request.call_args[0]
            if len(args) > 1:
                params = args[1]
                assert "bitcoin,ethereum,solana" in params.get("ids", "")


class TestCoinGeckoIntegration:
    """Integration tests for complete workflows."""
    
    @patch('time.sleep')
    def test_multiple_requests_respect_rate_limit(self, mock_sleep):
        """Integration: Multiple requests properly rate limited."""
        client = CoinGeckoClient()
        client.request_interval = 0.1  # Fast for testing
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            # Make 3 requests
            client.get_token_data("bitcoin")
            client.get_market_chart("ethereum")
            client.get_simple_price(["solana"])
            
            # Should have made 3 API calls
            assert mock_get.call_count == 3
