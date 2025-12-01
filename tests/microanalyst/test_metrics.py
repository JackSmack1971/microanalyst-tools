"""
Unit tests for metrics calculation functions.

Following Classicist TDD approach:
- State-based verification (no mocks)
- Test mathematical properties and invariants
- Edge case coverage
- Property-based testing for invariants
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st
from src.microanalyst.analysis.metrics import (
    calculate_volatility_metrics,
    calculate_volume_metrics,
    calculate_liquidity_metrics
)


class TestVolatilityMetrics:
    """Tests for calculate_volatility_metrics function."""
    
    def test_calculate_volatility_with_valid_prices(self):
        """Test basic volatility calculation with sufficient data."""
        # Arrange: 20+ data points for Bollinger Bands
        prices = [100.0, 105.0, 102.0, 108.0, 103.0, 107.0, 104.0, 109.0,
                  106.0, 110.0, 108.0, 112.0, 109.0, 111.0, 107.0, 113.0,
                  110.0, 114.0, 111.0, 115.0, 112.0]
        
        # Act
        result = calculate_volatility_metrics(prices)
        
        # Assert: Basic structure and invariants
        assert "cv" in result
        assert "bb_width" in result
        assert "ath_distance" in result
        
        # Invariant: Coefficient of variation is non-negative
        assert result["cv"] >= 0
        assert isinstance(result["cv"], float)
        
        # Invariant: Bollinger band width is non-negative
        assert result["bb_width"] >= 0
        assert isinstance(result["bb_width"], float)
    
    def test_calculate_volatility_with_insufficient_data(self):
        """Edge case: Less than 20 data points."""
        prices = [100.0, 105.0, 102.0]
        
        result = calculate_volatility_metrics(prices)
        
        # Should return zero values when insufficient data
        assert result["cv"] == 0.0
        assert result["bb_width"] == 0.0
        assert result["ath_distance"] == 0.0
    
    def test_calculate_volatility_with_empty_list(self):
        """Edge case: Empty price list."""
        prices = []
        
        result = calculate_volatility_metrics(prices)
        
        assert result["cv"] == 0.0
        assert result["bb_width"] == 0.0
    
    def test_calculate_volatility_with_constant_prices(self):
        """Edge case: No variance (all prices equal)."""
        prices = [100.0] * 25
        
        result = calculate_volatility_metrics(prices)
        
        # CV should be 0 when there's no variance
        assert result["cv"] == 0.0
        # BB width should also be 0
        assert result["bb_width"] == 0.0
    
    def test_calculate_volatility_cv_calculation(self):
        """Verify CV formula: std_dev / mean."""
        prices = [100.0, 110.0, 90.0, 105.0, 95.0, 100.0, 110.0, 90.0,
                  105.0, 95.0, 100.0, 110.0, 90.0, 105.0, 95.0, 100.0,
                  110.0, 90.0, 105.0, 95.0, 100.0]
        
        result = calculate_volatility_metrics(prices)
        
        # Manual verification: CV = std/mean
        mean = np.mean(prices)
        std = np.std(prices, ddof=1)  # pandas uses ddof=1 by default
        expected_cv = std / mean if mean != 0 else 0.0
        
        assert abs(result["cv"] - expected_cv) < 0.0001  # Float precision


class TestVolumeMetrics:
    """Tests for calculate_volume_metrics function."""
    
    def test_calculate_volume_with_valid_data(self):
        """Test basic volume change calculation."""
        prices = [100.0, 105.0, 102.0, 108.0, 103.0, 107.0, 104.0]
        volumes = [50000.0, 60000.0, 55000.0, 65000.0, 58000.0, 62000.0, 70000.0]
        
        result = calculate_volume_metrics(prices, volumes)
        
        assert "vol_change_7d" in result
        assert isinstance(result["vol_change_7d"], float)
    
    def test_calculate_volume_with_empty_data(self):
        """Edge case: Empty volumes."""
        prices = []
        volumes = []
        
        result = calculate_volume_metrics(prices, volumes)
        
        assert result["vol_change_7d"] == 0.0
    
    def test_calculate_volume_change_formula(self):
        """Verify volume change formula: (current - avg) / avg * 100."""
        prices = [100.0] * 10
        volumes = [50000.0, 60000.0, 55000.0, 65000.0, 58000.0, 62000.0, 70000.0, 75000.0]
        
        result = calculate_volume_metrics(prices, volumes)
        
        # Manual calculation
        current_vol = volumes[-1]
        avg_vol_7d = np.mean(volumes[-7:])
        expected_change = ((current_vol - avg_vol_7d) / avg_vol_7d) * 100
        
        assert abs(result["vol_change_7d"] - expected_change) < 0.01
    
    def test_calculate_volume_with_less_than_7_days(self):
        """Edge case: Less than 7 data points uses all available."""
        prices = [100.0, 105.0, 102.0]
        volumes = [50000.0, 60000.0, 70000.0]
        
        result = calculate_volume_metrics(prices, volumes)
        
        # Should still calculate using available data
        current_vol = volumes[-1]
        avg_vol = np.mean(volumes)
        expected = ((current_vol - avg_vol) / avg_vol) * 100
        
        assert abs(result["vol_change_7d"] - expected) < 0.01


class TestLiquidityMetrics:
    """Tests for calculate_liquidity_metrics function."""
    
    def test_calculate_liquidity_with_valid_orderbook(self):
        """Test basic liquidity calculation with valid order book."""
        order_book = {
            "bids": [["100.0", "1.5"], ["99.5", "2.0"], ["99.0", "1.0"]],
            "asks": [["101.0", "1.2"], ["101.5", "1.8"], ["102.0", "1.5"]]
        }
        
        result = calculate_liquidity_metrics(order_book)
        
        assert "spread_pct" in result
        assert "imbalance" in result
        assert "depth_2pct" in result
        
        # Invariants
        assert result["spread_pct"] >= 0
        assert result["imbalance"] >= 0
        assert result["depth_2pct"] >= 0
    
    def test_calculate_liquidity_with_empty_orderbook(self):
        """Edge case: Empty order book."""
        order_book = {"bids": [], "asks": []}
        
        result = calculate_liquidity_metrics(order_book)
        
        assert result["spread_pct"] == 0.0
        assert result["imbalance"] == 0.0
        assert result["depth_2pct"] == 0.0
    
    def test_calculate_spread_formula(self):
        """Verify spread calculation: (ask - bid) / midpoint * 100."""
        order_book = {
            "bids": [["100.0", "1.5"]],
            "asks": [["102.0", "1.2"]]
        }
        
        result = calculate_liquidity_metrics(order_book)
        
        best_bid = 100.0
        best_ask = 102.0
        midpoint = (best_bid + best_ask) / 2
        expected_spread = ((best_ask - best_bid) / midpoint) * 100
        
        assert abs(result["spread_pct"] - expected_spread) < 0.0001
    
    def test_calculate_imbalance_ratio(self):
        """Verify imbalance calculation: total_bid_vol / total_ask_vol."""
        order_book = {
            "bids": [["100.0", "2.0"], ["99.5", "3.0"]],  # Total: 5.0
            "asks": [["101.0", "1.0"], ["101.5", "1.5"]]  # Total: 2.5
        }
        
        result = calculate_liquidity_metrics(order_book)
        
        total_bid_vol = 2.0 + 3.0
        total_ask_vol = 1.0 + 1.5
        expected_imbalance = total_bid_vol / total_ask_vol
        
        assert abs(result["imbalance"] - expected_imbalance) < 0.0001


# ======== PROPERTY-BASED TESTS (STRENGTHEN PHASE) ========

class TestVolatilityProperties:
    """Property-based tests for volatility metrics using Hypothesis."""
    
    @given(st.lists(st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False), 
                    min_size=20, max_size=50))
    def test_volatility_cv_always_non_negative(self, prices):
        """Property: CV is always non-negative."""
        result = calculate_volatility_metrics(prices)
        assert result["cv"] >= 0, f"CV should be non-negative, got {result['cv']}"
    
    @given(st.lists(st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False), 
                    min_size=20, max_size=50))
    def test_volatility_bb_width_always_non_negative(self, prices):
        """Property: Bollinger Band width is always non-negative."""
        result = calculate_volatility_metrics(prices)
        assert result["bb_width"] >= 0, f"BB width should be non-negative, got {result['bb_width']}"
    
    @given(st.floats(min_value=1.0, max_value=10000.0))
    def test_volatility_constant_prices_gives_zero_cv(self, constant_price):
        """Property: Constant prices always give CV = 0."""
        prices = [constant_price] * 25
        result = calculate_volatility_metrics(prices)
        assert result["cv"] == 0.0, "Constant prices should give CV = 0"


class TestVolumeProperties:
    """Property-based tests for volume metrics."""
    
    @given(st.lists(st.floats(min_value=100.0, max_value=100000.0, allow_nan=False, allow_infinity=False), 
                    min_size=7, max_size=30))
    def test_volume_change_is_finite(self, volumes):
        """Property: Volume change is always a finite number."""
        prices = [100.0] * len(volumes)
        result = calculate_volume_metrics(prices, volumes)
        assert np.isfinite(result["vol_change_7d"]), "Volume change must be finite"


class TestLiquidityProperties:
    """Property-based tests for liquidity metrics."""
    
    @given(st.floats(min_value=90.0, max_value=100.0),
           st.floats(min_value=100.0, max_value=110.0))
    def test_spread_always_non_negative(self, bid_price, ask_price):
        """Property: Spread percentage is always non-negative."""
        order_book = {
            "bids": [[str(bid_price), "1.0"]],
            "asks": [[str(ask_price), "1.0"]]
        }
        
        result = calculate_liquidity_metrics(order_book)
        assert result["spread_pct"] >= 0, "Spread must be non-negative"
    
    @given(st.floats(min_value=1.0, max_value=10.0),
           st.floats(min_value=1.0, max_value=10.0))
    def test_imbalance_always_non_negative(self, bid_qty, ask_qty):
        """Property: Imbalance ratio is always non-negative."""
        order_book = {
            "bids": [["100.0", str(bid_qty)]],
            "asks": [["101.0", str(ask_qty)]]
        }
        
        result = calculate_liquidity_metrics(order_book)
        assert result["imbalance"] >= 0, "Imbalance must be non-negative"
