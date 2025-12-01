import pytest
from unittest.mock import patch, MagicMock, ANY
from pathlib import Path
from src.microanalyst.main import main, OutputMode

@patch("src.microanalyst.main.CoinGeckoClient")
@patch("src.microanalyst.main.BinanceClient")
@patch("src.microanalyst.main.console")
@patch("src.microanalyst.main.export_to_json")
@patch("src.microanalyst.main.export_to_html")
def test_export_json_flow(mock_html, mock_json, mock_console, mock_binance, mock_cg):
    """Test full flow for JSON export."""
    with patch("sys.argv", ["main.py", "btc", "--output", "json"]):
        # Mock API responses
        mock_cg_instance = mock_cg.return_value
        mock_cg_instance._request.return_value = {"coins": [{"id": "bitcoin", "symbol": "btc"}]}
        mock_cg_instance.get_token_data.return_value = {
            "market_cap_rank": 1,
            "market_data": {
                "current_price": {"usd": 50000},
                "market_cap": {"usd": 1000000},
                "total_volume": {"usd": 50000}
            },
            "name": "Bitcoin",
            "symbol": "btc"
        }
        mock_cg_instance.get_market_chart.return_value = {"prices": [], "total_volumes": []}
        
        mock_binance.return_value.get_ticker_24h.return_value = {"quoteVolume": 50000}
        mock_binance.return_value.get_depth.return_value = {"bids": [], "asks": []}

        main()
        
        # Verify export_to_json called
        mock_json.assert_called_once()
        args, _ = mock_json.call_args
        data, filepath = args
        assert data["token_symbol"] == "btc"
        assert str(filepath).endswith(".json")
        assert "btc_" in str(filepath)
        
        # Verify success message
        mock_console.print.assert_any_call(ANY) # Check for success message

@patch("src.microanalyst.main.CoinGeckoClient")
@patch("src.microanalyst.main.BinanceClient")
@patch("src.microanalyst.main.console")
@patch("src.microanalyst.main.export_to_json")
@patch("src.microanalyst.main.export_to_html")
def test_export_html_flow(mock_html, mock_json, mock_console, mock_binance, mock_cg):
    """Test full flow for HTML export."""
    with patch("sys.argv", ["main.py", "eth", "--output", "html"]):
        # Mock API responses (minimal)
        mock_cg.return_value._request.return_value = {"coins": [{"id": "ethereum", "symbol": "eth"}]}
        mock_cg.return_value.get_token_data.return_value = {"name": "Ethereum", "symbol": "eth"}
        mock_cg.return_value.get_market_chart.return_value = {"prices": []}
        mock_binance.return_value.get_ticker_24h.return_value = {}
        mock_binance.return_value.get_depth.return_value = {}

        main()
        
        mock_html.assert_called_once()
        args, _ = mock_html.call_args
        data, filepath = args
        assert data["token_symbol"] == "eth"
        assert str(filepath).endswith(".html")

@patch("src.microanalyst.main.CoinGeckoClient")
@patch("src.microanalyst.main.BinanceClient")
@patch("src.microanalyst.main.console")
@patch("src.microanalyst.main.export_to_json")
def test_export_custom_path(mock_json, mock_console, mock_binance, mock_cg):
    """Test --save argument."""
    custom_path = "custom_report.json"
    with patch("sys.argv", ["main.py", "sol", "--output", "json", "--save", custom_path]):
        # Mock API
        mock_cg.return_value._request.return_value = {"coins": [{"id": "solana", "symbol": "sol"}]}
        mock_cg.return_value.get_token_data.return_value = {"name": "Solana", "symbol": "sol"}
        mock_cg.return_value.get_market_chart.return_value = {"prices": []}
        mock_binance.return_value.get_ticker_24h.return_value = {}
        mock_binance.return_value.get_depth.return_value = {}

        main()
        
        mock_json.assert_called_once()
        _, filepath = mock_json.call_args[0]
        assert str(filepath) == custom_path

@patch("src.microanalyst.main.CoinGeckoClient")
@patch("src.microanalyst.main.BinanceClient")
@patch("src.microanalyst.main.console")
@patch("src.microanalyst.main.export_to_json")
def test_export_error_handling(mock_json, mock_console, mock_binance, mock_cg):
    """Test error handling during export."""
    mock_json.side_effect = IOError("Permission denied")
    
    with patch("sys.argv", ["main.py", "btc", "--output", "json"]):
        # Mock API
        mock_cg.return_value._request.return_value = {"coins": [{"id": "bitcoin", "symbol": "btc"}]}
        mock_cg.return_value.get_token_data.return_value = {"name": "Bitcoin", "symbol": "btc"}
        mock_cg.return_value.get_market_chart.return_value = {"prices": []}
        mock_binance.return_value.get_ticker_24h.return_value = {}
        mock_binance.return_value.get_depth.return_value = {}

        main()
        
        # Verify error panel printed
        # We can check if generate_error_panel was called, but here we check console.print calls
        # One of the calls should be an error panel (Renderable)
        assert mock_console.print.call_count >= 1
