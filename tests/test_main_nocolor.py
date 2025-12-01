import pytest
from unittest.mock import MagicMock, patch
import sys
import os
from src.microanalyst.main import main, console

@pytest.fixture
def mock_clients_nocolor():
    with patch("src.microanalyst.main.CoinGeckoClient") as MockCG, \
         patch("src.microanalyst.main.BinanceClient") as MockBin:
        
        cg_instance = MockCG.return_value
        bin_instance = MockBin.return_value
        
        # Mock search
        cg_instance.search.side_effect = lambda q: {"coins": [{"id": q, "symbol": q}]}
        
        # Mock token data
        cg_instance.get_token_data.return_value = {
            "name": "Test Token",
            "symbol": "test",
            "market_cap_rank": 1,
            "market_data": {
                "current_price": {"usd": 100.0},
                "market_cap": {"usd": 1000000.0},
                "total_volume": {"usd": 50000.0}
            }
        }
        
        # Mock market chart
        cg_instance.get_market_chart.return_value = {
            "prices": [[1000, 100.0]],
            "total_volumes": [[1000, 50000.0]]
        }
        
        # Mock Binance
        bin_instance.get_ticker_24h.return_value = {"quoteVolume": "50000.0"}
        bin_instance.get_depth.return_value = {"bids": [], "asks": []}
        
        yield cg_instance, bin_instance

def test_no_color_flag(mock_clients_nocolor, rich_console):
    """Test that --no-color disables console color."""
    test_args = ["microanalyst", "btc", "--no-color"]
    
    # We need to patch the global console in main to check if no_color gets set
    # But main.py imports console. We can check if main modifies it.
    # However, main() modifies the global console object.
    
    # Reset console state
    console.no_color = False
    
    with patch.object(sys, "argv", test_args), \
         patch("src.microanalyst.main.console", console): # Use real console object to check property change
        
        main()
        
        assert console.no_color is True

def test_no_color_env(mock_clients_nocolor):
    """Test that NO_COLOR env var disables console color."""
    test_args = ["microanalyst", "btc"]
    
    # Reset console state
    console.no_color = False
    
    with patch.object(sys, "argv", test_args), \
         patch.dict(os.environ, {"NO_COLOR": "1"}), \
         patch("src.microanalyst.main.console", console):
        
        main()
        
        assert console.no_color is True
