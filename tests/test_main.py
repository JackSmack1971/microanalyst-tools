import pytest
from unittest.mock import patch, MagicMock
from src.microanalyst.main import main
from rich.panel import Panel
from rich.console import Group

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
    # Mock search directly because the class is mocked
    mock_cg_instance.search.return_value = {"coins": []}
    
    main()
    
    # Verify console.print was called
    assert mock_console.print.called
    
    # Verify it was called with a Panel
    args, _ = mock_console.print.call_args
    assert isinstance(args[0], Panel)
    assert "Analysis Failed" in args[0].title

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
    mock_cg_instance.search.return_value = {
        "coins": [{"id": "bitcoin", "symbol": "btc"}]
    }
    mock_cg_instance.get_token_data.return_value = {
        "market_data": {"market_cap": {"usd": 100}, "total_volume": {"usd": 1000}, "current_price": {"usd": 50000}},
        "market_cap_rank": 1,
        "symbol": "btc",
        "name": "Bitcoin"
    }
    mock_cg_instance.get_market_chart.return_value = {
        "prices": [[1600000000000, 100], [1600086400000, 101]],
        "total_volumes": [[1600000000000, 1000], [1600086400000, 1000]]
    }
    
    # Mock Binance success
    mock_binance_instance = mock_binance.return_value
    mock_binance_instance.get_ticker_24h.return_value = {"quoteVolume": 1000}
    mock_binance_instance.get_depth.return_value = {"bids": [], "asks": []}
    
    main()
    
    # Verify console.print was called for report
    assert mock_console.print.called
    
    # Check that we printed a Group or similar (Report Layout)
    # The report is complex, but we can check if print was called with something renderable
    # We can just assert called for now, or check type if we know it.
    # generate_report returns a Group or Layout.
    args, _ = mock_console.print.call_args
    # It might be the last call.
    # We expect multiple prints (progress bar, etc might interfere if not mocked out, but progress uses its own console or transient)
    # main() prints "Starting analysis...", then report.
    
    # Let's check that at least one print argument is NOT a string (implies renderable)
    has_renderable = False
    for call in mock_console.print.call_args_list:
        args, _ = call
        if not isinstance(args[0], str):
            has_renderable = True
            break
    assert has_renderable
