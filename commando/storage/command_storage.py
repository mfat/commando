"""
Storage for commands using JSON.
"""

import json
from pathlib import Path
from typing import List, Optional

from commando.models.command import Command
from commando.config import Config
from commando.logger import get_logger

logger = get_logger(__name__)


class CommandStorage:
    """Manages persistent storage of commands."""
    
    def __init__(self):
        """Initialize storage."""
        self.config = Config()
        self.data_dir = self.config.get_data_dir()
        self.storage_file = self.data_dir / "commands.json"
        self._commands: List[Command] = []
        self._load()
    
    def _load(self):
        """Load commands from storage."""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r") as f:
                    data = json.load(f)
                    self._commands = [Command.from_dict(cmd) for cmd in data]
                logger.info(f"Loaded {len(self._commands)} commands from storage")
            except Exception as e:
                logger.error(f"Failed to load commands: {e}")
                self._commands = []
        else:
            self._commands = []
            self._save()
    
    def _save(self):
        """Save commands to storage."""
        try:
            data = [cmd.to_dict() for cmd in self._commands]
            with open(self.storage_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self._commands)} commands to storage")
        except Exception as e:
            logger.error(f"Failed to save commands: {e}")
    
    def get_all(self) -> List[Command]:
        """Get all commands."""
        return self._commands.copy()
    
    def get_by_number(self, number: int) -> Optional[Command]:
        """Get command by number."""
        for cmd in self._commands:
            if cmd.number == number:
                return cmd
        return None
    
    def add(self, command: Command) -> bool:
        """Add a new command."""
        # Check if number already exists
        if self.get_by_number(command.number) is not None:
            logger.warning(f"Command number {command.number} already exists")
            return False
        
        self._commands.append(command)
        self._save()
        logger.info(f"Added command: {command.title} (#{command.number})")
        return True
    
    def update(self, command: Command) -> bool:
        """Update an existing command."""
        for i, cmd in enumerate(self._commands):
            if cmd.number == command.number:
                self._commands[i] = command
                self._save()
                logger.info(f"Updated command: {command.title} (#{command.number})")
                return True
        logger.warning(f"Command #{command.number} not found for update")
        return False
    
    def delete(self, number: int) -> bool:
        """Delete a command by number."""
        for i, cmd in enumerate(self._commands):
            if cmd.number == number:
                deleted = self._commands.pop(i)
                self._save()
                logger.info(f"Deleted command: {deleted.title} (#{number})")
                return True
        logger.warning(f"Command #{number} not found for deletion")
        return False
    
    def get_next_number(self) -> int:
        """Get the next available command number."""
        if not self._commands:
            return 1
        numbers = [cmd.number for cmd in self._commands]
        return max(numbers) + 1

