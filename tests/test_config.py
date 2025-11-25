"""Tests for configuration management."""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open

from commando.config import Config


class TestConfig:
    """Test Config class."""
    
    @pytest.fixture
    def temp_config(self, temp_config_dir):
        """Create a temporary config instance."""
        with patch('commando.config.Config._get_config_dir', return_value=temp_config_dir):
            with patch('commando.config.Config.get_data_dir', return_value=temp_config_dir):
                config = Config()
                # Reset singleton
                Config._instance = None
                config = Config()
                return config
    
    def test_config_get_default(self, temp_config):
        """Test getting default configuration values."""
        theme = temp_config.get("theme")
        assert theme == "system"
        
        # After initialization, defaults should be loaded
        log_level = temp_config.get("logging.level", "INFO")
        assert log_level == "INFO"
    
    def test_config_get_custom_default(self, temp_config):
        """Test getting config with custom default."""
        value = temp_config.get("nonexistent.key", "default_value")
        assert value == "default_value"
    
    def test_config_set_and_get(self, temp_config):
        """Test setting and getting configuration."""
        temp_config.set("test.key", "test_value")
        value = temp_config.get("test.key")
        assert value == "test_value"
    
    def test_config_nested_keys(self, temp_config):
        """Test nested configuration keys."""
        temp_config.set("section.subsection.key", "value")
        result = temp_config.get("section.subsection.key")
        assert result == "value"
    
    def test_config_get_data_dir(self, temp_config):
        """Test getting data directory."""
        data_dir = temp_config.get_data_dir()
        assert isinstance(data_dir, Path)
        assert data_dir.exists()
    
    def test_config_persistence(self, temp_config_dir):
        """Test that configuration persists."""
        with patch('commando.config.Config._get_config_dir', return_value=temp_config_dir):
            with patch('commando.config.Config.get_data_dir', return_value=temp_config_dir):
                # Create first config and set value
                Config._instance = None
                config1 = Config()
                config1.set("test.key", "persisted_value")
                
                # Create second config and verify value
                Config._instance = None
                config2 = Config()
                value = config2.get("test.key")
                assert value == "persisted_value"
    
    def test_config_singleton(self):
        """Test that Config is a singleton."""
        with patch('commando.config.Config._get_config_dir'):
            with patch('commando.config.Config.get_data_dir'):
                Config._instance = None
                config1 = Config()
                config2 = Config()
                assert config1 is config2

