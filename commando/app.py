"""Application entry point for Commando."""

from __future__ import annotations

import logging
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk  # noqa: E402

from . import APP_ID, __version__
from .config import Config
from .window import MainWindow

logger = logging.getLogger(__name__)

_COLOR_SCHEMES = {
    "default": Adw.ColorScheme.DEFAULT,
    "light": Adw.ColorScheme.FORCE_LIGHT,
    "dark": Adw.ColorScheme.FORCE_DARK,
}


class CommandoApplication(Adw.Application):
    def __init__(self) -> None:
        super().__init__(application_id=APP_ID,
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.config = Config()
        self.window: MainWindow | None = None

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)

        scheme = _COLOR_SCHEMES.get(
            str(self.config.get_setting("app-theme", "default")),
            Adw.ColorScheme.DEFAULT)
        Adw.StyleManager.get_default().set_color_scheme(scheme)

        self._add_action("new-tab", lambda *_a: self._win() and self.window.new_tab(),
                         ["<Primary><Shift>t"])
        self._add_action("close-tab", lambda *_a: self._win() and self.window.close_current_tab(),
                         ["<Primary><Shift>w"])
        self._add_action("copy", lambda *_a: self._win() and self.window.copy_active(),
                         ["<Primary><Shift>c"])
        self._add_action("paste", lambda *_a: self._win() and self.window.paste_active(),
                         ["<Primary><Shift>v"])
        self._add_action("toggle-sidebar", lambda *_a: self._win() and self.window.toggle_sidebar(),
                         ["F9"])
        self._add_action("quit", lambda *_a: self.quit(), ["<Primary>q"])

    def do_activate(self) -> None:
        if self.window is None:
            self.window = MainWindow(self, self.config)
        self.window.present()

    # -- helpers -----------------------------------------------------------

    def _win(self) -> bool:
        return self.window is not None

    def _add_action(self, name: str, callback, accels: list[str]) -> None:
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if accels:
            self.set_accels_for_action(f"app.{name}", accels)


def main() -> int:
    logging.basicConfig(level=logging.WARNING,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if "--version" in sys.argv[1:]:
        print(f"Commando {__version__}")
        return 0
    return CommandoApplication().run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
