import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional

DEFAULTS_PATH = Path(__file__).parent / "defaults.yaml"

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from defaults and optional user config file.
    
    Args:
        config_path: Path to user configuration file.
        
    Returns:
        Merged configuration dictionary.
    """
    # Load defaults
    if not DEFAULTS_PATH.exists():
        raise FileNotFoundError(f"Defaults file not found at {DEFAULTS_PATH}")
        
    with open(DEFAULTS_PATH, "r") as f:
        config = yaml.safe_load(f) or {}
        
    # Determine user config path if not provided
    if not config_path:
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            user_path = Path(xdg_config) / "microanalyst" / "config.yaml"
        else:
            user_path = Path.home() / ".microanalyst" / "config.yaml"
            
        if user_path.exists():
            config_path = user_path
            
    # Load and merge user config
    if config_path and config_path.exists():
        try:
            with open(config_path, "r") as f:
                user_config = yaml.safe_load(f) or {}
                _deep_merge(config, user_config)
        except yaml.YAMLError as e:
            # In a real app we might log this, but for now we just warn or ignore
            # print(f"Warning: Failed to parse config file {config_path}: {e}")
            pass
            
    validate_config(config)
    return config

def _deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> None:
    """Recursive merge of dictionaries."""
    for key, val in update.items():
        if isinstance(val, dict) and key in base and isinstance(base[key], dict):
            _deep_merge(base[key], val)
        else:
            base[key] = val

def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration schema.
    
    Args:
        config: Configuration dictionary.
        
    Returns:
        True if valid.
        
    Raises:
        ValueError: If configuration is invalid.
    """
    required_sections = ["defaults", "providers", "display"]
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required config section: {section}")
            
    return True
