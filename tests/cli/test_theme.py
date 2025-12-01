import pytest
from src.cli.theme import get_metric_color, SEVERITY_STYLES, generate_error_panel
from rich.panel import Panel

def test_get_metric_color_volatility():
    # High volatility (> 0.12)
    assert get_metric_color("volatility", 0.15) == SEVERITY_STYLES["critical"]
    # Low volatility (< 0.08)
    assert get_metric_color("volatility", 0.05) == SEVERITY_STYLES["healthy"]
    # Medium volatility (0.08 - 0.12)
    assert get_metric_color("volatility", 0.10) == SEVERITY_STYLES["warning"]
    
    # Boundary cases
    # 0.12 is not strictly > 0.12, so it falls to else (warning)
    assert get_metric_color("volatility", 0.12) == SEVERITY_STYLES["warning"] 

def test_get_metric_color_spread():
    # High spread (> 0.5)
    assert get_metric_color("spread", 0.6) == SEVERITY_STYLES["critical"]
    # Medium spread (> 0.2)
    assert get_metric_color("spread", 0.3) == SEVERITY_STYLES["warning"]
    # Low spread (<= 0.2)
    assert get_metric_color("spread", 0.1) == SEVERITY_STYLES["healthy"]

def test_get_metric_color_volume_delta():
    # Critical (> 50)
    assert get_metric_color("volume_delta", 60.0) == SEVERITY_STYLES["critical"]
    # Warning (> 20)
    assert get_metric_color("volume_delta", 30.0) == SEVERITY_STYLES["warning"]
    # Healthy (<= 20)
    assert get_metric_color("volume_delta", 10.0) == SEVERITY_STYLES["healthy"]

def test_get_metric_color_imbalance():
    # High (> 2.0)
    assert get_metric_color("imbalance", 2.5) == SEVERITY_STYLES["warning"]
    # Low (< 0.5)
    assert get_metric_color("imbalance", 0.4) == SEVERITY_STYLES["warning"]
    # Neutral (0.5 - 2.0)
    assert get_metric_color("imbalance", 1.0) == SEVERITY_STYLES["healthy"]

def test_get_metric_color_unknown():
    assert get_metric_color("unknown_metric", 100) == SEVERITY_STYLES["neutral"]

def test_generate_error_panel(rich_console, assert_rich_contains):
    panel = generate_error_panel(
        title="Connection Failed",
        message="Could not connect to CoinGecko API.",
        suggestions=["Check internet connection", "Verify API status"]
    )
    
    assert isinstance(panel, Panel)
    rich_console.print(panel)
    
    assert_rich_contains(rich_console, "❌ Connection Failed")
    assert_rich_contains(rich_console, "Could not connect to CoinGecko API.")
    assert_rich_contains(rich_console, "Suggestions:")
    assert_rich_contains(rich_console, "Check internet connection")

