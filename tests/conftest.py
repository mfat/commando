"""Pytest configuration and fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Mock GI before importing commando modules
import sys
from unittest.mock import patch

# Mock gi.repository before any imports
sys.modules['gi'] = MagicMock()
sys.modules['gi.repository'] = MagicMock()

@pytest.fixture
def temp_config_dir():
    """Create a temporary configuration directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_command():
    """Create a mock command object."""
    from commando.models.command import Command
    return Command(
        number=1,
        title="Test Command",
        command="echo 'test'",
        icon="terminal-symbolic",
        color="blue",
        tag="test",
        category="testing",
        description="A test command"
    )

@pytest.fixture
def sample_commands():
    """Create sample commands for testing."""
    from commando.models.command import Command
    return [
        Command(number=1, title="Command 1", command="cmd1"),
        Command(number=2, title="Command 2", command="cmd2"),
        Command(number=3, title="Command 3", command="cmd3"),
    ]

