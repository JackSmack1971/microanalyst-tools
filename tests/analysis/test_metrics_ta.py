import pytest
import pandas as pd
import numpy as np
from src.microanalyst.analysis.metrics import calculate_technical_indicators

def test_calculate_technical_indicators_insufficient_data():
    prices = [100.0] * 49
    result = calculate_technical_indicators(prices)
    assert result["rsi"] is None
    assert result["sma_20"] is None
    assert result["sma_50"] is None
    assert result["trend"] == "NEUTRAL"

def test_calculate_technical_indicators_uptrend():
    # Create a sequence where price > sma20 > sma50
    # Linear increase: 1, 2, 3... 100
    prices = list(range(1, 101))
    prices = [float(p) for p in prices]
    
    result = calculate_technical_indicators(prices)
    
    assert result["rsi"] is not None
    assert result["rsi"] == 100.0 # Pure uptrend means no loss, so RSI -> 100
    assert result["sma_20"] is not None
    assert result["sma_50"] is not None
    assert result["trend"] == "BULLISH"
    
    # Verify SMA values
    # SMA 20 of 81..100 is (81+100)/2 = 90.5
    assert result["sma_20"] == 90.5
    # SMA 50 of 51..100 is (51+100)/2 = 75.5
    assert result["sma_50"] == 75.5

def test_calculate_technical_indicators_downtrend():
    # Linear decrease: 100, 99... 1
    prices = list(range(100, 0, -1))
    prices = [float(p) for p in prices]
    
    result = calculate_technical_indicators(prices)
    
    assert result["rsi"] == 0.0 # Pure downtrend
    assert result["trend"] == "BEARISH"

def test_calculate_technical_indicators_neutral():
    # Oscillating price around 100
    prices = [100.0, 101.0, 99.0, 100.0] * 25 # 100 points
    
    result = calculate_technical_indicators(prices)
    
    # Trend should be neutral because SMAs will be close to 100 and price is 100
    # But strictly, if price == sma20 == sma50, it's neutral.
    # Let's verify it's not BULLISH or BEARISH
    assert result["trend"] == "NEUTRAL"
    
    # RSI should be around 50
    assert 40 < result["rsi"] < 60
