import pytest
from unittest.mock import patch, MagicMock
from src.cli.prompts import prompt_token_selection

def test_prompt_selection():
    """Test that prompt returns the selected symbol."""
    suggestions = [
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin", "market_cap_rank": 1},
        {"id": "ethereum", "symbol": "eth", "name": "Ethereum", "market_cap_rank": 2}
    ]
    
    # Mock questionary.select().ask()
    with patch("questionary.select") as mock_select:
        mock_ask = mock_select.return_value.ask
        mock_ask.return_value = "bitcoin" # ID
        
        result = prompt_token_selection(suggestions)
        
        assert result == "bitcoin"
        
        # Verify choices were formatted correctly
        args, kwargs = mock_select.call_args
        choices = kwargs["choices"]
        assert len(choices) == 2
        assert choices[0].title == "BTC (Bitcoin) - Rank #1"
        # Since we don't have ID in suggestions above, let's update suggestions too


def test_prompt_empty():
    """Test behavior with empty suggestions."""
    assert prompt_token_selection([]) is None

def test_prompt_cancellation():
    """Test that None is returned if user cancels (returns None from ask)."""
    suggestions = [{"symbol": "btc", "name": "Bitcoin", "market_cap_rank": 1}]
    
    with patch("questionary.select") as mock_select:
        mock_select.return_value.ask.return_value = None
        
        result = prompt_token_selection(suggestions)
        
        assert result is None

def test_prompt_keyboard_interrupt():
    """Test handling of Ctrl+C."""
    suggestions = [{"symbol": "btc", "name": "Bitcoin", "market_cap_rank": 1}]
    
    with patch("questionary.select") as mock_select:
        mock_select.return_value.ask.side_effect = KeyboardInterrupt
        
        result = prompt_token_selection(suggestions)
        
        assert result is None
