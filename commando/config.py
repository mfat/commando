"""Configuration and terminal colour profiles.

A deliberately small settings store backed by a single JSON file under the XDG
config directory. Settings use dotted keys (e.g. ``terminal.theme``) and are
flushed to disk atomically. The same file also holds the command-sidebar data
(folders/commands) under the ``commands`` key.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from typing import Any

logger = logging.getLogger(__name__)


# Two built-in terminal colour profiles. The shape mirrors what the VTE widget
# consumes in ``terminal.py`` (foreground/background/cursor/highlight + a
# 16-entry ANSI palette + a Pango font string).
_PALETTE = [
    "#2E3436", "#CC0000", "#4E9A06", "#C4A000",
    "#3465A4", "#75507B", "#06989A", "#D3D7CF",
    "#555753", "#EF2929", "#8AE234", "#FCE94F",
    "#729FCF", "#AD7FA8", "#34E2E2", "#EEEEEC",
]

BUILTIN_PROFILES: dict[str, dict[str, Any]] = {
    "default": {
        "foreground": "#1A1A1A",
        "background": "#FFFFFF",
        "cursor_color": "#1A1A1A",
        "highlight_background": "#4A90E2",
        "highlight_foreground": "#FFFFFF",
        "font": "Monospace 12",
        "palette": list(_PALETTE),
    },
    "dark": {
        "foreground": "#D3D7CF",
        "background": "#1E1E1E",
        "cursor_color": "#FFFFFF",
        "highlight_background": "#4A90E2",
        "highlight_foreground": "#FFFFFF",
        "font": "Monospace 12",
        "palette": list(_PALETTE),
    },
}

DEFAULTS: dict[str, Any] = {
    "app-theme": "default",          # libadwaita colour scheme: default/light/dark
    "terminal.theme": "dark",        # which BUILTIN_PROFILES entry to use
    "terminal.insert_only": False,   # paste sidebar commands without a trailing newline
    "terminal.auto_hide_sidebar": False,
}


def _config_dir() -> str:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "commando")


class Config:
    """JSON-backed settings + command store."""

    def __init__(self) -> None:
        self.path = os.path.join(_config_dir(), "config.json")
        self.config_data: dict[str, Any] = {}
        self._load()

    # -- persistence -------------------------------------------------------

    def _load(self) -> None:
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                self.config_data = json.load(fh)
        except FileNotFoundError:
            self.config_data = {}
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read config %s: %s", self.path, exc)
            self.config_data = {}

    def save(self) -> None:
        """Atomically write the config to disk."""
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.path), suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self.config_data, fh, indent=2)
            os.replace(tmp, self.path)
        except OSError as exc:
            logger.error("Failed to save config %s: %s", self.path, exc)

    # Alias kept so the ported command store reads naturally.
    save_json_config = save

    # -- settings ----------------------------------------------------------

    def get_setting(self, key: str, default: Any = None) -> Any:
        if key in self.config_data:
            return self.config_data[key]
        if key in DEFAULTS:
            return DEFAULTS[key]
        return default

    def set_setting(self, key: str, value: Any) -> None:
        self.config_data[key] = value
        self.save()

    # -- terminal profiles -------------------------------------------------

    def get_terminal_profile(self, name: str | None = None) -> dict[str, Any]:
        if name is None:
            name = self.get_setting("terminal.theme", "dark")
        return dict(BUILTIN_PROFILES.get(name, BUILTIN_PROFILES["default"]))
