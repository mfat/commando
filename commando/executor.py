"""
Command execution handler.
"""

import subprocess
import shlex
from pathlib import Path

from commando.models.command import Command
from commando.config import Config
from commando.logger import get_logger

logger = get_logger(__name__)


class CommandExecutor:
    """Handles command execution."""
    
    def __init__(self):
        """Initialize executor."""
        self.config = Config()
        self.terminal_mode_1_view = None  # Terminal mode 1: terminal view in ViewStack
        self.terminal_mode_2_view = None  # Terminal mode 2: terminal at bottom of main window
    
    def set_terminal_view(self, terminal_view):
        """Set the terminal mode 1 view for internal execution."""
        self.terminal_mode_1_view = terminal_view
    
    def execute(self, command: Command, use_external: bool = None):
        """
        Execute a command.
        
        Args:
            command: Command to execute
            use_external: Whether to use external terminal. If None, reads from config.
        """
        # Check if command should run directly without terminal
        if getattr(command, 'no_terminal', False):
            self._execute_direct(command)
            return
        
        if use_external is None:
            external_terminal = self.config.get("terminal.external_terminal")
            use_external = external_terminal is not None
        
        if use_external:
            self._execute_external(command)
        else:
            self._execute_internal(command)
    
    def _execute_internal(self, command: Command):
        """Execute command in internal terminal."""
        logger.info(f"Executing command in internal terminal: {command.command}")
        
        # Prefer terminal mode 2 if it exists (it's only created when setting is enabled)
        # Otherwise use terminal mode 1
        target_terminal = None
        if self.terminal_mode_2_view:
            target_terminal = self.terminal_mode_2_view
            logger.debug("Using terminal mode 2 for command execution")
        elif self.terminal_mode_1_view:
            target_terminal = self.terminal_mode_1_view
            logger.debug("Using terminal mode 1 for command execution")
        
        if target_terminal:
            # Execute in the selected terminal
            target_terminal.execute_command(command.command, create_new_tab=True)
            # Focus the terminal after executing command - use multiple attempts
            # The execute_command method will also try to focus, but we add extra attempts here
            from gi.repository import GLib
            def focus_terminal():
                if target_terminal:
                    target_terminal.focus_current_terminal()
                return False  # Don't repeat
            
            # Try multiple times with increasing delays to ensure terminal is ready
            # Start with longer delays since the terminal needs to spawn first
            GLib.timeout_add(200, focus_terminal)  # After spawn
            GLib.timeout_add(400, focus_terminal)  # After command execution
            GLib.timeout_add(800, focus_terminal)  # Final attempt
        else:
            logger.warning("No terminal view available, falling back to external")
            self._execute_external(command)
    
    def _execute_external(self, command: Command):
        """Execute command in external terminal."""
        external_terminal = self.config.get("terminal.external_terminal")
        if not external_terminal:
            logger.error("External terminal not configured")
            return
        
        # Parse terminal command
        # Common patterns: gnome-terminal -e "command", xterm -e "command", etc.
        try:
            # Try to detect terminal type
            terminal_cmd = self._get_terminal_command(external_terminal, command.command)
            
            logger.info(f"Executing in external terminal: {terminal_cmd}")
            subprocess.Popen(terminal_cmd, shell=True)
        except Exception as e:
            logger.error(f"Failed to execute in external terminal: {e}")
    
    def _execute_direct(self, command: Command):
        """Execute command directly without terminal."""
        logger.info(f"Executing command directly (no terminal): {command.command}")
        try:
            # Use shell=True to allow shell features, but run in background
            # This runs the command directly without opening a terminal
            subprocess.Popen(
                command.command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True  # Detach from parent process
            )
            logger.debug(f"Command started in background: {command.command}")
        except Exception as e:
            logger.error(f"Failed to execute command directly: {e}")
    
    def _get_terminal_command(self, terminal: str, command: str) -> str:
        """Get the command to launch terminal with command."""
        # Common terminal patterns
        if "gnome-terminal" in terminal:
            return f'gnome-terminal -- bash -c "{command}; exec bash"'
        elif "xterm" in terminal:
            return f'xterm -e bash -c "{command}; exec bash"'
        elif "konsole" in terminal:
            return f'konsole -e bash -c "{command}; exec bash"'
        elif "alacritty" in terminal:
            return f'alacritty -e bash -c "{command}; exec bash"'
        else:
            # Generic fallback
            return f'{terminal} -e bash -c "{command}; exec bash"'

