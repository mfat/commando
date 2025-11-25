# Commando Documentation

## Table of Contents

1. [Installation](#installation)
2. [Usage](#usage)
3. [Architecture](#architecture)
4. [Function Reference](#function-reference)
5. [Development](#development)
6. [Packaging](#packaging)

## Installation

### From Source

```bash
git clone https://github.com/commando/commando.git
cd commando
pip install -e .
```

### Dependencies

- Python 3.10+
- PyGObject 3.42.0+
- GTK4
- libadwaita
- VTE 3.91+
- WebKitGTK 6.0+

### System Dependencies

On Fedora:
```bash
sudo dnf install python3-gobject gtk4 libadwaita vte291 webkitgtk6
```

On Ubuntu/Debian:
```bash
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-vte-3.91 gir1.2-webkit-6.0
```

On Arch:
```bash
sudo pacman -S python-gobject gtk4 libadwaita vte3 webkit2gtk
```

## Usage

### Basic Usage

1. Launch Commando from the applications menu or run `commando` from terminal
2. Click "New Command" to create your first command card
3. Fill in the command details (title, command, icon, color, etc.)
4. Click or double-click a card to execute the command
5. Use Ctrl+K to open speed dial and quickly run commands by number

### Keyboard Shortcuts

- `Ctrl+K`: Open speed dial
- `Enter` (in speed dial): Execute command
- `Tab`: Navigate between cards
- `Escape`: Close dialogs/cancel actions
- `Ctrl+N`: New command
- `Ctrl+F`: Focus search
- `Ctrl+,`: Open settings

### Features

#### Command Cards

Each command card has the following properties:
- **Number**: Unique identifier (used for speed dial)
- **Title**: Display name
- **Command**: The actual command to execute
- **Icon**: GTK icon name
- **Color**: Card accent color
- **Tag**: Optional tag for organization
- **Category**: Optional category
- **Description**: Optional description

#### Speed Dial

Type a command number and press Enter to quickly execute it. Press Ctrl+K to open the speed dial.

#### Terminal View

The terminal view supports multiple tabs. Commands executed from cards will run in the active terminal tab.

#### Web View

Use the web view to browse documentation or web pages while working with commands.

## Architecture

### Project Structure

```
commando/
├── commando/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── application.py       # Application class
│   ├── window.py            # Main window
│   ├── config.py            # Configuration management
│   ├── logger.py            # Logging system
│   ├── executor.py          # Command execution
│   ├── models/
│   │   └── command.py       # Command model
│   ├── storage/
│   │   └── command_storage.py  # Data persistence
│   ├── views/
│   │   ├── main_view.py     # Main view with cards
│   │   ├── terminal_view.py # Terminal view
│   │   └── web_view.py      # Web view
│   ├── widgets/
│   │   ├── command_card.py  # Command card widget
│   │   └── speed_dial.py    # Speed dial widget
│   └── dialogs/
│       ├── card_editor.py   # Card editor dialog
│       ├── settings.py      # Settings dialog
│       └── about.py         # About dialog
├── data/                    # Data files (desktop, metainfo)
├── docs/                    # Documentation
├── packaging/               # Packaging files
└── flatpak/                 # Flatpak manifest
```

### Design Patterns

- **MVC-like**: Models (Command), Views (MainView, TerminalView), Controllers (executor, storage)
- **Singleton**: Config class uses singleton pattern
- **Observer**: Signal-based communication between components

## Function Reference

### commando.main

#### `main() -> int`
Main entry point for the application.

**Returns:** Exit status code

### commando.application

#### `CommandoApplication`
Main application class inheriting from `Adw.Application`.

**Methods:**
- `__init__()`: Initialize the application
- `on_activate(app)`: Handle application activation
- `on_shutdown(app)`: Handle application shutdown

### commando.window

#### `CommandoWindow`
Main application window.

**Methods:**
- `__init__(**kwargs)`: Initialize the window
- `_create_header_bar()`: Create the header bar
- `_create_view_switcher()`: Create view switcher
- `_apply_theme()`: Apply current theme
- `_on_theme_toggled(button)`: Handle theme toggle
- `cleanup()`: Clean up resources

### commando.models.command

#### `Command`
Data class representing a command card.

**Attributes:**
- `number: int`: Unique number
- `title: str`: Display title
- `command: str`: Command to execute
- `icon: str`: Icon name
- `color: str`: Color name
- `tag: str`: Tag
- `category: str`: Category
- `description: str`: Description

**Methods:**
- `to_dict() -> dict`: Convert to dictionary
- `from_dict(data: dict) -> Command`: Create from dictionary
- `to_json() -> str`: Convert to JSON
- `from_json(json_str: str) -> Command`: Create from JSON

### commando.storage.command_storage

#### `CommandStorage`
Manages persistent storage of commands.

**Methods:**
- `__init__()`: Initialize storage
- `get_all() -> List[Command]`: Get all commands
- `get_by_number(number: int) -> Optional[Command]`: Get command by number
- `add(command: Command) -> bool`: Add a new command
- `update(command: Command) -> bool`: Update existing command
- `delete(number: int) -> bool`: Delete command
- `get_next_number() -> int`: Get next available number

### commando.executor

#### `CommandExecutor`
Handles command execution.

**Methods:**
- `__init__()`: Initialize executor
- `set_terminal_view(terminal_view)`: Set terminal view for internal execution
- `execute(command: Command, use_external: bool = None)`: Execute a command
- `_execute_internal(command: Command)`: Execute in internal terminal
- `_execute_external(command: Command)`: Execute in external terminal

### commando.views.main_view

#### `MainView`
Main view displaying command cards.

**Methods:**
- `__init__()`: Initialize the view
- `_load_commands()`: Load and display commands
- `_sort_commands(commands: list[Command])`: Sort commands
- `execute_command(command: Command)`: Execute a command
- `get_command_by_number(number: int) -> Command | None`: Get command by number
- `_edit_command(command: Command)`: Open editor for command
- `cleanup()`: Clean up resources

### commando.views.terminal_view

#### `TerminalView`
Terminal view with tab support.

**Methods:**
- `__init__()`: Initialize the view
- `_create_terminal_tab()`: Create a new terminal tab
- `_configure_terminal(terminal: Vte.Terminal)`: Configure terminal
- `execute_command(command: str)`: Execute command in current terminal
- `cleanup()`: Clean up resources

### commando.widgets.command_card

#### `CommandCard`
Card widget representing a command.

**Methods:**
- `__init__(command, on_click, on_double_click, main_view)`: Initialize card
- `_apply_color()`: Apply color styling
- `_on_click(gesture, n_press, x, y)`: Handle click events
- `_on_right_click(gesture, n_press, x, y)`: Handle right-click
- `update_command(command: Command)`: Update card with new command

### commando.config

#### `Config`
Configuration manager (singleton).

**Methods:**
- `get(key: str, default: Any = None) -> Any`: Get configuration value
- `set(key: str, value: Any)`: Set configuration value
- `get_data_dir() -> Path`: Get data directory

### commando.logger

#### Functions:
- `setup_logging(level: LogLevel = None)`: Set up logging
- `get_logger(name: str) -> logging.Logger`: Get logger instance
- `set_log_level(level: LogLevel)`: Change logging level

## Development

### Setting Up Development Environment

```bash
git clone https://github.com/commando/commando.git
cd commando
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Style

The project uses:
- Black for code formatting
- Flake8 for linting
- MyPy for type checking

```bash
black commando/
flake8 commando/
mypy commando/
```

### Building

```bash
python setup.py build
```

## Packaging

### Flatpak

```bash
flatpak-builder build flatpak/com.github.commando.yml --install --user
```

### Debian Package

```bash
cd packaging/debian
dpkg-buildpackage -us -uc
```

### RPM Package

```bash
rpmbuild -ba packaging/rpm/commando.spec
```

### Arch Package

```bash
cd packaging/arch
makepkg -si
```

## Requirements and Dependencies

### Runtime Dependencies

- Python 3.10+
- PyGObject 3.42.0+
- GTK4
- libadwaita
- VTE 3.91+
- WebKitGTK 6.0+

### Build Dependencies

- setuptools
- wheel
- python3-gobject development files
- GTK4 development files
- libadwaita development files
- VTE development files
- WebKitGTK development files

## License

GPL-3.0-or-later

