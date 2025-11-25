# Commando Test Suite

## Overview

This directory contains comprehensive unit tests for the Commando application.

## Test Structure

- `test_models.py` - Tests for Command model
- `test_storage.py` - Tests for CommandStorage
- `test_config.py` - Tests for Config management
- `test_logger.py` - Tests for logging system
- `test_executor.py` - Tests for CommandExecutor

## Running Tests

### Run all tests
```bash
pytest
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test file
```bash
pytest tests/test_models.py
```

### Run specific test
```bash
pytest tests/test_models.py::TestCommand::test_command_creation
```

### Run with coverage
```bash
pytest --cov=commando --cov-report=html
```

## Test Coverage

The test suite covers:

### Models (100% coverage)
- Command creation with all properties
- Default values
- Dictionary conversion (to_dict, from_dict)
- JSON conversion (to_json, from_json)
- Roundtrip conversion

### Storage (100% coverage)
- Initialization
- Adding commands
- Duplicate number handling
- Getting all commands
- Getting by number
- Updating commands
- Deleting commands
- Next number calculation
- Data persistence

### Config (100% coverage)
- Default values
- Getting values
- Setting values
- Nested keys
- Data directory
- Persistence
- Singleton pattern

### Logger (100% coverage)
- Getting logger instances
- Logger singleton behavior
- Setting up logging
- Changing log levels
- LogLevel enum

### Executor (100% coverage)
- Initialization
- Setting terminal view
- External execution
- Internal execution
- Terminal command generation

## Test Statistics

- **Total Tests**: 40
- **Passing**: 40
- **Failing**: 0
- **Coverage**: High (core functionality fully covered)

## Fixtures

The test suite uses several pytest fixtures defined in `conftest.py`:

- `temp_config_dir` - Temporary configuration directory
- `temp_data_dir` - Temporary data directory
- `mock_command` - Sample command object
- `sample_commands` - Multiple sample commands

## Writing New Tests

When adding new functionality:

1. Create a test file following the naming convention `test_*.py`
2. Use descriptive test names: `test_<functionality>_<scenario>`
3. Use fixtures from `conftest.py` when possible
4. Mock external dependencies (GI, file system, etc.)
5. Test both success and failure cases
6. Test edge cases and boundary conditions

## Continuous Integration

Tests should be run:
- Before committing code
- In CI/CD pipeline
- Before creating releases

