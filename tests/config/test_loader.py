import pytest
import yaml
from pathlib import Path
from src.config.loader import load_config, validate_config

def test_load_defaults():
    """Test loading default configuration."""
    config = load_config()
    assert config["defaults"]["days"] == 30
    assert config["defaults"]["output_format"] == "terminal"
    assert config["providers"]["binance"]["rate_limit_ms"] == 100

def test_load_user_config(tmp_path):
    """Test loading user configuration overrides."""
    user_config_path = tmp_path / "config.yaml"
    user_config_data = {
        "defaults": {
            "days": 60
        },
        "display": {
            "compact_mode": True
        }
    }
    
    with open(user_config_path, "w") as f:
        yaml.dump(user_config_data, f)
        
    config = load_config(user_config_path)
    
    # Check overrides
    assert config["defaults"]["days"] == 60
    assert config["display"]["compact_mode"] is True
    
    # Check preserved defaults
    assert config["defaults"]["output_format"] == "terminal"
    assert config["providers"]["binance"]["rate_limit_ms"] == 100

def test_invalid_yaml(tmp_path):
    """Test handling of invalid YAML file."""
    invalid_config_path = tmp_path / "invalid.yaml"
    with open(invalid_config_path, "w") as f:
        f.write("invalid: yaml: [unclosed list")
        
    # Should not crash, but return defaults (and maybe log warning)
    config = load_config(invalid_config_path)
    
    # Should still have defaults
    assert config["defaults"]["days"] == 30

def test_validation_error():
    """Test validation logic."""
    invalid_config = {"defaults": {}} # Missing other sections
    
    with pytest.raises(ValueError, match="Missing required config section"):
        validate_config(invalid_config)
