"""Tests for command storage."""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open

from commando.models.command import Command
from commando.storage.command_storage import CommandStorage


class TestCommandStorage:
    """Test CommandStorage class."""
    
    @pytest.fixture
    def temp_storage(self, temp_data_dir):
        """Create a temporary storage instance."""
        with patch('commando.storage.command_storage.Config') as mock_config:
            mock_instance = mock_config.return_value
            mock_instance.get_data_dir.return_value = temp_data_dir
            storage = CommandStorage()
            return storage
    
    def test_storage_initialization(self, temp_storage):
        """Test storage initialization."""
        assert temp_storage is not None
        assert isinstance(temp_storage.get_all(), list)
    
    def test_add_command(self, temp_storage, mock_command):
        """Test adding a command."""
        result = temp_storage.add(mock_command)
        assert result is True
        assert len(temp_storage.get_all()) == 1
    
    def test_add_duplicate_number(self, temp_storage, mock_command):
        """Test adding command with duplicate number."""
        temp_storage.add(mock_command)
        duplicate = Command(number=1, title="Duplicate", command="cmd")
        result = temp_storage.add(duplicate)
        assert result is False
        assert len(temp_storage.get_all()) == 1
    
    def test_get_all(self, temp_storage, sample_commands):
        """Test getting all commands."""
        for cmd in sample_commands:
            temp_storage.add(cmd)
        all_commands = temp_storage.get_all()
        assert len(all_commands) == 3
    
    def test_get_by_number(self, temp_storage, mock_command):
        """Test getting command by number."""
        temp_storage.add(mock_command)
        found = temp_storage.get_by_number(1)
        assert found is not None
        assert found.number == 1
        assert found.title == "Test Command"
    
    def test_get_by_number_not_found(self, temp_storage):
        """Test getting non-existent command."""
        found = temp_storage.get_by_number(999)
        assert found is None
    
    def test_update_command(self, temp_storage, mock_command):
        """Test updating a command."""
        temp_storage.add(mock_command)
        mock_command.title = "Updated Title"
        result = temp_storage.update(mock_command)
        assert result is True
        updated = temp_storage.get_by_number(1)
        assert updated.title == "Updated Title"
    
    def test_update_nonexistent(self, temp_storage):
        """Test updating non-existent command."""
        cmd = Command(number=999, title="Test", command="cmd")
        result = temp_storage.update(cmd)
        assert result is False
    
    def test_delete_command(self, temp_storage, mock_command):
        """Test deleting a command."""
        temp_storage.add(mock_command)
        result = temp_storage.delete(1)
        assert result is True
        assert len(temp_storage.get_all()) == 0
        assert temp_storage.get_by_number(1) is None
    
    def test_delete_nonexistent(self, temp_storage):
        """Test deleting non-existent command."""
        result = temp_storage.delete(999)
        assert result is False
    
    def test_get_next_number_empty(self, temp_storage):
        """Test getting next number when storage is empty."""
        next_num = temp_storage.get_next_number()
        assert next_num == 1
    
    def test_get_next_number_with_commands(self, temp_storage, sample_commands):
        """Test getting next number with existing commands."""
        for cmd in sample_commands:
            temp_storage.add(cmd)
        next_num = temp_storage.get_next_number()
        assert next_num == 4
    
    def test_persistence(self, temp_data_dir):
        """Test that commands persist across storage instances."""
        with patch('commando.storage.command_storage.Config') as mock_config:
            mock_instance = mock_config.return_value
            mock_instance.get_data_dir.return_value = temp_data_dir
            
            # Create first storage and add command
            storage1 = CommandStorage()
            cmd = Command(number=1, title="Test", command="cmd")
            storage1.add(cmd)
            
            # Create second storage and verify command exists
            storage2 = CommandStorage()
            found = storage2.get_by_number(1)
            assert found is not None
            assert found.title == "Test"

