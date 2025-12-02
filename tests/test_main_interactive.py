import pytest
from unittest.mock import patch, MagicMock, ANY
from src.microanalyst.main import main

@patch("src.microanalyst.main.CoinGeckoClient")
@patch("src.microanalyst.main.BinanceClient")
@patch("src.microanalyst.main.console")
@patch("src.microanalyst.main.prompt_token_selection")
@patch("questionary.text")
@patch("sys.stdout.isatty", return_value=True)
def test_interactive_no_token(mock_isatty, mock_text, mock_prompt, mock_console, mock_binance, mock_cg):
    """Test interactive mode when no token is provided."""
    with patch("sys.argv", ["main.py", "--interactive"]):
        # Mock user input for search
        mock_text.return_value.ask.return_value = "btc"
        
        # Mock API
        mock_cg.return_value._request.return_value = {"coins": [{"id": "bitcoin", "symbol": "btc"}]}
        mock_cg.return_value.get_token_data.return_value = {"name": "Bitcoin", "symbol": "btc"}
        mock_cg.return_value.get_market_chart.return_value = {"prices": []}
        mock_binance.return_value.get_ticker_24h.return_value = {}
        mock_binance.return_value.get_depth.return_value = {}
        
        # Mock selection
        mock_prompt.return_value = "bitcoin" # ID

        main()
        
        # Verify prompts called
        mock_text.assert_called_once()
        mock_prompt.assert_called_once()

@patch("src.microanalyst.main.CoinGeckoClient")
@patch("src.microanalyst.main.BinanceClient")
@patch("src.microanalyst.main.console")
@patch("src.microanalyst.main.prompt_token_selection")
@patch("sys.stdout.isatty", return_value=True)
def test_interactive_with_token(mock_isatty, mock_prompt, mock_console, mock_binance, mock_cg):
    """Test interactive mode when token is provided (skips search prompt, shows selection)."""
    with patch("sys.argv", ["main.py", "btc", "--interactive"]):
        # Mock API
        mock_cg.return_value._request.return_value = {"coins": [{"id": "bitcoin", "symbol": "btc"}]}
        mock_cg.return_value.get_token_data.return_value = {"name": "Bitcoin", "symbol": "btc"}
        mock_cg.return_value.get_market_chart.return_value = {"prices": []}
        mock_binance.return_value.get_ticker_24h.return_value = {}
        mock_binance.return_value.get_depth.return_value = {}
        
        # Mock selection
        mock_prompt.return_value = "bitcoin"

        main()
        
        # Verify selection prompt called, but not text prompt (implied by not mocking it and it not crashing)
        mock_prompt.assert_called_once()

@patch("src.microanalyst.main.CoinGeckoClient")
@patch("src.microanalyst.main.BinanceClient")
@patch("src.microanalyst.main.console")
@patch("sys.stdout.isatty", return_value=False)
def test_non_interactive_missing_token(mock_isatty, mock_console, mock_binance, mock_cg):
    """Test error when token missing and not interactive (or no TTY)."""
    with patch("sys.argv", ["main.py"]), \
         patch("argparse.ArgumentParser.print_help") as mock_print_help:
        # Should print help and return, not exit
        main()
        mock_print_help.assert_called_once()

@patch("src.microanalyst.main.CoinGeckoClient")
@patch("src.microanalyst.main.BinanceClient")
@patch("src.microanalyst.main.console")
@patch("src.microanalyst.main.prompt_token_selection")
@patch("sys.stdout.isatty", return_value=False)
def test_interactive_no_tty(mock_isatty, mock_prompt, mock_console, mock_binance, mock_cg):
    """Test --interactive flag ignored if no TTY (should error if token missing)."""
    with patch("sys.argv", ["main.py", "--interactive"]), \
         patch("argparse.ArgumentParser.print_help") as mock_print_help:
        # Even with --interactive, if isatty is False, it should behave as non-interactive.
        # And since token is missing, it should print help.
        main()
        mock_print_help.assert_called_once()
