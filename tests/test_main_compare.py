import pytest
from unittest.mock import MagicMock, patch
import sys
from src.microanalyst.main import main

@pytest.fixture
def mock_clients():
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
            "prices": [[1000, 100.0], [2000, 101.0]],
            "total_volumes": [[1000, 50000.0], [2000, 51000.0]]
        }
        
import pytest
from unittest.mock import MagicMock, patch
import sys
from src.microanalyst.main import main

@pytest.fixture
def mock_clients():
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
            "prices": [[1000, 100.0], [2000, 101.0]],
            "total_volumes": [[1000, 50000.0], [2000, 51000.0]]
        }
        
        # Mock Binance
        bin_instance.get_ticker_24h.return_value = {"quoteVolume": "50000.0"}
        bin_instance.get_depth.return_value = {"bids": [], "asks": []}
        
        yield cg_instance, bin_instance

def test_compare_arg_parsing(mock_clients, rich_console):
    """Test that --compare triggers comparison logic."""
    test_args = ["microanalyst", "--compare", "btc,eth"]
    with patch.object(sys, "argv", test_args), \
         patch("src.microanalyst.main.console", rich_console):
        main()
        
    output = rich_console.file.getvalue()
    assert "Comparing" in output
    assert "2 tokens" in output or "2" in output # "2" might be styled separately
    assert "Token Comparison Matrix" in output

def test_compare_validation_min(mock_clients, rich_console):
    """Test validation for minimum tokens."""
    test_args = ["microanalyst", "--compare", "btc"]
    with patch.object(sys, "argv", test_args), \
         patch("src.microanalyst.main.console", rich_console):
        main()
        
    output = rich_console.file.getvalue()
    assert "Comparison requires at least 2 tokens" in output

def test_compare_validation_max(mock_clients, rich_console):
    """Test validation for maximum tokens."""
    tokens = ",".join(["t"] * 11)
    test_args = ["microanalyst", "--compare", tokens]
    with patch.object(sys, "argv", test_args), \
         patch("src.microanalyst.main.console", rich_console):
        main()
        
    output = rich_console.file.getvalue()
    assert "Comparison limited to 10 tokens max" in output

def test_compare_execution(mock_clients, rich_console):
    """Test full execution flow."""
    cg, _ = mock_clients
    test_args = ["microanalyst", "--compare", "btc,eth,sol"]
    with patch.object(sys, "argv", test_args), \
         patch("src.microanalyst.main.console", rich_console):
        main()
        
    # Check that search was called for each token
    assert cg.search.call_count == 3
    
    # Check that get_token_data was called for each
    assert cg.get_token_data.call_count == 3
    
    output = rich_console.file.getvalue()
    assert "Token Comparison Matrix" in output
