"""Main window: a tabbed terminal area beside the command sidebar."""

from __future__ import annotations

import logging

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk  # noqa: E402

from .commands.panel import CommandSidebar
from .commands.store import CommandStore
from .terminal import TerminalWidget

logger = logging.getLogger(__name__)


class MainWindow(Adw.ApplicationWindow):
    """Adw.OverlaySplitView with the terminal tabs as content and the command
    sidebar on the trailing edge."""

    def __init__(self, application: Adw.Application, config) -> None:
        super().__init__(application=application)
        self.config = config
        self.store = CommandStore(config)

        self.set_title("Commando")
        self.set_default_size(1000, 640)

        self._build_ui()
        self.new_tab()

    # -- UI ----------------------------------------------------------------

    def _build_ui(self) -> None:
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        self.split_view = Adw.OverlaySplitView()
        self.split_view.set_sidebar_position(Gtk.PackType.END)
        self.split_view.set_max_sidebar_width(420)
        self.split_view.set_sidebar_width_fraction(0.32)
        self.toast_overlay.set_child(self.split_view)

        # --- content: header + tab bar + tab view ---
        self.tab_view = Adw.TabView()
        self.tab_view.set_hexpand(True)
        self.tab_view.set_vexpand(True)
        self.tab_view.connect("close-page", self._on_close_page)
        self.tab_view.connect("notify::selected-page", self._on_selected_page)

        header = Adw.HeaderBar()
        new_tab_btn = Gtk.Button(icon_name="tab-new-symbolic")
        new_tab_btn.set_tooltip_text("New tab (Ctrl+Shift+T)")
        new_tab_btn.connect("clicked", lambda _b: self.new_tab())
        header.pack_start(new_tab_btn)

        self._sidebar_btn = Gtk.ToggleButton(icon_name="view-sidebar-end-symbolic")
        self._sidebar_btn.set_tooltip_text("Toggle commands (F9)")
        self._sidebar_btn.set_active(True)
        self._sidebar_btn.connect("toggled",
                                  lambda b: self.split_view.set_show_sidebar(b.get_active()))
        header.pack_end(self._sidebar_btn)

        tab_bar = Adw.TabBar()
        tab_bar.set_view(self.tab_view)
        tab_bar.set_autohide(False)

        content = Adw.ToolbarView()
        content.add_top_bar(header)
        content.add_top_bar(tab_bar)
        content.set_content(self.tab_view)
        self.split_view.set_content(content)

        # --- sidebar: command panel ---
        self.sidebar = CommandSidebar(self, self.store)
        self.split_view.set_sidebar(self.sidebar)
        self.split_view.set_show_sidebar(True)

        # Keep the toggle button in sync if the split view collapses on its own.
        self.split_view.connect("notify::show-sidebar",
                                lambda *_a: self._sidebar_btn.set_active(
                                    self.split_view.get_show_sidebar()))

    # -- tabs --------------------------------------------------------------

    def new_tab(self) -> None:
        terminal = TerminalWidget(self.config)
        page = self.tab_view.append(terminal)
        page.set_title("Terminal")
        page.set_icon(Gio.ThemedIcon.new("utilities-terminal-symbolic"))

        terminal.connect_title_changed(
            lambda vte, p=page: p.set_title(vte.get_window_title() or "Terminal"))
        terminal.connect_child_exited(
            lambda _vte, _status, t=terminal: self._close_terminal(t))

        terminal.spawn()
        self.tab_view.set_selected_page(page)
        terminal.grab_focus()

    def close_current_tab(self) -> None:
        page = self.tab_view.get_selected_page()
        if page is not None:
            self.tab_view.close_page(page)

    def _close_terminal(self, terminal: TerminalWidget) -> None:
        page = self.tab_view.get_page(terminal)
        if page is not None:
            self.tab_view.close_page(page)

    def _on_close_page(self, tab_view: Adw.TabView, page: Adw.TabPage) -> bool:
        tab_view.close_page_finish(page, True)
        if tab_view.get_n_pages() == 0:
            self.close()
        return True  # we handled the close

    def _on_selected_page(self, *_args) -> None:
        terminal = self.get_active_terminal()
        if terminal is not None:
            terminal.grab_focus()

    # -- seam used by the sidebar -----------------------------------------

    def get_active_terminal(self) -> TerminalWidget | None:
        page = self.tab_view.get_selected_page()
        if page is None:
            return None
        child = page.get_child()
        return child if isinstance(child, TerminalWidget) else None

    def toast(self, message: str, timeout: int = 3) -> None:
        toast = Adw.Toast.new(message)
        toast.set_timeout(timeout)
        self.toast_overlay.add_toast(toast)

    def set_sidebar_visible(self, visible: bool) -> None:
        self.split_view.set_show_sidebar(visible)

    def toggle_sidebar(self) -> None:
        self.set_sidebar_visible(not self.split_view.get_show_sidebar())

    # -- clipboard (wired to app actions) ----------------------------------

    def copy_active(self) -> None:
        terminal = self.get_active_terminal()
        if terminal is not None:
            terminal.copy_clipboard()

    def paste_active(self) -> None:
        terminal = self.get_active_terminal()
        if terminal is not None:
            terminal.paste_clipboard()
