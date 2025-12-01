import pytest
from src.visualization.charts import generate_price_chart, generate_volume_chart

def test_generate_price_chart():
    dates = ["2023-01-01", "2023-01-02", "2023-01-03"]
    prices = [100.0, 105.0, 102.0]
    
    chart = generate_price_chart(dates, prices, "Test Price Chart")
    
    assert isinstance(chart, str)
    assert len(chart) > 0
    # Check for title
    assert "Test Price Chart" in chart
    # Check for axis labels (plotext adds them)
    # Note: plotext output format might vary, but title should be there.

def test_generate_volume_chart():
    dates = ["2023-01-01", "2023-01-02", "2023-01-03"]
    volumes = [5000.0, 6000.0, 5500.0]
    
    chart = generate_volume_chart(dates, volumes, "Test Volume Chart")
    
    assert isinstance(chart, str)
    assert len(chart) > 0
    assert "Test Volume Chart" in chart

def test_empty_data():
    assert generate_price_chart([], []) == ""
    assert generate_volume_chart([], []) == ""
