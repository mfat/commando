"""
Command model representing a saved command card.
"""

from dataclasses import dataclass, asdict
from typing import Optional
import json

from commando.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Command:
    """Represents a command card."""
    
    number: int
    title: str
    command: str
    icon: str = "terminal-symbolic"
    color: str = "blue"
    tag: str = ""
    category: str = ""
    description: str = ""
    no_terminal: bool = False  # If True, run command directly without terminal
    run_mode: int = 1  # 1 = execute command, 2 = type command in terminal without executing
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Command":
        """Create from dictionary."""
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "Command":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))

