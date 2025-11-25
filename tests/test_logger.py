"""Tests for logging system."""

import pytest
import logging
from unittest.mock import patch, MagicMock

from commando.logger import setup_logging, get_logger, set_log_level, LogLevel


class TestLogger:
    """Test logging functionality."""
    
    def test_get_logger(self):
        """Test getting a logger instance."""
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"
    
    def test_get_logger_singleton(self):
        """Test that get_logger returns same instance for same name."""
        logger1 = get_logger("test.module")
        logger2 = get_logger("test.module")
        assert logger1 is logger2
    
    @patch('commando.logger.logging.getLogger')
    @patch('commando.logger.logging.StreamHandler')
    @patch('commando.logger.logging.FileHandler')
    @patch('commando.logger.Path.mkdir')
    def test_setup_logging(self, mock_mkdir, mock_file_handler, mock_stream_handler, mock_get_logger):
        """Test setting up logging."""
        mock_root_logger = MagicMock()
        mock_get_logger.return_value = mock_root_logger
        
        with patch('commando.config.Config') as mock_config:
            mock_instance = mock_config.return_value
            mock_instance.get.return_value = "INFO"
            mock_instance.get_data_dir.return_value = MagicMock()
            
            setup_logging()
            
            # Verify handlers were added
            assert mock_root_logger.addHandler.called
    
    def test_set_log_level(self):
        """Test changing log level."""
        with patch('commando.logger.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            set_log_level(LogLevel.DEBUG)
            
            mock_logger.setLevel.assert_called_with(logging.DEBUG)
    
    def test_log_level_enum(self):
        """Test LogLevel enum values."""
        assert LogLevel.DEBUG.value == logging.DEBUG
        assert LogLevel.INFO.value == logging.INFO
        assert LogLevel.WARNING.value == logging.WARNING
        assert LogLevel.ERROR.value == logging.ERROR
        assert LogLevel.CRITICAL.value == logging.CRITICAL

