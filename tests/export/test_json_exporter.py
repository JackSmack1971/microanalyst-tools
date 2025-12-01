import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock
from src.export.json_exporter import export_to_json

def test_export_json_valid(tmp_path):
    """Test valid JSON export."""
    data = {"key": "value", "number": 123}
    filepath = tmp_path / "output.json"
    
    export_to_json(data, filepath)
    
    assert filepath.exists()
    with open(filepath, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    
    assert loaded_data == data

def test_export_json_types(tmp_path):
    """Test serialization of custom types."""
    dt = datetime(2023, 1, 1, 12, 0, 0)
    dec = Decimal("10.5")
    data = {"date": dt, "decimal": dec}
    filepath = tmp_path / "types.json"
    
    export_to_json(data, filepath)
    
    with open(filepath, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
        
    assert loaded_data["date"] == dt.isoformat()
    assert loaded_data["decimal"] == 10.5

def test_export_json_atomic(tmp_path):
    """
    Test that atomic write uses a temporary file.
    We mock shutil.move to verify it's called.
    """
    data = {"test": "atomic"}
    filepath = tmp_path / "atomic.json"
    
    with patch("shutil.move") as mock_move:
        export_to_json(data, filepath)
        
        # Verify move was called
        assert mock_move.called
        # Verify source was a temp file (not the target)
        args, _ = mock_move.call_args
        src, dst = args
        assert src != str(filepath)
        assert dst == str(filepath)

def test_export_json_error(tmp_path):
    """Test error handling during write."""
    data = {"test": "error"}
    filepath = tmp_path / "error.json"
    
    # Simulate write error by mocking json.dump to raise OSError
    with patch("json.dump", side_effect=OSError("Disk full")):
        with pytest.raises(IOError) as excinfo:
            export_to_json(data, filepath)
        
        assert "Failed to export JSON" in str(excinfo.value)
