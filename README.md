# Commando

A minimal, well-structured GTK4 / libadwaita terminal emulator: tabbed local
shells plus a **command sidebar** of reusable snippets (folders, favorites, live
search, and `${VAR}` placeholder substitution).

Commando started life as two pieces of [sshpilot](https://github.com/mfat/sshpilot)
— the tabbed terminal and the command sidebar — extracted into a standalone,
SSH-free foundation to build on.

## Features

- Tabbed local terminal (VTE) running your login shell
- Command sidebar with folders, favorites, and full-text search
- `${VAR}` placeholders prompt for values before a command is sent
- Add / edit / duplicate / delete commands; settings persist to JSON
- Keyboard-friendly: `/` to search, Enter to run, Ctrl+E to edit, Del to delete

## Requirements

System libraries (with GObject-introspection typelibs):

- GTK 4 ≥ 4.6
- libadwaita ≥ 1.4
- VTE for GTK 4 (`gir1.2-vte-3.91` / `vte3` built with `-Dgtk4=true`)
- Python ≥ 3.9

Python packages: `PyGObject`, `pycairo` (see `requirements.txt`).

On Debian/Ubuntu:

```sh
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-vte-3.91
```

On Fedora:

```sh
sudo dnf install python3-gobject gtk4 libadwaita vte291-gtk4
```

## Run

```sh
python3 run.py
```

## Configuration

Settings and saved commands live in `~/.config/commando/config.json`.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
