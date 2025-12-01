"""
Theme module for Microanalyst CLI.
Centralizes semantic color logic and metric thresholds.
"""
from typing import Dict, Any, List
from rich.panel import Panel
from rich.text import Text
from rich.console import Group

# Metric Thresholds
# These define the boundaries for color coding.
# Volatility: Coefficient of Variation (CV)
# Spread: Percentage
# Volume Delta: Percentage difference between sources
METRIC_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "volatility": {
        "high": 0.12,  # > 12% CV is high volatility
        "low": 0.08    # < 8% CV is low volatility
    },
    "spread": {
        "high": 0.5,   # > 0.5% spread is high/warning
        "medium": 0.2  # > 0.2% is medium
    },
    "volume_delta": {
        "critical": 50.0, # > 50% discrepancy is critical
        "warning": 20.0   # > 20% is warning
    },
    "imbalance": {
        "high": 2.0,   # > 2.0 ratio (buy pressure)
        "low": 0.5     # < 0.5 ratio (sell pressure)
    }
}

# Severity Styles
# Maps semantic severity levels to Rich style strings
SEVERITY_STYLES: Dict[str, str] = {
    "critical": "bold red",
    "warning": "yellow",
    "healthy": "green",
    "neutral": "white",
    "info": "cyan"
}

def get_metric_color(metric_type: str, value: float) -> str:
    """
    Returns the Rich color style for a given metric value based on thresholds.
    
    Args:
        metric_type: One of 'volatility', 'spread', 'volume_delta', 'imbalance'
        value: The numeric value of the metric
        
    Returns:
        str: Rich style string (e.g., 'red', 'green', 'yellow')
    """
    thresholds = METRIC_THRESHOLDS.get(metric_type)
    if not thresholds:
        return SEVERITY_STYLES["neutral"]

    if metric_type == "volatility":
        if value > thresholds["high"]:
            return SEVERITY_STYLES["critical"]
        elif value < thresholds["low"]:
            return SEVERITY_STYLES["healthy"]
        else:
            return SEVERITY_STYLES["warning"] # Medium volatility

    elif metric_type == "spread":
        if value > thresholds["high"]:
            return SEVERITY_STYLES["critical"]
        elif value > thresholds["medium"]:
            return SEVERITY_STYLES["warning"]
        else:
            return SEVERITY_STYLES["healthy"]

    elif metric_type == "volume_delta":
        if value > thresholds["critical"]:
            return SEVERITY_STYLES["critical"]
        elif value > thresholds["warning"]:
            return SEVERITY_STYLES["warning"]
        else:
            return SEVERITY_STYLES["healthy"]
            
    elif metric_type == "imbalance":
        # Imbalance is ratio. 1.0 is neutral. 
        # Far from 1.0 is "interesting" but not necessarily "bad" unless extreme.
        # For this context, let's highlight extreme imbalances.
        if value > thresholds["high"] or value < thresholds["low"]:
            return SEVERITY_STYLES["warning"]
        else:
            return SEVERITY_STYLES["healthy"]

    return SEVERITY_STYLES["neutral"]

def generate_error_panel(title: str, message: str, suggestions: List[str] = None) -> Panel:
    """
    Generates a standardized error panel.
    
    Args:
        title: The error title.
        message: The main error description.
        suggestions: Optional list of actionable suggestions.
        
    Returns:
        Panel: Rich Panel object.
    """
    content_group = [Text(message)]
    
    if suggestions:
        content_group.append(Text("\n💡 Suggestions:", style="bold yellow"))
        for suggestion in suggestions:
            content_group.append(Text(f"• {suggestion}"))
            
    return Panel(
        Group(*content_group),
        title=f"❌ {title}",
        border_style=SEVERITY_STYLES["critical"],
        width=80
    )

def strip_color(text: str) -> str:
    """
    Removes ANSI color codes from text.
    
    Args:
        text: Input text with potential ANSI codes.
        
    Returns:
        str: Plain text without color codes.
    """
    return Text.from_markup(text).plain


