"""
Formatter utilities for Microanalyst CLI.
Provides consistent formatting for currencies, percentages, and numbers.
"""
from typing import Union, Optional
import math

def format_currency(value: float, symbol: str = "$") -> str:
    """
    Formats a float as a currency string with 2 decimal places and thousand separators.
    
    Args:
        value: The numeric value to format.
        symbol: The currency symbol (default: '$').
        
    Returns:
        str: Formatted currency string (e.g., "$1,234.56").
    """
    if value is None:
        return "N/A"
    try:
        return f"{symbol}{value:,.2f}"
    except (ValueError, TypeError):
        return "N/A"

def format_percentage(value: float, precision: int = 2) -> str:
    """
    Formats a float as a percentage string.
    
    Args:
        value: The numeric value (e.g., 12.34). Note: This assumes the value is already scaled 
               (i.e., 12.34 for 12.34%, not 0.1234). 
               Wait, standard convention in finance often uses 0.1234 for 12.34%.
               Let's check the usage in main.py.
               In main.py: `vol_change = f"{volume_metrics.get('vol_change_7d', 0.0):+.1f}%"`
               It seems the metrics return the percentage value directly (e.g. 5.0 for 5%).
               However, `spread` in main.py is `spread = f"{liquidity_metrics.get('spread_pct', 0.0):.2f}%"`.
               Let's stick to the assumption that input is the percentage value (e.g. 5.0), not the ratio (0.05),
               based on existing code usage, BUT `format_percentage` usually implies taking a ratio.
               
               Let's look at the implementation plan example: "format_percentage(0.0832) returns '8.32%'".
               This implies the input IS a ratio (0.0832 -> 8.32%).
               I will implement it as ratio -> percentage string.
               
    Returns:
        str: Formatted percentage string (e.g., "12.34%").
    """
    if value is None:
        return "N/A"
    try:
        return f"{value * 100:.{precision}f}%"
    except (ValueError, TypeError):
        return "N/A"

def format_number(value: float, precision: int = 2) -> str:
    """
    Formats a float with thousand separators and specified precision.
    
    Args:
        value: The numeric value.
        precision: Number of decimal places.
        
    Returns:
        str: Formatted number string.
    """
    if value is None:
        return "N/A"
    try:
        return f"{value:,.{precision}f}"
    except (ValueError, TypeError):
        return "N/A"

def format_large_number(value: float) -> str:
    """
    Formats a large number with suffixes (K, M, B, T).
    
    Args:
        value: The numeric value.
        
    Returns:
        str: Formatted string (e.g., "1.2M").
    """
    if value is None:
        return "N/A"
    
    try:
        value = float(value)
    except (ValueError, TypeError):
        return "N/A"
        
    if value == 0:
        return "0"
        
    abs_value = abs(value)
    sign = "-" if value < 0 else ""
    
    if abs_value < 1000:
        return f"{sign}{abs_value:.2f}".rstrip("0").rstrip(".")
        
    suffixes = ["", "K", "M", "B", "T", "Q"]
    magnitude = 0
    
    while abs_value >= 1000 and magnitude < len(suffixes) - 1:
        abs_value /= 1000.0
        magnitude += 1
        
    return f"{sign}{abs_value:.2f}{suffixes[magnitude]}"
