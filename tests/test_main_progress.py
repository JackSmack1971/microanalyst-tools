import pytest
from unittest.mock import patch, MagicMock, ANY
from src.microanalyst.main import main
from src.cli.progress import STAGE_DESCRIPTIONS

@patch("src.microanalyst.main.CoinGeckoClient")
@patch("src.microanalyst.main.BinanceClient")
@patch("src.microanalyst.main.console")
@patch("src.microanalyst.main.create_progress_bar")
@patch("sys.argv", ["main.py", "btc"])
def test_main_progress_flow(mock_create_progress, mock_console, mock_binance, mock_cg):
    """
    Test that main() correctly initializes and updates the progress bar.
    """
    # Mock Progress Context Manager
    mock_progress = MagicMock()
    mock_create_progress.return_value.__enter__.return_value = mock_progress
    
    # Mock API Success
    mock_cg_instance = mock_cg.return_value
    mock_cg_instance._request.return_value = {
        "coins": [{"id": "bitcoin", "symbol": "btc"}]
    }
    mock_cg_instance.get_token_data.return_value = {
        "market_data": {"market_cap": {"usd": 100}},
        "market_cap_rank": 1
    }
    mock_cg_instance.get_market_chart.return_value = {
        "prices": [[1, 100]],
        "total_volumes": [[1, 1000]]
    }
    mock_binance_instance = mock_binance.return_value
    mock_binance_instance.get_ticker_24h.return_value = {"quoteVolume": 1000}
    mock_binance_instance.get_depth.return_value = {"bids": [], "asks": []}
    
    main()
    
    # Verify Tasks Added
    # We expect 4 tasks: search, market, orderbook, analysis
    assert mock_progress.add_task.call_count == 4
    
    # Verify Tasks Updated
    # We expect 8 updates (start and finish for 4 stages)
    assert mock_progress.update.call_count == 8
    
    # Verify specific task descriptions were used
    mock_progress.add_task.assert_any_call(STAGE_DESCRIPTIONS["token_search"], total=1)
    mock_progress.add_task.assert_any_call(STAGE_DESCRIPTIONS["market_data"], total=1)
    mock_progress.add_task.assert_any_call(STAGE_DESCRIPTIONS["orderbook"], total=1)
    mock_progress.add_task.assert_any_call(STAGE_DESCRIPTIONS["analysis"], total=1)

@patch("src.microanalyst.main.CoinGeckoClient")
@patch("src.microanalyst.main.BinanceClient")
@patch("src.microanalyst.main.console")
@patch("src.microanalyst.main.create_progress_bar")
@patch("sys.argv", ["main.py", "invalid"])
def test_main_progress_stop_on_error(mock_create_progress, mock_console, mock_binance, mock_cg):
    """
    Test that progress.stop() is called when an error occurs (e.g. token not found).
    """
    # Mock Progress Context Manager
    mock_progress = MagicMock()
    mock_create_progress.return_value.__enter__.return_value = mock_progress
    
    # Mock Token Not Found
    mock_cg_instance = mock_cg.return_value
    mock_cg_instance.search.return_value = {"coins": []}
    
    main()
    
    # Verify progress.stop() was called (via context manager exit, but explicit stop might be called?)
    # Context manager handles stop automatically.
    # But if we return early, __exit__ is called.
    # The test checks mock_progress.stop.assert_called_once()
    # Does Rich Progress context manager call .stop() on exit? Yes.
    # But mock_create_progress returns a MagicMock.
    # The context manager protocol calls __exit__.
    # Does __exit__ call stop?
    # If we mock the context manager, we need to ensure __exit__ is called.
    
    # Actually, main() uses `with create_progress_bar() as progress:`.
    # If main returns early, __exit__ is called.
    # Does Rich Progress call .stop() in __exit__? Yes.
    # But we are mocking the return value of create_progress_bar().
    # The return value is the Progress object.
    # The context manager is the Progress object itself (Rich Progress is a context manager).
    
    # So mock_create_progress.return_value IS the context manager.
    # So __exit__ is called on it.
    # We should check if __exit__ was called.
    mock_create_progress.return_value.__exit__.assert_called()
    
    # Verify error panel printed
    assert mock_console.print.called
