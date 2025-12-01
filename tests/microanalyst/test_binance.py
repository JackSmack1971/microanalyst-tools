"""
Unit tests for Binance API client.

Following London (Mockist) TDD approach:
- Mock external HTTP dependencies
- Test error handling and retry logic
- Test IP ban detection
- Test API response parsing
"""

import pytest
from unittest.mock import Mock, patch
import requests
from src.microanalyst.providers.binance import BinanceClient


class TestBinanceClientInitialization:
    """Tests for Binance client initialization."""
    
    def test_client_initializes_with_session(self):
        """Test client creates HTTP session."""
        client = BinanceClient()
        
        assert client.session is not None
        assert isinstance(client.session, requests.Session)


class TestBinanceRequestMethod:
    """Tests for internal _request method."""
    
    def test_request_returns_json_on_success(self):
        """Test successful request returns parsed JSON."""
        client = BinanceClient()
        expected_data = {"symbol": "BTCUSDT", "price": "50000.00"}
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = expected_data
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            result = client._request("ticker/24hr", {"symbol": "BTCUSDT"})
            
            assert result == expected_data
            mock_get.assert_called_once()
    
    def test_request_handles_timeout(self):
        """Test request handles timeout gracefully."""
        client = BinanceClient()
        
        with patch.object(client.session, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()
            
            result = client._request("ticker/24hr")
            
            assert result is None
    
    def test_request_handles_http_error(self):
        """Test request handles general HTTP errors."""
        client = BinanceClient()
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
            mock_get.return_value = mock_response
            
            result = client._request("ticker/24hr")
            
            assert result is None
    
    @patch('time.sleep')
    def test_request_retries_on_429_with_retry_after(self, mock_sleep):
        """Test 429 triggers retry with Retry-After header."""
        client = BinanceClient()
        
        with patch.object(client.session, 'get') as mock_get:
            # First call returns 429, second succeeds
            mock_429 = Mock()
            mock_429.status_code = 429
            mock_429.headers = {"Retry-After": "30"}
            mock_429.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_429)
            
            mock_success = Mock()
            mock_success.json.return_value = {"success": True}
            mock_success.raise_for_status = Mock()
            
            mock_get.side_effect = [mock_429, mock_success]
            
            result = client._request("ticker/24hr")
            
            assert result == {"success": True}
            assert mock_get.call_count == 2
            mock_sleep.assert_called_once_with(30)
    
    @patch('time.sleep')
    def test_request_retries_on_429_without_retry_after(self, mock_sleep):
        """Test 429 uses default wait if no Retry-After header."""
        client = BinanceClient()
        
        with patch.object(client.session, 'get') as mock_get:
            mock_429 = Mock()
            mock_429.status_code = 429
            mock_429.headers = {}
            mock_429.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_429)
            
            mock_success = Mock()
            mock_success.json.return_value = {}
            mock_success.raise_for_status = Mock()
            
            mock_get.side_effect = [mock_429, mock_success]
            
            client._request("ticker/24hr")
            
            mock_sleep.assert_called_once_with(60)  # Default
    
    def test_request_raises_on_418_ip_ban(self):
        """Test 418 (IP ban) raises exception."""
        client = BinanceClient()
        
        with patch.object(client.session, 'get') as mock_get:
            mock_418 = Mock()
            mock_418.status_code = 418
            error = requests.exceptions.HTTPError(response=mock_418)
            mock_418.raise_for_status.side_effect = error
            mock_get.return_value = mock_418
            
            with pytest.raises(requests.exceptions.HTTPError):
                client._request("ticker/24hr")


class TestBinanceGetTicker24h:
    """Tests for get_ticker_24h method."""
    
    def test_get_ticker_returns_24h_stats(self):
        """Test get_ticker_24h returns price statistics."""
        client = BinanceClient()
        expected_data = {
            "symbol": "BTCUSDT",
            "priceChange": "1000.00",
            "priceChangePercent": "2.00",
            "volume": "50000",
            "quoteVolume": "2500000000"
        }
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = expected_data
            
            result = client.get_ticker_24h("BTCUSDT")
            
            assert result == expected_data
            mock_request.assert_called_once_with("ticker/24hr", {"symbol": "BTCUSDT"})
    
    def test_get_ticker_uppercases_symbol(self):
        """Test symbol is uppercased automatically."""
        client = BinanceClient()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {}
            
            client.get_ticker_24h("btcusdt")
            
            args = mock_request.call_args[0]
            if len(args) > 1:
                params = args[1]
                assert params["symbol"] == "BTCUSDT"


class TestBinanceGetDepth:
    """Tests for get_depth method."""
    
    def test_get_depth_returns_orderbook(self):
        """Test get_depth returns bids and asks."""
        client = BinanceClient()
        expected_data = {
            "bids": [["50000.00", "1.5"], ["49999.00", "2.0"]],
            "asks": [["50001.00", "1.2"], ["50002.00", "1.8"]]
        }
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = expected_data
            
            result = client.get_depth("BTCUSDT")
            
            assert result == expected_data
            assert "bids" in result
            assert "asks" in result
    
    def test_get_depth_uses_default_limit(self):
        """Test default limit is 100."""
        client = BinanceClient()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {"bids": [], "asks": []}
            
            client.get_depth("BTCUSDT")
            
            args = mock_request.call_args[0]
            if len(args) > 1:
                params = args[1]
                assert params["limit"] == 100
    
    def test_get_depth_accepts_custom_limit(self):
        """Test custom limit parameter."""
        client = BinanceClient()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {}
            
            client.get_depth("ETHUSDT", limit=500)
            
            args = mock_request.call_args[0]
            if len(args) > 1:
                params = args[1]
                assert params["limit"] == 500


class TestBinanceGetKlines:
    """Tests for get_klines method."""
    
    def test_get_klines_returns_candlestick_data(self):
        """Test get_klines returns OHLCV data."""
        client = BinanceClient()
        expected_data = [
            [1640000000, "50000", "51000", "49500", "50500", "100"],
            [1640001000, "50500", "52000", "50000", "51500", "150"]
        ]
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = expected_data
            
            result = client.get_klines("BTCUSDT", interval="1h", limit=100)
            
            assert result == expected_data
            assert isinstance(result, list)
    
    def test_get_klines_uses_default_parameters(self):
        """Test default interval and limit."""
        client = BinanceClient()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = []
            
            client.get_klines("SOLUSDT")
            
            # Access call args correctly
            args, kwargs = mock_request.call_args
            endpoint = args[0]
            params = args[1] if len(args) > 1 else kwargs.get('params', {})
            
            assert params["interval"] == "1h"
            assert params["limit"] == 500


class TestBinanceGetAggTrades:
    """Tests for get_agg_trades method."""
    
    def test_get_agg_trades_returns_trade_data(self):
        """Test get_agg_trades returns aggregate trades."""
        client = BinanceClient()
        expected_data = [
            {"a": 1, "p": "50000.00", "q": "0.5", "T": 1640000000},
            {"a": 2, "p": "50100.00", "q": "0.8", "T": 1640000100}
        ]
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = expected_data
            
            result = client.get_agg_trades("BTCUSDT", limit=100)
            
            assert result == expected_data
    
    def test_get_agg_trades_uses_default_limit(self):
        """Test default limit is 500."""
        client = BinanceClient()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = []
            
            client.get_agg_trades("ETHUSDT")
            
            args = mock_request.call_args[0]
            if len(args) > 1:
                params = args[1]
                assert params["limit"] == 500


class TestBinanceIntegration:
    """Integration tests for complete workflows."""
    
    def test_multiple_endpoints_work_together(self):
        """Integration: Multiple API calls in sequence."""
        client = BinanceClient()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.side_effect = [
                {"symbol": "BTCUSDT", "quoteVolume": "1000000"},  # ticker
                {"bids": [["50000", "1"]], "asks": [["50100", "1"]]},  # depth
                [[1, "50000", "51000", "49000", "50500", "100"]]  # klines
            ]
            
            ticker = client.get_ticker_24h("BTCUSDT")
            depth = client.get_depth("BTCUSDT")
            klines = client.get_klines("BTCUSDT")
            
            assert ticker is not None
            assert depth is not None
            assert klines is not None
            assert mock_request.call_count == 3
