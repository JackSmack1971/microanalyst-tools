"""
Interactive prompts for the CLI using questionary.
"""
import questionary
from typing import List, Dict, Any, Optional

def prompt_token_selection(suggestions: List[Dict[str, Any]]) -> Optional[str]:
    """
    Prompts the user to select a token from a list of suggestions.
    
    Args:
        suggestions: List of dictionaries containing token info (symbol, name, market_cap_rank).
        
    Returns:
        The selected token symbol (lowercase), or None if cancelled/empty.
    """
    if not suggestions:
        return None
        
    choices = []
    for coin in suggestions:
        symbol = coin.get("symbol", "???").upper()
        name = coin.get("name", "Unknown")
        rank = coin.get("market_cap_rank", "N/A")
        display = f"{symbol} ({name}) - Rank #{rank}"
        choices.append(questionary.Choice(title=display, value=coin.get("symbol")))
        
    try:
        answer = questionary.select(
            "Multiple tokens found. Please select one:",
            choices=choices,
            use_indicator=True,
            use_shortcuts=True
        ).ask()
        
        return answer.lower() if answer else None
        
    except KeyboardInterrupt:
        return None
