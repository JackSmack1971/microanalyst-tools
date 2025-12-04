import pytest
import numpy as np
import pandas as pd
from src.microanalyst.analysis.advanced_metrics import (
    calculate_risk_metrics,
    calculate_macd,
    calculate_fibonacci_levels
)

def test_calculate_risk_metrics_basic():
    # Simple uptrend with some volatility
    prices = [100, 110, 115]
    metrics = calculate_risk_metrics(prices)
    assert metrics["max_drawdown"] == 0.0
    assert metrics["sharpe_ratio"] > 0
    assert metrics["sortino_ratio"] > 0

def test_calculate_risk_metrics_drawdown():
    # 100 -> 50 (50% drop) -> 60 (partial recovery but still down)
    prices = [100, 50, 60]
    metrics = calculate_risk_metrics(prices)
    assert metrics["max_drawdown"] == -0.5
    assert metrics["sharpe_ratio"] < 0 # Negative returns

def test_calculate_risk_metrics_empty():
    metrics = calculate_risk_metrics([])
    assert metrics["max_drawdown"] is None
    assert metrics["sharpe_ratio"] is None

def test_calculate_macd_basic():
    # Generate enough data for MACD (need > 26 points)
    prices = [100 + i for i in range(50)]
    metrics = calculate_macd(prices)
    assert metrics["macd_line"] is not None
    assert metrics["signal_line"] is not None
    assert metrics["histogram"] is not None
    assert isinstance(metrics["macd_line"], float)

def test_calculate_macd_insufficient_data():
    prices = [100, 101, 102]
    metrics = calculate_macd(prices)
    assert metrics["macd_line"] is None
    assert metrics["signal_line"] is None

def test_calculate_fibonacci_levels():
    prices = [100, 200] # Low 100, High 200, Diff 100
    levels = calculate_fibonacci_levels(prices)
    
    assert levels["high"] == 200
    assert levels["low"] == 100
    assert levels["fib_0.500"] == 150.0
    assert levels["fib_0.618"] == 138.2 # 200 - (100 * 0.618)
    assert levels["fib_0.236"] == 176.4 # 200 - (100 * 0.236)

def test_calculate_fibonacci_empty():
    levels = calculate_fibonacci_levels([])
    assert levels == {}
