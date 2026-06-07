"""A self-contained VTE terminal widget running a local login shell.

Distilled from sshpilot's ``VTETerminalBackend`` and local-shell spawn path,
with all SSH/Connection/process-manager coupling removed. One instance == one
local shell in one tab.
"""

from __future__ import annotations

import logging
import os
import pwd

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Vte", "3.91")
from gi.repository import Gdk, GLib, Gtk, Pango, Vte  # noqa: E402

logger = logging.getLogger(__name__)


def _resolve_shell() -> str:
    """Pick the user's login shell, preferring the passwd database."""
    try:
        shell = pwd.getpwuid(os.getuid()).pw_shell
    except (KeyError, AttributeError):
        shell = None
    return shell or os.environ.get("SHELL") or "/bin/bash"


class TerminalWidget(Gtk.Box):
    """Vertical box wrapping a scrolled ``Vte.Terminal``."""

    __gtype_name__ = "CommandoTerminal"

    def __init__(self, config) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.config = config

        self.vte = Vte.Terminal()
        self.vte.set_hexpand(True)
        self.vte.set_vexpand(True)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        scrolled.set_child(self.vte)
        self.append(scrolled)

        self._configure_vte()
        self.apply_theme()

    # -- setup -------------------------------------------------------------

    def _configure_vte(self) -> None:
        vte = self.vte
        try:
            vte.set_cursor_blink_mode(Vte.CursorBlinkMode.ON)
            vte.set_cursor_shape(Vte.CursorShape.BLOCK)
            vte.set_scrollback_lines(10000)
            vte.set_scroll_on_keystroke(True)
            vte.set_scroll_on_output(False)
            vte.set_mouse_autohide(True)
            vte.set_allow_bold(True)
            vte.set_word_char_exceptions("@-./_~")
        except Exception:
            logger.debug("Failed to apply some VTE properties", exc_info=True)
        try:
            vte.set_encoding("UTF-8")
        except Exception:
            logger.debug("Failed to set encoding", exc_info=True)

    def apply_theme(self, theme_name: str | None = None) -> None:
        """Apply colours and font from the active terminal profile."""
        profile = self.config.get_terminal_profile(theme_name)
        try:
            fg = Gdk.RGBA()
            fg.parse(profile["foreground"])
            bg = Gdk.RGBA()
            bg.parse(profile["background"])
            cursor = Gdk.RGBA()
            cursor.parse(profile.get("cursor_color", profile["foreground"]))
            hl_bg = Gdk.RGBA()
            hl_bg.parse(profile.get("highlight_background", "#4A90E2"))
            hl_fg = Gdk.RGBA()
            hl_fg.parse(profile.get("highlight_foreground", profile["foreground"]))

            palette = []
            for color_hex in profile.get("palette", []):
                rgba = Gdk.RGBA()
                if rgba.parse(color_hex):
                    palette.append(rgba)
            palette = palette[:16] or None

            self.vte.set_colors(fg, bg, palette)
            self.vte.set_color_cursor(cursor)
            self.vte.set_color_highlight(hl_bg)
            self.vte.set_color_highlight_foreground(hl_fg)
            self.vte.set_font(Pango.FontDescription.from_string(profile["font"]))
            self.vte.queue_draw()
        except Exception:
            logger.error("Failed to apply terminal theme", exc_info=True)

    # -- shell -------------------------------------------------------------

    def spawn(self) -> None:
        """Spawn the user's interactive login shell in a fresh PTY."""
        shell = _resolve_shell()
        env = os.environ.copy()
        env["SHELL"] = shell
        if env.get("TERM", "").lower() in ("", "dumb"):
            env["TERM"] = "xterm-256color"
        try:
            pw = pwd.getpwuid(os.getuid())
            env.setdefault("USER", pw.pw_name)
            env.setdefault("LOGNAME", pw.pw_name)
            env.setdefault("HOME", pw.pw_dir)
        except (KeyError, AttributeError):
            env.setdefault("HOME", os.path.expanduser("~"))

        env_list = [f"{k}={v}" for k, v in env.items()]

        # Set the PTY size before spawning to avoid an early SIGWINCH.
        try:
            pty = Vte.Pty.new_sync(Vte.PtyFlags.DEFAULT)
            rows, cols = self.vte.get_row_count(), self.vte.get_column_count()
            if rows > 0 and cols > 0 and (rows, cols) != (24, 80):
                pty.set_size(rows, cols)
            self.vte.set_pty(pty)
        except Exception:
            logger.debug("Could not pre-create PTY", exc_info=True)

        self.vte.spawn_async(
            Vte.PtyFlags.DEFAULT,
            os.path.expanduser("~") or "/",
            [shell, "-i"],
            env_list,
            GLib.SpawnFlags.DEFAULT,
            None,
            None,
            -1,
            None,
            self._on_spawned,
            (),
        )

    def _on_spawned(self, _terminal, pid, error, _user_data) -> None:
        if error is not None:
            logger.error("Failed to spawn shell: %s", error)

    # -- helpers used by the sidebar / window ------------------------------

    def feed_child(self, data: bytes) -> None:
        self.vte.feed_child(data)

    def copy_clipboard(self) -> None:
        self.vte.copy_clipboard_format(Vte.Format.TEXT)

    def paste_clipboard(self) -> None:
        self.vte.paste_clipboard()

    def grab_focus(self) -> bool:
        return self.vte.grab_focus()

    def connect_child_exited(self, callback) -> int:
        return self.vte.connect("child-exited", callback)

    def connect_title_changed(self, callback) -> int:
        return self.vte.connect("window-title-changed", callback)

    @property
    def title(self) -> str:
        return self.vte.get_window_title() or ""
