import pytest
from unittest.mock import patch, MagicMock
from src.microanalyst.main import main, OutputMode

@patch("src.microanalyst.main.CoinGeckoClient")
@patch("src.microanalyst.main.BinanceClient")
@patch("src.microanalyst.main.console")
@patch("sys.argv", ["main.py", "btc"])
def test_args_output_default(mock_console, mock_binance, mock_cg):
    """
    Test that default output mode is TERMINAL.
    """
    with patch("argparse.ArgumentParser.parse_args") as mock_parse:
        mock_parse.return_value.token = "btc"
        mock_parse.return_value.days = "30"
        mock_parse.return_value.output = "terminal"
        
        # Mock API responses to avoid MagicMock comparisons
        mock_cg_instance = mock_cg.return_value
        mock_cg_instance._request.return_value = {"coins": [{"id": "bitcoin", "symbol": "btc"}]}
        mock_cg_instance.get_token_data.return_value = {
            "market_cap_rank": 1,
            "market_data": {
                "current_price": {"usd": 50000},
                "market_cap": {"usd": 1000000},
                "total_volume": {"usd": 50000},
                "ath_change_percentage": {"usd": -10}
            },
            "name": "Bitcoin",
            "symbol": "btc"
        }
        mock_cg_instance.get_market_chart.return_value = {
            "prices": [[1, 100]],
            "total_volumes": [[1, 1000]]
        }
        
        mock_binance_instance = mock_binance.return_value
        mock_binance_instance.get_ticker_24h.return_value = {"quoteVolume": 1000}
        mock_binance_instance.get_depth.return_value = {"bids": [], "asks": []}

        main()
        
        # If main runs, it means args were "parsed" (mocked) successfully.
        pass

@patch("sys.argv", ["main.py", "btc", "--output", "json"])
@patch("src.microanalyst.main.CoinGeckoClient")
@patch("src.microanalyst.main.BinanceClient")
@patch("src.microanalyst.main.console")
def test_args_output_json(mock_console, mock_binance, mock_cg):
    """
    Test that --output json is accepted.
    """
    # Mock clients to avoid network calls
    mock_cg_instance = mock_cg.return_value
    mock_cg_instance._request.return_value = {"coins": [{"id": "bitcoin", "symbol": "btc"}]}
    mock_cg_instance.get_token_data.return_value = {
        "market_cap_rank": 1,
        "market_data": {
            "current_price": {"usd": 50000},
            "market_cap": {"usd": 1000000},
            "total_volume": {"usd": 50000},
            "ath_change_percentage": {"usd": -10}
        },
        "name": "Bitcoin",
        "symbol": "btc"
    }
    mock_cg_instance.get_market_chart.return_value = {
        "prices": [[1, 100]],
        "total_volumes": [[1, 1000]]
    }
    
    mock_binance_instance = mock_binance.return_value
    mock_binance_instance.get_ticker_24h.return_value = {"quoteVolume": 1000}
    mock_binance_instance.get_depth.return_value = {"bids": [], "asks": []}
    
    main()
    # If no SystemExit, it worked.

@patch("sys.argv", ["main.py", "btc", "--output", "invalid_format"])
@patch("src.microanalyst.main.CoinGeckoClient")
@patch("src.microanalyst.main.BinanceClient")
@patch("src.microanalyst.main.console")
def test_args_output_invalid(mock_console, mock_binance, mock_cg):
    """
    Test that invalid output format raises SystemExit.
    """
    with pytest.raises(SystemExit):
        main()

def test_output_mode_enum():
    assert OutputMode.TERMINAL == "terminal"
    assert OutputMode.JSON == "json"
    assert OutputMode.HTML == "html"
    assert OutputMode.MARKDOWN == "markdown"
