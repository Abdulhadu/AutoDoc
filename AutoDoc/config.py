"""Configuration handling for AutoDoc."""

import os
import yaml
import json
from typing import Dict, Any, Optional


DEFAULT_CONFIG = {
    "source": {
        "directories": ["."],
        "exclude": ["venv", "env", ".venv", ".env", "__pycache__", ".git", "build", "dist"],
    },
    "ai": {
        "model": "models/gemini-1.5-flash",
        "temperature": 0.2,
        "max_output_tokens": 8192,
    },
    "output": {
        "format": "markdown",
        "index_title": "API Documentation",
        "group_by": "module",
    },
    "tests": {
        "framework": "pytest",
        "output_dir": "tests",
        "exclude": ["tests", "test", "testing"],
    }
}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML or JSON file and merge with defaults.

    Args:
        config_path: Path to the configuration file

    Returns:
        Dictionary with configuration values
    """
    config = DEFAULT_CONFIG.copy()
    
    if not config_path:
        # Look for config in common locations
        for filename in ["autodoc.yaml", "autodoc.yml", "autodoc.json"]:
            if os.path.exists(filename):
                config_path = filename
                break
    
    if config_path and os.path.exists(config_path):
        with open(config_path, "r") as f:
            if config_path.endswith((".yaml", ".yml")):
                user_config = yaml.safe_load(f)
            elif config_path.endswith(".json"):
                user_config = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_path}")
        
        # Merge configs (simple recursive merge)
        _merge_configs(config, user_config)
    
    return config


def _merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> None:
    """
    Recursively merge override dictionary into base dictionary.
    
    Args:
        base: Base configuration dictionary (modified in-place)
        override: Override configuration dictionary
    """
    for key, value in override.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            _merge_configs(base[key], value)
        else:
            base[key] = value


def save_default_config(path: str = "autodoc.yaml") -> str:
    """
    Save the default configuration to a file.

    Args:
        path: Path where to save the configuration

    Returns:
        Path to the saved configuration file
    """
    with open(path, "w") as f:
        yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, sort_keys=False)
    
    return os.path.abspath(path)
