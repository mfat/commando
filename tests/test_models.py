"""Tests for command model."""

import pytest
import json
from commando.models.command import Command         


class TestCommand:
    """Test Command model."""
    
    def test_command_creation(self):
        """Test creating a command with all properties."""
        cmd = Command(
            number=1,
            title="Test",
            command="echo test",
            icon="icon",
            color="blue",
            tag="tag",
            category="cat",
            description="desc"
        )
        assert cmd.number == 1
        assert cmd.title == "Test"
        assert cmd.command == "echo test"
        assert cmd.icon == "icon"
        assert cmd.color == "blue"
        assert cmd.tag == "tag"
        assert cmd.category == "cat"
        assert cmd.description == "desc"
    
    def test_command_defaults(self):
        """Test command with default values."""
        cmd = Command(number=1, title="Test", command="cmd")
        assert cmd.icon == "terminal-symbolic"
        assert cmd.color == "blue"
        assert cmd.tag == ""
        assert cmd.category == ""
        assert cmd.description == ""
    
    def test_command_to_dict(self):
        """Test converting command to dictionary."""
        cmd = Command(number=1, title="Test", command="cmd")
        data = cmd.to_dict()
        assert isinstance(data, dict)
        assert data["number"] == 1
        assert data["title"] == "Test"
        assert data["command"] == "cmd"
    
    def test_command_from_dict(self):
        """Test creating command from dictionary."""
        data = {
            "number": 1,
            "title": "Test",
            "command": "cmd",
            "icon": "icon",
            "color": "red"
        }
        cmd = Command.from_dict(data)
        assert cmd.number == 1
        assert cmd.title == "Test"
        assert cmd.command == "cmd"
        assert cmd.icon == "icon"
        assert cmd.color == "red"
    
    def test_command_to_json(self):
        """Test converting command to JSON."""
        cmd = Command(number=1, title="Test", command="cmd")
        json_str = cmd.to_json()
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["number"] == 1
    
    def test_command_from_json(self):
        """Test creating command from JSON."""
        json_str = '{"number": 1, "title": "Test", "command": "cmd"}'
        cmd = Command.from_json(json_str)
        assert cmd.number == 1
        assert cmd.title == "Test"
        assert cmd.command == "cmd"
    
    def test_command_roundtrip(self):
        """Test roundtrip conversion."""
        original = Command(
            number=1,
            title="Test",
            command="cmd",
            icon="icon",
            color="blue",
            tag="tag"
        )
        data = original.to_dict()
        restored = Command.from_dict(data)
        assert restored.number == original.number
        assert restored.title == original.title
        assert restored.command == original.command
        assert restored.icon == original.icon
        assert restored.color == original.color
        assert restored.tag == original.tag

