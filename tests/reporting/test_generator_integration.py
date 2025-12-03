import pytest
from rich.layout import Layout
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
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
    
    from rich.layout import Layout
    assert isinstance(report, Layout)
    
    # Check Layout Structure
    assert "header" in [c.name for c in report.children]
    assert "main" in [c.name for c in report.children]
    assert "footer" in [c.name for c in report.children]
    
    # Check Header Content
    header_panel = report["header"].renderable
    assert isinstance(header_panel, Panel)
    assert "MICROANALYST REPORT" in str(header_panel.renderable)
    assert "BTC" in str(header_panel.renderable)
    
    # Check Footer Content
    footer_panel = report["footer"].renderable
    assert isinstance(footer_panel, Panel)
    # The footer content is a Group, so we check its renderables
    footer_group = footer_panel.renderable
    assert isinstance(footer_group, Group)
    # We can't easily stringify a Group without rendering, but we can check its renderables list
    footer_texts = [str(r) for r in footer_group.renderables if isinstance(r, Text)]
    assert any("Data Confidence" in t for t in footer_texts)
    
    # Check Overview
    overview_panel = report["overview"].renderable
    assert isinstance(overview_panel, Panel)
    # Overview content is Columns -> Group -> Text
    # This is getting deep, let's just assert the panel exists and has the title
    assert overview_panel.title == "TOKEN OVERVIEW"

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
    
    # Check Risk Panel
    risk_panel = report["risk"].renderable
    assert isinstance(risk_panel, Panel)
    risk_table = risk_panel.renderable
    assert isinstance(risk_table, Table)
    
    # Check rows in the table
    # We can inspect the table columns/rows if needed, but Rich Tables are hard to inspect without rendering.
    # Let's render just the table to a string
    rich_console.print(risk_table)
    output = rich_console.file.getvalue()
    
    assert "Wide Bid-Ask Spread" in output
    assert "Volume Discrepancy" in output
    assert "Order Book Imbalance" in output
