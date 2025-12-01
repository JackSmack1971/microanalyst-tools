"""
Progress infrastructure for Microanalyst CLI.
Provides consistent progress bar configuration.
"""
from typing import Dict
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn
)

# Stage Descriptions
# Maps internal stage keys to user-friendly display strings
STAGE_DESCRIPTIONS: Dict[str, str] = {
    "token_search": "Resolving Token ID",
    "market_data": "Fetching Market Data",
    "orderbook": "Querying Order Books",
    "analysis": "Computing Metrics",
    "report": "Generating Report"
}

def create_progress_bar() -> Progress:
    """
    Creates a configured Rich Progress instance.
    
    Returns:
        Progress: Configured progress bar.
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        transient=True # Remove bar when done
    )
