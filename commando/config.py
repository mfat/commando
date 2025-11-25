"""
Configuration management.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager."""
    
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance
    
    def _get_config_dir(self) -> Path:
        """
        Get configuration directory following XDG Base Directory Specification.
        
        Uses XDG_CONFIG_HOME if set, otherwise defaults to ~/.config
        """
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home:
            config_dir = Path(xdg_config_home) / "commando"
        else:
            config_dir = Path.home() / ".config" / "commando"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    def get_data_dir(self) -> Path:
        """
        Get data directory following XDG Base Directory Specification.
        
        Uses XDG_DATA_HOME if set, otherwise defaults to ~/.local/share
        """
        xdg_data_home = os.environ.get("XDG_DATA_HOME")
        if xdg_data_home:
            data_dir = Path(xdg_data_home) / "commando"
        else:
            data_dir = Path.home() / ".local" / "share" / "commando"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    
    def get_cache_dir(self) -> Path:
        """
        Get cache directory following XDG Base Directory Specification.
        
        Uses XDG_CACHE_HOME if set, otherwise defaults to ~/.cache
        """
        xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
        if xdg_cache_home:
            cache_dir = Path(xdg_cache_home) / "commando"
        else:
            cache_dir = Path.home() / ".cache" / "commando"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def get_state_dir(self) -> Path:
        """
        Get state directory following XDG Base Directory Specification.
        
        Uses XDG_STATE_HOME if set, otherwise defaults to ~/.local/state
        """
        xdg_state_home = os.environ.get("XDG_STATE_HOME")
        if xdg_state_home:
            state_dir = Path(xdg_state_home) / "commando"
        else:
            state_dir = Path.home() / ".local" / "state" / "commando"
        state_dir.mkdir(parents=True, exist_ok=True)
        return state_dir
    
    def _get_config_file(self) -> Path:
        """Get configuration file path."""
        return self._get_config_dir() / "config.json"
    
    def _load(self):
        """Load configuration from file."""
        config_file = self._get_config_file()
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    self._config = json.load(f)
                logger.debug(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                self._config = {}
        else:
            self._config = self._get_defaults()
            self._save()
    
    def _save(self):
        """Save configuration to file."""
        config_file = self._get_config_file()
        try:
            with open(config_file, "w") as f:
                json.dump(self._config, f, indent=2)
            logger.debug(f"Saved configuration to {config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "theme": "system",
            "logging.level": "INFO",
            "terminal.font": "Monospace 12",
            "terminal.scrollback_lines": 10000,
            "terminal.cursor_blink": True,
            "terminal.cursor_shape": "block",
            "terminal.background_color": None,
            "terminal.foreground_color": None,
            "terminal.palette": None,
            "terminal.external_terminal": None,
            "terminal.show_in_main_window": False,
            "main_view.layout": "cards",
            "main_view.sort_by": "number",
            "main_view.sort_ascending": True,
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save()
        logger.debug(f"Set config {key} = {value}")

