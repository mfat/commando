# Commando API Reference

## Module: commando.main

### Function: `main() -> int`

Main entry point for the Commando application.

**Returns:**
- `int`: Exit status code (0 for success, non-zero for error)

**Example:**
```python
from commando.main import main
exit_code = main()
```

---

## Module: commando.application

### Class: `CommandoApplication(Adw.Application)`

Main application class that manages the application lifecycle.

#### Methods

##### `__init__()`

Initialize the Commando application.

**Side Effects:**
- Sets up application ID
- Connects activation and shutdown signals
- Initializes configuration

##### `on_activate(self, app: Adw.Application) -> None`

Handle application activation. Creates and presents the main window if it doesn't exist.

**Parameters:**
- `app`: The application instance

##### `on_shutdown(self, app: Adw.Application) -> None`

Handle application shutdown. Cleans up resources.

**Parameters:**
- `app`: The application instance

---

## Module: commando.window

### Class: `CommandoWindow(Adw.ApplicationWindow)`

Main application window containing all views.

#### Methods

##### `__init__(**kwargs)`

Initialize the main window.

**Parameters:**
- `**kwargs`: Additional arguments passed to parent class

**Side Effects:**
- Creates header bar
- Creates view switcher
- Creates main, terminal, and web views
- Sets up speed dial
- Applies theme

##### `_create_header_bar(self) -> None`

Create the header bar with menu button and theme toggle.

##### `_create_view_switcher(self) -> None`

Create the view switcher for navigating between views.

##### `_apply_theme(self) -> None`

Apply the current theme from configuration.

##### `_on_theme_toggled(self, button: Gtk.ToggleButton) -> None`

Handle theme toggle button press. Cycles through light, dark, and system themes.

**Parameters:**
- `button`: The toggle button that was pressed

##### `cleanup(self) -> None`

Clean up window resources. Called on shutdown.

---

## Module: commando.models.command

### Class: `Command`

Data class representing a command card with all its properties.

#### Attributes

- `number: int` - Unique command number
- `title: str` - Display title
- `command: str` - Command to execute
- `icon: str` - GTK icon name (default: "terminal-symbolic")
- `color: str` - Color name (default: "blue")
- `tag: str` - Optional tag (default: "")
- `category: str` - Optional category (default: "")
- `description: str` - Optional description (default: "")

#### Methods

##### `to_dict(self) -> dict`

Convert command to dictionary.

**Returns:**
- `dict`: Dictionary representation of the command

##### `from_dict(cls, data: dict) -> Command`

Create Command instance from dictionary.

**Parameters:**
- `data`: Dictionary containing command data

**Returns:**
- `Command`: New Command instance

##### `to_json(self) -> str`

Convert command to JSON string.

**Returns:**
- `str`: JSON string representation

##### `from_json(cls, json_str: str) -> Command`

Create Command instance from JSON string.

**Parameters:**
- `json_str`: JSON string

**Returns:**
- `Command`: New Command instance

---

## Module: commando.storage.command_storage

### Class: `CommandStorage`

Manages persistent storage of commands using JSON.

#### Methods

##### `__init__(self)`

Initialize storage. Loads commands from file.

##### `get_all(self) -> List[Command]`

Get all stored commands.

**Returns:**
- `List[Command]`: List of all commands

##### `get_by_number(self, number: int) -> Optional[Command]`

Get command by its number.

**Parameters:**
- `number`: Command number

**Returns:**
- `Optional[Command]`: Command if found, None otherwise

##### `add(self, command: Command) -> bool`

Add a new command to storage.

**Parameters:**
- `command`: Command to add

**Returns:**
- `bool`: True if added successfully, False if number already exists

##### `update(self, command: Command) -> bool`

Update an existing command.

**Parameters:**
- `command`: Command with updated data

**Returns:**
- `bool`: True if updated successfully, False if command not found

##### `delete(self, number: int) -> bool`

Delete a command by number.

**Parameters:**
- `number`: Command number to delete

**Returns:**
- `bool`: True if deleted successfully, False if command not found

##### `get_next_number(self) -> int`

Get the next available command number.

**Returns:**
- `int`: Next available number

---

## Module: commando.executor

### Class: `CommandExecutor`

Handles command execution in internal or external terminals.

#### Methods

##### `__init__(self)`

Initialize the executor.

##### `set_terminal_view(self, terminal_view) -> None`

Set the terminal view for internal command execution.

**Parameters:**
- `terminal_view`: TerminalView instance

##### `execute(self, command: Command, use_external: bool = None) -> None`

Execute a command.

**Parameters:**
- `command`: Command to execute
- `use_external`: Whether to use external terminal. If None, reads from config.

##### `_execute_internal(self, command: Command) -> None`

Execute command in internal terminal view.

**Parameters:**
- `command`: Command to execute

##### `_execute_external(self, command: Command) -> None`

Execute command in external terminal.

**Parameters:**
- `command`: Command to execute

---

## Module: commando.config

### Class: `Config`

Configuration manager using singleton pattern.

#### Methods

##### `get(self, key: str, default: Any = None) -> Any`

Get configuration value. Supports dot notation for nested keys.

**Parameters:**
- `key`: Configuration key (e.g., "theme" or "terminal.font")
- `default`: Default value if key not found

**Returns:**
- `Any`: Configuration value

**Example:**
```python
config = Config()
theme = config.get("theme", "system")
font = config.get("terminal.font", "Monospace 12")
```

##### `set(self, key: str, value: Any) -> None`

Set configuration value. Supports dot notation.

**Parameters:**
- `key`: Configuration key
- `value`: Value to set

**Example:**
```python
config = Config()
config.set("theme", "dark")
config.set("terminal.font", "Monospace 14")
```

##### `get_data_dir(self) -> Path`

Get the data directory path.

**Returns:**
- `Path`: Path to data directory

---

## Module: commando.logger

### Functions

##### `setup_logging(level: LogLevel = None) -> None`

Set up logging configuration.

**Parameters:**
- `level`: Logging level. If None, reads from config.

##### `get_logger(name: str) -> logging.Logger`

Get a logger instance.

**Parameters:**
- `name`: Logger name (typically `__name__`)

**Returns:**
- `logging.Logger`: Logger instance

**Example:**
```python
from commando.logger import get_logger
logger = get_logger(__name__)
logger.info("Message")
```

##### `set_log_level(level: LogLevel) -> None`

Change the logging level at runtime.

**Parameters:**
- `level`: New logging level

---

## Module: commando.views.main_view

### Class: `MainView(Adw.Bin)`

Main view displaying command cards.

#### Methods

##### `execute_command(self, command: Command) -> None`

Execute a command.

**Parameters:**
- `command`: Command to execute

##### `get_command_by_number(self, number: int) -> Command | None`

Get command by number.

**Parameters:**
- `number`: Command number

**Returns:**
- `Command | None`: Command if found

---

## Module: commando.views.terminal_view

### Class: `TerminalView(Adw.Bin)`

Terminal view with tab support.

#### Methods

##### `execute_command(self, command: str) -> None`

Execute a command in the current terminal.

**Parameters:**
- `command`: Command string to execute

---

## Module: commando.widgets.command_card

### Class: `CommandCard(Gtk.Box)`

Card widget representing a command.

#### Methods

##### `update_command(self, command: Command) -> None`

Update the card with a new command.

**Parameters:**
- `command`: Updated command

---

## Module: commando.dialogs.card_editor

### Class: `CardEditorDialog(Adw.Dialog)`

Dialog for editing command card properties.

#### Signals

- `command-saved`: Emitted when command is saved
  - Parameters: `(dialog, command: Command)`

#### Methods

##### `__init__(self, command: Command, **kwargs)`

Initialize the editor dialog.

**Parameters:**
- `command`: Command to edit
- `**kwargs`: Additional arguments for parent class

---

## Module: commando.dialogs.settings

### Class: `SettingsDialog(Adw.PreferencesWindow)`

Settings dialog for application preferences.

#### Methods

##### `__init__(**kwargs)`

Initialize the settings dialog.

---

## Module: commando.dialogs.about

### Class: `AboutDialog(Adw.AboutWindow)`

About dialog showing application information.

#### Methods

##### `__init__(**kwargs)`

Initialize the about dialog.

