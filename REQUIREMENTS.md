# Requirements and Dependencies

## Runtime Requirements

### Python
- Python 3.10 or higher

### System Libraries
- GTK4 (4.0 or higher)
- libadwaita (1.0 or higher)
- VTE (3.91 or higher)
- WebKitGTK (6.0 or higher)

### Python Packages
- PyGObject 3.42.0 or higher

## Build Requirements

### Python Build Tools
- setuptools 61.0 or higher
- wheel

### Development Tools (Optional)
- pytest (for testing)
- black (for code formatting)
- flake8 (for linting)
- mypy (for type checking)

## System-Specific Installation

### Fedora
```bash
sudo dnf install python3-gobject gtk4 libadwaita vte291 webkitgtk6
```

### Ubuntu/Debian
```bash
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-vte-3.91 gir1.2-webkit-6.0
```

### Arch Linux
```bash
sudo pacman -S python-gobject gtk4 libadwaita vte3 webkit2gtk
```

### openSUSE
```bash
sudo zypper install python3-gobject gtk4 libadwaita-1 vte webkit2gtk6
```

## Flatpak Runtime

When building as Flatpak, the following runtime is required:
- org.gnome.Platform 45 or higher
- org.gnome.Sdk 45 or higher

## Version Compatibility

| Component | Minimum Version | Recommended Version |
|-----------|----------------|---------------------|
| Python | 3.10 | 3.11+ |
| PyGObject | 3.42.0 | Latest |
| GTK4 | 4.0 | 4.8+ |
| libadwaita | 1.0 | 1.2+ |
| VTE | 3.91 | 3.92+ |
| WebKitGTK | 6.0 | 6.2+ |

## Optional Dependencies

### External Terminal Support
If you want to use an external terminal instead of the built-in one, you need:
- gnome-terminal, xterm, konsole, alacritty, or another terminal emulator

### Development Dependencies
For contributing to the project:
```bash
pip install -e ".[dev]"
```

This installs:
- pytest
- black
- flake8
- mypy

