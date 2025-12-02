import pytest
from unittest.mock import patch, MagicMock
import sys
from src.microanalyst.main import main

def test_frictionless_entry_tty(rich_console):
    """Test that interactive mode is auto-enabled in TTY with no args."""
    with patch("sys.stdout.isatty", return_value=True), \
         patch("sys.argv", ["microanalyst"]), \
         patch("src.microanalyst.main.questionary.text") as mock_ask, \
         patch("src.microanalyst.main.console", rich_console):
        
        # Mock the user input to return None/empty to exit early and avoid full analysis
        mock_ask.return_value.ask.return_value = None
        
        main()
        
        # Should have asked for input
        assert mock_ask.called
        assert "Enter token symbol" in mock_ask.call_args[0][0]

def test_frictionless_entry_no_tty(rich_console):
    """Test that help is printed in non-TTY with no args."""
    with patch("sys.stdout.isatty", return_value=False), \
         patch("sys.argv", ["microanalyst"]), \
         patch("src.microanalyst.main.console", rich_console), \
         patch("argparse.ArgumentParser.print_help") as mock_print_help:
        
        main()
        
        # Should have printed help
        assert mock_print_help.called
