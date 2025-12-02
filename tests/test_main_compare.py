"""
Integration tests for comparison mode.
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import pandas as pd
from rich.table import Table
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
    
    # Mock compare_tokens to return tuple
    with patch("src.microanalyst.main.compare_tokens") as mock_compare:
        mock_compare.return_value = (pd.DataFrame(), pd.DataFrame())
        
        with patch.object(sys, "argv", test_args), \
             patch("src.microanalyst.main.console", rich_console):
            main()
        
    output = rich_console.file.getvalue()
    assert "Comparing" in output
    assert "2 tokens" in output or "2" in output

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
    
    # Mock compare_tokens to return valid dataframes
    with patch("src.microanalyst.main.compare_tokens") as mock_compare:
        metrics_df = pd.DataFrame([{"Symbol": "BTC"}, {"Symbol": "ETH"}, {"Symbol": "SOL"}])
        corr_df = pd.DataFrame()
        mock_compare.return_value = (metrics_df, corr_df)
        
        with patch.object(sys, "argv", test_args), \
             patch("src.microanalyst.main.console", rich_console):
            main()
        
    # Check that search was called for each token
    assert cg.search.call_count == 3
    
    output = rich_console.file.getvalue()
    from rich.text import Text
    plain_output = Text.from_ansi(output).plain
    
    # Debug
    # print(f"PLAIN OUTPUT:\n{plain_output}")
    
    assert "BTC" in plain_output
    assert "ETH" in plain_output
    # Title might be wrapped, so check parts or use loose match
    assert "Token" in plain_output
    assert "Comparison" in plain_output
    assert "Matrix" in plain_output
