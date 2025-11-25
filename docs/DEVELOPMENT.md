# Development Guide

## Project Structure

```
commando/
├── commando/              # Main application package
│   ├── __init__.py
│   ├── main.py            # Entry point
│   ├── application.py     # Application class
│   ├── window.py          # Main window
│   ├── config.py          # Configuration
│   ├── logger.py          # Logging
│   ├── executor.py        # Command execution
│   ├── models/            # Data models
│   ├── storage/           # Data persistence
│   ├── views/             # UI views
│   ├── widgets/           # Custom widgets
│   └── dialogs/           # Dialogs
├── data/                  # Data files
├── docs/                  # Documentation
├── packaging/             # Packaging files
├── flatpak/               # Flatpak manifest
├── pyproject.toml         # Python project config
├── setup.py               # Setup script
└── README.md              # Main readme
```

## Code Organization

### Models
- `commando.models.command`: Command data model

### Storage
- `commando.storage.command_storage`: JSON-based storage for commands

### Views
- `commando.views.main_view`: Main view with command cards
- `commando.views.terminal_view`: Terminal view with tabs
- `commando.views.web_view`: Web view using WebKit

### Widgets
- `commando.widgets.command_card`: Command card widget
- `commando.widgets.speed_dial`: Speed dial widget

### Dialogs
- `commando.dialogs.card_editor`: Card editor dialog
- `commando.dialogs.settings`: Settings dialog
- `commando.dialogs.about`: About dialog

## Adding New Features

### Adding a New Command Property

1. Update `commando.models.command.Command` dataclass
2. Update `commando.dialogs.card_editor.CardEditorDialog` to include the new field
3. Update `commando.widgets.command_card.CommandCard` to display the new property
4. Update storage format if needed (JSON schema)

### Adding a New View

1. Create new view class in `commando.views`
2. Add view to `commando.window.CommandoWindow`
3. Add view to the view stack
4. Update view switcher if needed

### Adding Keyboard Shortcuts

Add shortcuts in `commando.window.CommandoWindow._setup_keyboard_navigation()`:

```python
shortcut = Gtk.Shortcut.new(
    Gtk.ShortcutTrigger.parse_string("<Primary>key"),
    Gtk.CallbackAction.new(callback_function)
)
self.add_controller(shortcut)
```

## Testing

### Running Tests

```bash
pytest
```

### Manual Testing Checklist

- [ ] Create a new command
- [ ] Edit an existing command
- [ ] Delete a command
- [ ] Execute command via click
- [ ] Execute command via double-click
- [ ] Use speed dial (Ctrl+K)
- [ ] Search commands
- [ ] Sort commands
- [ ] Toggle layout
- [ ] Switch themes
- [ ] Open settings
- [ ] Use terminal tabs
- [ ] Execute command in terminal
- [ ] Browse web view

## Debugging

### Enable Debug Logging

1. Open settings
2. Change log level to "Debug"
3. Check logs in `~/.local/share/commando/logs/commando.log`

### Common Issues

#### Terminal not spawning
- Check VTE installation
- Verify shell path
- Check permissions

#### Commands not executing
- Check executor configuration
- Verify terminal view connection
- Check logs for errors

#### Cards not displaying
- Check storage file: `~/.local/share/commando/commands.json`
- Verify JSON format
- Check logs for parsing errors

## Code Style

- Follow PEP 8
- Use type hints
- Document all public functions and classes
- Keep functions focused and small
- Use meaningful variable names

## Git Workflow

1. Create feature branch
2. Make changes
3. Run tests and linting
4. Commit with descriptive message
5. Push and create pull request

## Release Process

1. Update version in `commando/__init__.py` and `pyproject.toml`
2. Update CHANGELOG
3. Create git tag
4. Build packages
5. Upload to repositories

