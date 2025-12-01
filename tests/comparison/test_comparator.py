import pytest
from src.comparison.comparator import compare_tokens

def test_compare_tokens_basic():
    tokens = [
        {"symbol": "BTC", "volatility": 0.05, "spread": 0.1},
        {"symbol": "ETH", "volatility": 0.08, "spread": 0.2},
        {"symbol": "SOL", "volatility": 0.12, "spread": 0.15}
    ]
    metrics = ["volatility", "spread"]
    
    result = compare_tokens(tokens, metrics)
    
    matrix = result["comparison_matrix"]
    stats = result["summary_stats"]
    
    assert len(matrix) == 3
    assert "volatility_z_score" in matrix[0]
    assert "spread_percentile" in matrix[0]
    
    # Check mean calculation
    # Volatility mean: (0.05 + 0.08 + 0.12) / 3 = 0.08333333
    assert stats["volatility"]["mean"] == pytest.approx(0.08333333)

def test_compare_single_token():
    tokens = [{"symbol": "BTC", "volatility": 0.05}]
    metrics = ["volatility"]
    
    result = compare_tokens(tokens, metrics)
    matrix = result["comparison_matrix"]
    
    assert len(matrix) == 1
    assert matrix[0]["volatility_z_score"] == 0.0 # Std is NaN or 0, handled
    assert matrix[0]["volatility_dev_pct"] == 0.0

def test_missing_metrics():
    tokens = [
        {"symbol": "BTC", "volatility": 0.05},
        {"symbol": "ETH"} # Missing volatility
    ]
    metrics = ["volatility"]
    
    result = compare_tokens(tokens, metrics)
    matrix = result["comparison_matrix"]
    
    assert len(matrix) == 2
    # Check that missing value resulted in NaN/None for stats or handled gracefully
    # Pandas describe ignores NaNs. Mean of [0.05] is 0.05.
    # BTC: (0.05 - 0.05) = 0.
    assert matrix[0]["volatility_z_score"] == 0.0

def test_empty_input():
    result = compare_tokens([], ["volatility"])
    assert result["comparison_matrix"] == []
    assert result["summary_stats"] == {}
