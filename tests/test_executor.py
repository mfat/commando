"""Tests for command executor."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from commando.models.command import Command
from commando.executor import CommandExecutor


class TestCommandExecutor:
    """Test CommandExecutor class."""
    
    @pytest.fixture
    def executor(self):
        """Create an executor instance."""
        with patch('commando.executor.Config'):
            return CommandExecutor()
    
    def test_executor_initialization(self, executor):
        """Test executor initialization."""
        assert executor is not None
        assert executor.config is not None
    
    def test_set_terminal_view(self, executor):
        """Test setting terminal view."""
        mock_terminal_view = Mock()
        executor.set_terminal_view(mock_terminal_view)
        assert executor.terminal_view == mock_terminal_view
    
    @patch('commando.executor.subprocess.Popen')
    def test_execute_external(self, mock_popen, executor):
        """Test executing command in external terminal."""
        executor.config.get.return_value = "gnome-terminal"
        cmd = Command(number=1, title="Test", command="echo test")
        
        executor._execute_external(cmd)
        
        mock_popen.assert_called_once()
    
    def test_execute_internal_with_terminal_view(self, executor):
        """Test executing command in internal terminal."""
        mock_terminal_view = Mock()
        executor.set_terminal_view(mock_terminal_view)
        cmd = Command(number=1, title="Test", command="echo test")
        
        executor._execute_internal(cmd)
        
        mock_terminal_view.execute_command.assert_called_once_with("echo test")
    
    @patch('commando.executor.CommandExecutor._execute_external')
    def test_execute_internal_fallback(self, mock_external, executor):
        """Test internal execution falls back to external if no terminal view."""
        executor.terminal_view = None
        executor.config.get.return_value = "gnome-terminal"
        cmd = Command(number=1, title="Test", command="echo test")
        
        executor._execute_internal(cmd)
        
        mock_external.assert_called_once_with(cmd)
    
    def test_get_terminal_command_gnome_terminal(self, executor):
        """Test getting command for gnome-terminal."""
        result = executor._get_terminal_command("gnome-terminal", "echo test")
        assert "gnome-terminal" in result
        assert "echo test" in result
    
    def test_get_terminal_command_xterm(self, executor):
        """Test getting command for xterm."""
        result = executor._get_terminal_command("xterm", "echo test")
        assert "xterm" in result
    
    def test_get_terminal_command_generic(self, executor):
        """Test getting command for generic terminal."""
        result = executor._get_terminal_command("custom-terminal", "echo test")
        assert "custom-terminal" in result

