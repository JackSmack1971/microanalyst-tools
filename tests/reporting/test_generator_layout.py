import pytest
from rich.layout import Layout
from src.microanalyst.reporting.generator import generate_report

def test_generate_report_returns_layout():
    """Test that generate_report returns a Layout object."""
    # Mock data
    token_symbol = "eth"
    cg_data = {
        "name": "Ethereum",
        "symbol": "eth",
        "market_cap_rank": 2,
        "market_data": {
            "current_price": {"usd": 2000},
            "market_cap": {"usd": 200000000},
            "total_volume": {"usd": 10000000}
        }
    }
    binance_ticker = {"quoteVolume": 10000000}
    volatility_metrics = {"cv": 0.05}
    volume_metrics = {}
    liquidity_metrics = {"spread_pct": 0.1, "imbalance": 1.0}
    validation_flags = {}
    
    layout = generate_report(
        token_symbol,
        cg_data,
        binance_ticker,
        volatility_metrics,
        volume_metrics,
        liquidity_metrics,
        validation_flags
    )
    
    assert isinstance(layout, Layout)
    
    # Check structure
    # Layout should have children: header, main, footer
    children_names = [child.name for child in layout.children]
    assert "header" in children_names
    assert "main" in children_names
    assert "footer" in children_names
    
    # Check main split
    main_layout = next(child for child in layout.children if child.name == "main")
    main_children_names = [child.name for child in main_layout.children]
    assert "left" in main_children_names
    assert "right" in main_children_names
    
    # Check left split
    left_layout = next(child for child in main_layout.children if child.name == "left")
    left_children_names = [child.name for child in left_layout.children]
    assert "overview" in left_children_names
    assert "risk" in left_children_names
    assert "advanced" in left_children_names
