import pytest
from unittest.mock import MagicMock, patch
import sys
from src.microanalyst.main import main

@pytest.fixture
def mock_clients_charts():
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
        
        # Mock market chart with timestamps (ms)
        # 3 days of data
        cg_instance.get_market_chart.return_value = {
            "prices": [
                [1672531200000, 100.0], # 2023-01-01
                [1672617600000, 105.0], # 2023-01-02
                [1672704000000, 102.0]  # 2023-01-03
            ],
            "total_volumes": [
                [1672531200000, 50000.0],
                [1672617600000, 60000.0],
                [1672704000000, 55000.0]
            ]
        }
        
        # Mock Binance
        bin_instance.get_ticker_24h.return_value = {"quoteVolume": "50000.0"}
        bin_instance.get_depth.return_value = {"bids": [], "asks": []}
        
        yield cg_instance, bin_instance

def test_charts_flag(mock_clients_charts, rich_console):
    """Test that --charts triggers chart generation."""
    test_args = ["microanalyst", "btc", "--charts"]
    
    # Mock chart generation to avoid actual plotext logic during this integration test
    # (though plotext is fast, we want to verify calls)
    with patch.object(sys, "argv", test_args), \
         patch("src.microanalyst.main.console", rich_console), \
         patch("src.microanalyst.main.generate_price_chart") as mock_p_chart, \
         patch("src.microanalyst.main.generate_volume_chart") as mock_v_chart:
        
        mock_p_chart.return_value = "Mock Price Chart"
        mock_v_chart.return_value = "Mock Volume Chart"
        
        main()
        
        assert mock_p_chart.called
        assert mock_v_chart.called
        
        output = rich_console.file.getvalue()
        assert "Generating Charts" in output
        assert "Mock Price Chart" in output
        assert "Mock Volume Chart" in output

def test_no_charts_flag(mock_clients_charts, rich_console):
    """Test that absence of --charts does not trigger generation."""
    test_args = ["microanalyst", "btc"]
    
    with patch.object(sys, "argv", test_args), \
         patch("src.microanalyst.main.console", rich_console), \
         patch("src.microanalyst.main.generate_price_chart") as mock_p_chart:
        
        main()
        
        assert not mock_p_chart.called
        output = rich_console.file.getvalue()
        assert "Generating Charts" not in output

def test_charts_comparison(mock_clients_charts, rich_console):
    """Test charts in comparison mode."""
    test_args = ["microanalyst", "--compare", "btc,eth", "--charts"]
    
    with patch.object(sys, "argv", test_args), \
         patch("src.microanalyst.main.console", rich_console), \
         patch("src.microanalyst.main.generate_price_chart") as mock_p_chart:
        
        mock_p_chart.return_value = "Mock Chart"
        
        main()
        
        # Should be called for each token (2 tokens)
        assert mock_p_chart.call_count == 2
        
        output = rich_console.file.getvalue()
        assert "Generating Charts" in output
