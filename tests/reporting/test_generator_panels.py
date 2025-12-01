import pytest
from rich.panel import Panel
from src.microanalyst.reporting.generator import generate_overview_panel

def test_generate_overview_panel_structure(rich_console):
    token_data = {
        "name": "Bitcoin",
        "symbol": "btc",
        "market_cap_rank": 1,
        "market_data": {
            "current_price": {"usd": 50000},
            "market_cap": {"usd": 1000000000},
            "total_volume": {"usd": 50000000}
        }
    }
    panel = generate_overview_panel(token_data)
    
    assert isinstance(panel, Panel)
    assert panel.title == "TOKEN OVERVIEW"

def test_generate_overview_panel_content(rich_console, assert_rich_contains):
    token_data = {
        "name": "Bitcoin",
        "symbol": "btc",
        "market_cap_rank": 1,
        "market_data": {
            "current_price": {"usd": 50000},
            "market_cap": {"usd": 1000000000},
            "total_volume": {"usd": 50000000}
        }
    }
    panel = generate_overview_panel(token_data)
    rich_console.print(panel)
    
    # Check content
    assert_rich_contains(rich_console, "BTC")
    assert_rich_contains(rich_console, "Bitcoin")
    assert_rich_contains(rich_console, "#1")
    assert_rich_contains(rich_console, "$50,000.00")
    assert_rich_contains(rich_console, "$1,000,000,000.00") # 1B

def test_generate_overview_panel_missing_data(rich_console, assert_rich_contains):
    token_data = {} # Empty
    panel = generate_overview_panel(token_data)
    rich_console.print(panel)
    
    assert_rich_contains(rich_console, "???")
    assert_rich_contains(rich_console, "Unknown")
    assert_rich_contains(rich_console, "N/A")
    assert_rich_contains(rich_console, "Price: N/A")
