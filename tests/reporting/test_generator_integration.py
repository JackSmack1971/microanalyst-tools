import pytest
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from src.microanalyst.reporting.generator import generate_report

def test_generate_report_returns_renderable(rich_console):
    # Mock Data
    cg_data = {
        "market_data": {
            "market_cap": {"usd": 1000000},
            "total_volume": {"usd": 50000},
            "ath_change_percentage": {"usd": -10}
        },
        "market_cap_rank": 1,
        "name": "Bitcoin",
        "symbol": "btc"
    }
    binance_ticker = {"quoteVolume": 50000}
    volatility_metrics = {"cv": 0.05, "bb_width": 10.0}
    volume_metrics = {"vol_change_7d": 5.0}
    liquidity_metrics = {"spread_pct": 0.1, "depth_2pct": 100000, "imbalance": 1.0}
    
    report = generate_report(
        "btc",
        cg_data,
        binance_ticker,
        volatility_metrics,
        volume_metrics,
        liquidity_metrics,
        {}
    )
    
    assert isinstance(report, Group)
    
    # Render to console to check for exceptions and content
    rich_console.print(report)
    output = rich_console.file.getvalue()
    
    # Check for key sections
    assert "TOKEN OVERVIEW" in output
    assert "Quantitative Metrics" in output
    assert "Risk Factors" in output
    assert "Data Confidence" in output
    
    # Check for specific values
    assert "Bitcoin" in output
    assert "0.05" in output # Volatility

def test_generate_report_with_risks(rich_console):
    # Mock Data with Risks
    cg_data = {"market_data": {"total_volume": {"usd": 1000}}}
    binance_ticker = {"quoteVolume": 2000} # High delta
    volatility_metrics = {"cv": 0.2}
    volume_metrics = {}
    liquidity_metrics = {"spread_pct": 1.0, "imbalance": 3.0} # High spread, high imbalance
    
    report = generate_report(
        "btc",
        cg_data,
        binance_ticker,
        volatility_metrics,
        volume_metrics,
        liquidity_metrics,
        {}
    )
    
    rich_console.print(report)
    output = rich_console.file.getvalue()
    
    assert "Wide Bid-Ask Spread" in output
    assert "Volume Discrepancy" in output
    assert "Order Book Imbalance" in output
