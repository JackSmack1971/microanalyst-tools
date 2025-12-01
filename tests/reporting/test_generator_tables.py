import pytest
from rich.table import Table
from src.microanalyst.reporting.generator import generate_metric_table
from src.cli.theme import SEVERITY_STYLES

def test_generate_metric_table_structure(rich_console):
    metrics = {
        "volatility": 0.05,
        "spread": 0.1,
        "volume_delta": 5.0,
        "imbalance": 1.0
    }
    table = generate_metric_table(metrics)
    
    assert isinstance(table, Table)
    assert table.title == "Quantitative Metrics"
    assert len(table.columns) == 3
    assert table.columns[0].header == "Metric"

def test_generate_metric_table_content(rich_console, assert_rich_contains):
    metrics = {
        "volatility": 0.15, # High -> Critical
        "spread": 0.05,     # Low -> Healthy
        "volume_delta": 55.0, # Critical
        "imbalance": 2.5    # High -> Warning
    }
    table = generate_metric_table(metrics)
    rich_console.print(table)
    
    # Volatility: 0.15 -> 0.15 (number)
    assert_rich_contains(rich_console, "Volatility (CV)")
    assert_rich_contains(rich_console, "0.15")
    assert_rich_contains(rich_console, "HIGH") # Signal
    
    # Spread: 0.05 -> 0.05% (percentage)
    assert_rich_contains(rich_console, "Spread")
    assert_rich_contains(rich_console, "0.05%")
    
    # Volume Delta: 55.0 -> 55.0%
    assert_rich_contains(rich_console, "Volume Delta")
    assert_rich_contains(rich_console, "55.0%")
    
    # Imbalance: 2.5 -> 2.50
    assert_rich_contains(rich_console, "Imbalance")
    assert_rich_contains(rich_console, "2.50")

def test_generate_metric_table_empty(rich_console):
    metrics = {}
    table = generate_metric_table(metrics)
    assert isinstance(table, Table)
    assert table.row_count == 0
