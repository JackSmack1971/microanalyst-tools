"""
JSON Exporter module for Microanalyst.
Handles serialization of report data to JSON files.
"""
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from decimal import Decimal

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON Encoder for datetime and Decimal types."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def export_to_json(data: Dict[str, Any], filepath: Path) -> None:
    """
    Exports data to a JSON file using atomic write.
    
    Args:
        data: Dictionary of data to export.
        filepath: Path to the output file.
        
    Raises:
        IOError: If file writing fails.
    """
    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a temporary file in the same directory to ensure atomic move works
    # (os.rename across filesystems can fail)
    temp_dir = filepath.parent
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=temp_dir, delete=False, encoding='utf-8') as tmp_file:
            json.dump(data, tmp_file, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
            temp_path = Path(tmp_file.name)
            
        # Atomic move
        shutil.move(str(temp_path), str(filepath))
        
    except (IOError, OSError) as e:
        # Clean up temp file if it exists
        if 'temp_path' in locals() and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise IOError(f"Failed to export JSON to {filepath}: {e}")
