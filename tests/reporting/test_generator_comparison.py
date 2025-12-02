import pytest
import pandas as pd
from rich.table import Table
from src.microanalyst.reporting.generator import generate_comparison_table

def test_generate_comparison_table_structure():
    """Test that table has correct columns and rows."""
    data = [
        {"Symbol": "BTC", "Volatility": 0.05, "Volume": 1000},
        {"Symbol": "ETH", "Volatility": 0.08, "Volume": 2000},
        {"Symbol": "SOL", "Volatility": 0.12, "Volume": 3000}
    ]
    metrics_df = pd.DataFrame(data)
    
    table = generate_comparison_table(metrics_df)
    
    assert isinstance(table, Table)
    assert table.title == "Token Comparison Matrix"
    
    # Columns: Symbol, Volatility, Volume
    assert len(table.columns) == 3
    assert table.columns[0].header == "Symbol"
    assert table.columns[1].header == "Volatility"
    assert table.columns[2].header == "Volume"
    
    # Rows: 3 tokens
    assert table.row_count == 3

def test_empty_data():
    """Test handling of empty data."""
    table = generate_comparison_table(pd.DataFrame())
    assert table.title == "Comparison Matrix (Empty)"
    assert table.row_count == 0

def test_formatting_logic():
    """Test that formatting is applied."""
    data = [
        {"Symbol": "BTC", "Price": 50000.0, "Change%": 5.5},
    ]
    metrics_df = pd.DataFrame(data)
    
    table = generate_comparison_table(metrics_df)
    
    assert table.row_count == 1

    # We can't easily check internal cell formatting without rendering,
    # but we verify it runs.
