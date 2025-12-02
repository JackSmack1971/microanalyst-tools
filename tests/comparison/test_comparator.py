"""
Unit tests for comparator module.
"""
import pytest
import pandas as pd
from src.comparison.comparator import compare_tokens

class TestComparator:
    
    def test_compare_tokens_returns_correct_structure(self):
        """Test that compare_tokens returns a tuple of DataFrames."""
        results = [
            {
                "symbol": "BTC",
                "current_price": 50000,
                "market_cap": 1000000,
                "total_volume": 50000,
                "volatility": {"cv": 0.05},
                "liquidity": {"spread_pct": 0.1, "depth_2pct": 100000, "imbalance": 1.0}
            },
            {
                "symbol": "ETH",
                "current_price": 3000,
                "market_cap": 500000,
                "total_volume": 30000,
                "volatility": {"cv": 0.06},
                "liquidity": {"spread_pct": 0.1, "depth_2pct": 50000, "imbalance": 1.0}
            }
        ]
        
        metrics_df, correlation_df = compare_tokens(results)
        
        assert isinstance(metrics_df, pd.DataFrame)
        assert isinstance(correlation_df, pd.DataFrame)
        assert not metrics_df.empty
        # Correlation df might be empty if no price history provided
        assert correlation_df.empty 
        
        # Check columns in metrics_df
        expected_cols = ["Symbol", "Price", "Market Cap", "Volume", "CV (Vol)", "Spread %", "Depth ±2%"]
        for col in expected_cols:
            assert col in metrics_df.columns

    def test_compare_tokens_empty_input(self):
        """Test that empty input returns empty DataFrames."""
        metrics_df, correlation_df = compare_tokens([])
        assert metrics_df.empty
        assert correlation_df.empty
