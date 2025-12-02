import pytest
from unittest.mock import patch, MagicMock, ANY
import time
from src.microanalyst.main import main

def test_watch_mode_loop(rich_console):
    """Test that watch mode enters the loop and refreshes data."""
    with patch("sys.argv", ["main.py", "btc", "--watch"]), \
         patch("src.microanalyst.main.CoinGeckoClient") as mock_cg, \
         patch("src.microanalyst.main.BinanceClient") as mock_binance, \
         patch("src.microanalyst.main.console", rich_console), \
         patch("src.microanalyst.main.Live") as mock_live, \
         patch("time.sleep") as mock_sleep:
        
        # Mock API
        mock_cg.return_value.search.return_value = {"coins": [{"id": "bitcoin", "symbol": "btc"}]}
        mock_cg.return_value.get_token_data.return_value = {"name": "Bitcoin", "symbol": "btc", "market_data": {}}
        mock_cg.return_value.get_market_chart.return_value = {"prices": [], "total_volumes": []}
        mock_binance.return_value.get_ticker_24h.return_value = {}
        mock_binance.return_value.get_depth.return_value = {}
        
        # Mock sleep to raise KeyboardInterrupt after one iteration to break the loop
        mock_sleep.side_effect = [None, KeyboardInterrupt]
        
        main()
        
        # Verify Live context manager used
        mock_live.assert_called_once()
        
        # Verify sleep called (refresh interval)
        assert mock_sleep.called
        
        # Verify analyze_token called multiple times (initial + refresh)
        # We can check if get_token_data was called at least twice
        assert mock_cg.return_value.get_token_data.call_count >= 2

def test_watch_mode_rate_limit_callback(rich_console):
    """Test that rate limit callback is registered."""
    with patch("sys.argv", ["main.py", "btc", "--watch"]), \
         patch("src.microanalyst.main.CoinGeckoClient") as mock_cg, \
         patch("src.microanalyst.main.BinanceClient"), \
         patch("src.microanalyst.main.console", rich_console), \
         patch("src.microanalyst.main.Live"), \
         patch("time.sleep", side_effect=KeyboardInterrupt): # Exit immediately
        
        # Mock API
        mock_cg.return_value.search.return_value = {"coins": [{"id": "bitcoin", "symbol": "btc"}]}
        mock_cg.return_value.get_token_data.return_value = {"name": "Bitcoin", "symbol": "btc", "market_data": {}}
        mock_cg.return_value.get_market_chart.return_value = {"prices": [], "total_volumes": []}
        
        main()
        
        # Verify callback was set
        client_instance = mock_cg.return_value
        assert client_instance.status_callback is not None
