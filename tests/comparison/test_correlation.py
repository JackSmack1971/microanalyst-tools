"""
Unit tests for correlation heatmap functionality.
"""
import pytest
import pandas as pd
from rich.table import Table
from src.comparison.comparator import compare_tokens
from src.microanalyst.reporting.generator import generate_correlation_table

class TestCorrelationLogic:
    """Tests for correlation matrix calculation in comparator.py"""
    
    def test_compare_tokens_returns_correlation_matrix(self):
        """Test that compare_tokens returns a valid correlation DataFrame."""
        # Mock results with price history
        results = [
            {
                "symbol": "BTC",
                "current_price": 50000,
                "market_cap": 1000000,
                "total_volume": 50000,
                "volatility": {"cv": 0.05},
                "liquidity": {"spread_pct": 0.1, "depth_2pct": 100000, "imbalance": 1.0},
                "prices": [
                    [1640000000000, 48000], # Day 1
                    [1640086400000, 49000], # Day 2
                    [1640172800000, 50000]  # Day 3
                ]
            },
            {
                "symbol": "ETH",
                "current_price": 3000,
                "market_cap": 500000,
                "total_volume": 30000,
                "volatility": {"cv": 0.06},
                "liquidity": {"spread_pct": 0.1, "depth_2pct": 50000, "imbalance": 1.0},
                "prices": [
                    [1640000000000, 2800], # Day 1 (Perfectly correlated movement)
                    [1640086400000, 2900], # Day 2
                    [1640172800000, 3000]  # Day 3
                ]
            }
        ]
        
        metrics_df, correlation_df = compare_tokens(results)
        
        assert not correlation_df.empty
        assert "BTC" in correlation_df.columns
        assert "ETH" in correlation_df.columns
        assert correlation_df.loc["BTC", "ETH"] > 0.99  # Should be highly correlated

    def test_compare_tokens_handles_missing_prices(self):
        """Test that missing price data is handled gracefully."""
        results = [
            {
                "symbol": "BTC",
                "current_price": 50000,
                "market_cap": 1000000,
                "total_volume": 50000,
                "volatility": {"cv": 0.05},
                "liquidity": {"spread_pct": 0.1, "depth_2pct": 100000, "imbalance": 1.0},
                "prices": [] # No prices
            }
        ]
        
        metrics_df, correlation_df = compare_tokens(results)
        
        assert correlation_df.empty

class TestCorrelationReporting:
    """Tests for correlation table generation in generator.py"""
    
    def test_generate_correlation_table_structure(self):
        """Test that the table has correct columns and rows."""
        data = {
            "BTC": [1.0, 0.9],
            "ETH": [0.9, 1.0]
        }
        df = pd.DataFrame(data, index=["BTC", "ETH"])
        
        table = generate_correlation_table(df)
        
        assert isinstance(table, Table)
        assert table.title == "Market Correlation Heatmap (Pearson)"
        # Columns: Token + BTC + ETH = 3 columns
        assert len(table.columns) == 3 
