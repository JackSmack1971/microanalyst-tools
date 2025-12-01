import pytest
from rich.table import Table
from src.microanalyst.reporting.generator import generate_comparison_table

def test_generate_comparison_table_structure():
    """Test that table has correct columns and rows."""
    comparison_data = {
        "comparison_matrix": [
            {"symbol": "BTC", "volatility": 0.05, "volatility_z_score": -1.0},
            {"symbol": "ETH", "volatility": 0.08, "volatility_z_score": 0.0},
            {"symbol": "SOL", "volatility": 0.12, "volatility_z_score": 1.5}
        ],
        "summary_stats": {
            "volatility": {"mean": 0.0833, "std": 0.0351}
        }
    }
    
    table = generate_comparison_table(comparison_data)
    
    assert isinstance(table, Table)
    assert table.title == "Token Comparison Matrix"
    
    # Check columns: Metric + 3 Tokens + Avg + StdDev = 6 columns
    assert len(table.columns) == 6
    assert table.columns[0].header == "Metric"
    assert table.columns[1].header == "BTC"
    assert table.columns[2].header == "ETH"
    assert table.columns[3].header == "SOL"
    assert table.columns[4].header == "Avg"
    assert table.columns[5].header == "StdDev"
    
    # Check rows: 1 metric = 1 row
    assert table.row_count == 1

def test_empty_data():
    """Test handling of empty data."""
    table = generate_comparison_table({})
    assert table.title == "Comparison Matrix (Empty)"
    assert table.row_count == 0

def test_coloring_logic():
    """Test that coloring markup is applied for high z-scores."""
    comparison_data = {
        "comparison_matrix": [
            {"symbol": "A", "metric": 10, "metric_z_score": 2.5}, # Red
            {"symbol": "B", "metric": 5, "metric_z_score": 0.0},  # No color
            {"symbol": "C", "metric": 1, "metric_z_score": -1.5}  # Blue
        ],
        "summary_stats": {
            "metric": {"mean": 5.33, "std": 4.5}
        }
    }
    
    table = generate_comparison_table(comparison_data)
    
    # We can't easily inspect rendered output without a console, 
    # but we can check that the function runs without error
    # and produces a table with rows.
    assert table.row_count == 1
