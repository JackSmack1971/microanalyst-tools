import pytest
from pathlib import Path
from unittest.mock import patch
from src.export.html_exporter import export_to_html

def test_export_html_valid(tmp_path):
    """Test valid HTML export."""
    data = {
        "token_symbol": "btc",
        "timestamp": "2023-01-01 12:00:00",
        "overview": {
            "name": "Bitcoin",
            "symbol": "btc",
            "rank": 1,
            "price": "50,000",
            "market_cap": "1,000,000,000",
            "volume_24h": "50,000,000"
        },
        "metrics": [
            {"name": "Volatility", "value": "0.05", "signal": "OK", "signal_class": "signal-ok"}
        ],
        "risks": [],
        "confidence_score": 100
    }
    filepath = tmp_path / "report.html"
    
    export_to_html(data, filepath)
    
    assert filepath.exists()
    content = filepath.read_text(encoding="utf-8")
    
    assert "<!DOCTYPE html>" in content
    assert "Bitcoin" in content
    assert "50,000" in content
    assert "Volatility" in content

def test_export_html_rendering_error(tmp_path):
    """Test error when data is missing required fields."""
    # Missing 'token_symbol' which is used in title
    data = {} 
    filepath = tmp_path / "error.html"
    
    # Verify that it raises ValueError (caught exception from Jinja)
    with pytest.raises(ValueError):
        export_to_html(data, filepath)

def test_export_html_io_error(tmp_path):
    """Test IO error."""
    data = {
        "token_symbol": "btc",
        "timestamp": "2023-01-01",
        "overview": {"name": "Bitcoin", "symbol": "BTC", "rank": 1, "price": 100, "market_cap": 1000, "volume_24h": 500},
        "metrics": [],
        "risks": [],
        "confidence_score": 100
    }
    # directory as file
    filepath = tmp_path / "output.html"
    
    # Mock tempfile.NamedTemporaryFile to raise IOError
    with patch("tempfile.NamedTemporaryFile", side_effect=IOError("Disk full")):
        with pytest.raises(IOError):
            export_to_html(data, filepath)
