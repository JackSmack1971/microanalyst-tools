import pytest
from unittest.mock import patch, MagicMock
from src.microanalyst.main import main
from src.cli.theme import generate_error_panel

@patch("src.microanalyst.main.CoinGeckoClient")
@patch("src.microanalyst.main.BinanceClient")
@patch("src.microanalyst.main.console")
@patch("sys.argv", ["main.py", "invalid_token"])
def test_main_token_not_found(mock_console, mock_binance, mock_cg):
    """
    Test that main() prints an error panel when token is not found.
    """
    # Mock CoinGecko search returning empty
    mock_cg_instance = mock_cg.return_value
    mock_cg_instance._request.return_value = {"coins": []}
    
    main()
    
    # Verify console.print was called
    assert mock_console.print.called
    
    # Verify it was called with a Panel (we can check args or just that it was called)
    # Ideally we check if generate_error_panel was used, but that returns a Panel object.
    # We can check if the first arg to print is a Panel.
    args, _ = mock_console.print.call_args
    from rich.panel import Panel
    assert isinstance(args[0], Panel)
    assert "Token Not Found" in args[0].title

@patch("src.microanalyst.main.CoinGeckoClient")
@patch("src.microanalyst.main.BinanceClient")
@patch("src.microanalyst.main.console")
@patch("sys.argv", ["main.py", "btc"])
def test_main_success(mock_console, mock_binance, mock_cg):
    """
    Test successful execution path.
    """
    # Mock CoinGecko success
    mock_cg_instance = mock_cg.return_value
    mock_cg_instance._request.return_value = {
        "coins": [{"id": "bitcoin", "symbol": "btc"}]
    }
    mock_cg_instance.get_token_data.return_value = {
        "market_data": {"market_cap": {"usd": 100}},
        "market_cap_rank": 1
    }
    mock_cg_instance.get_market_chart.return_value = {
        "prices": [[1, 100], [2, 101]],
        "total_volumes": [[1, 1000], [2, 1000]]
    }
    
    # Mock Binance success
    mock_binance_instance = mock_binance.return_value
    mock_binance_instance.get_ticker_24h.return_value = {"quoteVolume": 1000}
    mock_binance_instance.get_depth.return_value = {"bids": [], "asks": []}
    
    main()
    
    # Verify console.print was called for report
    assert mock_console.print.called
    # Check that we didn't print an error panel
    # The last call should be the report (Markdown)
    args, _ = mock_console.print.call_args
    from rich.markdown import Markdown
    assert isinstance(args[0], Markdown)
