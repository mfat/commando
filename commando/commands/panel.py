"""The command sidebar widget.

A folder/favorites tree of command snippets with live search, keyboard
navigation, add/edit/duplicate/delete, and ``${VAR}`` placeholder support.
Sends commands to the host window's active terminal through a tiny seam:
``window.get_active_terminal()``, ``window.toast()`` and
``window.set_sidebar_visible()``.
"""

from __future__ import annotations

import logging

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, GObject, Gtk, Pango  # noqa: E402

from .dialogs import AddFolderDialog, CommandEditDialog, PlaceholderDialog
from .store import CommandStore

logger = logging.getLogger(__name__)

_FOLDER_INDENT_PX = 24


# ---------------------------------------------------------------------------
# Row widgets
# ---------------------------------------------------------------------------

class FavoritesRow(Gtk.ListBoxRow):
    """Virtual 'Favorites' header — always first, unremovable."""

    __gsignals__ = {
        "folder-toggled": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    def __init__(self, cmd_count: int) -> None:
        super().__init__()
        self._expanded = True
        self.set_selectable(True)
        self.set_child(_header_box(
            "starred-symbolic", "Favorites", cmd_count, self._on_expand))
        self._expand_btn = self.get_child().expand_btn  # type: ignore[attr-defined]
        _add_click(self, self._on_click)

    def _on_click(self, _g, n_press, _x, _y) -> None:
        parent = self.get_parent()
        if parent and n_press == 1:
            parent.select_row(self)
        elif n_press == 2:
            self._toggle()

    def _on_expand(self, _btn) -> None:
        self._toggle()

    def _toggle(self) -> None:
        self._expanded = not self._expanded
        self._expand_btn.set_icon_name(
            "pan-down-symbolic" if self._expanded else "pan-end-symbolic")
        self.emit("folder-toggled", self._expanded)

    # Allow the panel to expand/collapse via Enter.
    def _toggle_expand(self) -> None:
        self._toggle()


class FolderRow(Gtk.ListBoxRow):
    """A folder header row."""

    __gsignals__ = {
        "folder-toggled": (GObject.SignalFlags.RUN_FIRST, None, (str, bool)),
    }

    def __init__(self, folder: dict, cmd_count: int) -> None:
        super().__init__()
        self.folder_id = folder["id"]
        self._folder = folder
        self.set_selectable(True)
        box = _header_box("folder-symbolic", folder.get("name", ""),
                          cmd_count, self._on_expand)
        self._expand_btn = box.expand_btn  # type: ignore[attr-defined]
        self._update_icon()
        self.set_child(box)
        _add_click(self, self._on_click)

    def _on_click(self, _g, n_press, _x, _y) -> None:
        parent = self.get_parent()
        if parent and n_press == 1:
            parent.select_row(self)
        elif n_press == 2:
            self._toggle()

    def _update_icon(self) -> None:
        self._expand_btn.set_icon_name(
            "pan-down-symbolic" if self._folder.get("expanded", True)
            else "pan-end-symbolic")

    def _on_expand(self, _btn) -> None:
        self._toggle()

    def _toggle(self) -> None:
        expanded = not self._folder.get("expanded", True)
        self._folder["expanded"] = expanded
        self._update_icon()
        self.emit("folder-toggled", self.folder_id, expanded)

    def _toggle_expand(self) -> None:
        self._toggle()


class CommandRow(Gtk.ListBoxRow):
    """A single command snippet row with a favourite toggle."""

    def __init__(self, cmd: dict, indent: bool = False) -> None:
        super().__init__()
        self._cmd_data = cmd
        self.set_selectable(True)

        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        content.set_margin_start(12 + (_FOLDER_INDENT_PX if indent else 0))
        content.set_margin_end(12)
        content.set_margin_top(6)
        content.set_margin_bottom(6)

        icon = Gtk.Image.new_from_icon_name("utilities-terminal-symbolic")
        icon.set_pixel_size(16)
        icon.set_valign(Gtk.Align.CENTER)
        content.append(icon)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info.set_hexpand(True)
        info.set_valign(Gtk.Align.CENTER)
        info.append(_ellipsized(cmd.get("name", "")))
        subtitle = cmd.get("description") or cmd.get("command", "")[:60]
        if subtitle:
            info.append(_ellipsized(subtitle, dim=True))
        content.append(info)

        self._star_btn = Gtk.ToggleButton()
        self._star_btn.set_icon_name(
            "starred-symbolic" if cmd.get("is_favorite") else "non-starred-symbolic")
        self._star_btn.set_active(bool(cmd.get("is_favorite")))
        self._star_btn.add_css_class("flat")
        self._star_btn.set_valign(Gtk.Align.CENTER)
        self._star_btn.set_tooltip_text("Toggle favorite")
        content.append(self._star_btn)

        self.set_child(content)


def _ellipsized(text: str, dim: bool = False) -> Gtk.Label:
    label = Gtk.Label(label=text)
    label.set_halign(Gtk.Align.START)
    label.set_xalign(0)
    label.set_hexpand(True)
    label.set_ellipsize(Pango.EllipsizeMode.END)
    if dim:
        label.add_css_class("dim-label")
    return label


def _header_box(icon_name: str, title: str, count: int, on_expand) -> Gtk.Box:
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    box.set_margin_start(12)
    box.set_margin_end(12)
    box.set_margin_top(6)
    box.set_margin_bottom(6)

    icon = Gtk.Image.new_from_icon_name(icon_name)
    icon.set_pixel_size(16)
    icon.set_valign(Gtk.Align.CENTER)
    box.append(icon)

    info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    info.set_hexpand(True)
    info.set_valign(Gtk.Align.CENTER)
    info.append(_ellipsized(title))
    info.append(_ellipsized(
        "1 command" if count == 1 else f"{count} commands", dim=True))
    box.append(info)

    expand = Gtk.Button(icon_name="pan-down-symbolic")
    expand.add_css_class("flat")
    expand.set_can_focus(False)
    expand.connect("clicked", on_expand)
    box.append(expand)
    box.expand_btn = expand  # type: ignore[attr-defined]
    return box


def _add_click(widget: Gtk.Widget, handler) -> None:
    gesture = Gtk.GestureClick()
    gesture.set_button(1)
    gesture.connect("pressed", handler)
    widget.add_controller(gesture)


# ---------------------------------------------------------------------------
# CommandSidebar
# ---------------------------------------------------------------------------

class CommandSidebar(Gtk.Box):
    """The right-hand command panel."""

    def __init__(self, window, store: CommandStore) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.window = window
        self.store = store
        self._search_query = ""
        self._favorites_expanded = True
        self._build_ui()
        self.refresh()

    # -- UI ----------------------------------------------------------------

    def _build_ui(self) -> None:
        self.add_css_class("sidebar")

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        header.set_margin_start(8)
        header.set_margin_end(8)
        header.set_margin_top(8)
        header.set_margin_bottom(4)

        title = Gtk.Label(label="Commands")
        title.add_css_class("heading")
        title.set_hexpand(True)
        title.set_xalign(0)
        header.append(title)

        for icon, tooltip, cb in (
            ("list-add-symbolic", "Add command", lambda _b: self._open_edit_dialog(None)),
            ("folder-new-symbolic", "New folder", lambda _b: self._open_add_folder_dialog()),
        ):
            btn = Gtk.Button(icon_name=icon)
            btn.add_css_class("flat")
            btn.set_tooltip_text(tooltip)
            btn.connect("clicked", cb)
            header.append(btn)

        self._search_toggle = Gtk.ToggleButton(icon_name="system-search-symbolic")
        self._search_toggle.add_css_class("flat")
        self._search_toggle.set_tooltip_text("Search commands")
        self._search_toggle.connect("toggled", self._on_search_toggle)
        header.append(self._search_toggle)
        self.append(header)

        self._search_revealer = Gtk.Revealer()
        self._search_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_margin_start(8)
        self._search_entry.set_margin_end(8)
        self._search_entry.set_margin_top(4)
        self._search_entry.set_margin_bottom(4)
        self._search_entry.connect("search-changed", self._on_search_changed)
        self._search_revealer.set_child(self._search_entry)
        self.append(self._search_revealer)

        self.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        self._stack = Gtk.Stack()
        self._stack.set_vexpand(True)
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.append(self._stack)

        self._tree_list = self._make_list()
        self._stack.add_named(_scrolled(self._tree_list), "tree")
        self._search_list = self._make_list()
        self._stack.add_named(_scrolled(self._search_list), "search")
        self._stack.add_named(self._make_empty(), "empty")

        panel_key = Gtk.EventControllerKey()
        panel_key.connect("key-pressed", self._on_panel_key)
        self.add_controller(panel_key)

    def _make_list(self) -> Gtk.ListBox:
        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        listbox.set_activate_on_single_click(False)
        listbox.add_css_class("navigation-sidebar")
        listbox.set_show_separators(False)
        key = Gtk.EventControllerKey()
        key.connect("key-pressed", self._on_list_key)
        listbox.add_controller(key)
        return listbox

    @staticmethod
    def _make_empty() -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        box.set_vexpand(True)
        icon = Gtk.Image.new_from_icon_name("utilities-terminal-symbolic")
        icon.set_pixel_size(48)
        icon.add_css_class("dim-label")
        box.append(icon)
        label = Gtk.Label(label="No commands yet.\nClick + to add one.")
        label.set_justify(Gtk.Justification.CENTER)
        label.add_css_class("dim-label")
        box.append(label)
        return box

    # -- refresh / tree ----------------------------------------------------

    def refresh(self) -> None:
        _clear(self._tree_list)

        commands = self.store.get_commands()
        if not commands:
            self._stack.set_visible_child_name("empty")
            return
        if self._search_query:
            self._show_search_results(self._search_query)
            return

        self._stack.set_visible_child_name("tree")

        by_folder: dict[str | None, list[dict]] = {}
        for cmd in commands:
            by_folder.setdefault(cmd.get("folder_id"), []).append(cmd)

        favorites = self.store.get_favorites()
        if favorites:
            fav_row = FavoritesRow(len(favorites))
            fav_row.connect("folder-toggled", self._on_favorites_toggled)
            self._tree_list.append(fav_row)
            if self._favorites_expanded:
                for cmd in favorites:
                    self._tree_list.append(self._build_command_row(cmd, indent=True))

        for cmd in by_folder.get(None, []):
            self._tree_list.append(self._build_command_row(cmd))

        for folder in sorted(self.store.get_folders(), key=lambda f: f.get("order", 0)):
            folder_cmds = by_folder.get(folder["id"], [])
            folder_row = FolderRow(folder, len(folder_cmds))
            folder_row.connect("folder-toggled", self._on_folder_toggled)
            self._tree_list.append(folder_row)
            if folder.get("expanded", True):
                for cmd in folder_cmds:
                    self._tree_list.append(self._build_command_row(cmd, indent=True))

    def _on_favorites_toggled(self, _row: FavoritesRow, expanded: bool) -> None:
        self._favorites_expanded = expanded
        self.refresh()

    def _on_folder_toggled(self, _row: FolderRow, folder_id: str, expanded: bool) -> None:
        self.store.update_folder(folder_id, expanded=expanded)
        self.refresh()

    def _build_command_row(self, cmd: dict, indent: bool = False) -> CommandRow:
        row = CommandRow(cmd, indent=indent)

        def on_star(btn, c=cmd):
            self._toggle_favorite(c)
            btn.set_icon_name(
                "starred-symbolic" if c.get("is_favorite") else "non-starred-symbolic")
        row._star_btn.connect("toggled", on_star)

        dbl = Gtk.GestureClick()
        dbl.set_button(1)
        dbl.connect("pressed", lambda _g, n, x, y, c=cmd: self._on_row_click(n, c))
        row.add_controller(dbl)

        right = Gtk.GestureClick()
        right.set_button(3)
        right.connect("pressed",
                      lambda _g, n, x, y, r=row, c=cmd: self._show_context_menu(r, c, x, y))
        row.add_controller(right)
        return row

    # -- search ------------------------------------------------------------

    def _on_search_toggle(self, btn: Gtk.ToggleButton) -> None:
        revealed = btn.get_active()
        self._search_revealer.set_reveal_child(revealed)
        if revealed:
            self._search_entry.grab_focus()
        else:
            self._search_entry.set_text("")
            self._search_query = ""
            self.refresh()

    def _on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        self._search_query = entry.get_text().strip()
        if self._search_query:
            self._show_search_results(self._search_query)
        else:
            self.refresh()

    def _show_search_results(self, query: str) -> None:
        _clear(self._search_list)
        results = self.store.search(query)
        if not results:
            label = Gtk.Label(label="No results")
            label.add_css_class("dim-label")
            label.set_margin_top(24)
            self._search_list.append(label)
        else:
            for cmd in results:
                self._search_list.append(self._build_command_row(cmd))
        self._stack.set_visible_child_name("search")

    def focus_search(self) -> None:
        self._search_toggle.set_active(True)
        self._search_revealer.set_reveal_child(True)
        self._search_entry.grab_focus()

    # -- keyboard ----------------------------------------------------------

    def _on_panel_key(self, _ctrl, keyval, _keycode, _state) -> bool:
        if keyval == Gdk.KEY_slash:
            self.focus_search()
            return True
        return False

    def _on_list_key(self, _ctrl, keyval, _keycode, state) -> bool:
        mods = state & Gtk.accelerator_get_default_mod_mask()
        active = (self._search_list
                  if self._stack.get_visible_child_name() == "search"
                  else self._tree_list)
        selected = active.get_selected_row()
        cmd = getattr(selected, "_cmd_data", None) if selected else None

        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) and mods == 0:
            if cmd:
                self._send_command(cmd)
                return True
            if selected is not None and hasattr(selected, "_toggle_expand"):
                selected._toggle_expand()
                return True
        if keyval == Gdk.KEY_Delete and mods == 0 and cmd:
            self._delete_command(cmd)
            return True
        if keyval == Gdk.KEY_e and mods == Gdk.ModifierType.CONTROL_MASK and cmd:
            self._open_edit_dialog(cmd)
            return True
        return False

    def _on_row_click(self, n_press: int, cmd: dict) -> None:
        if n_press == 2:
            self._send_command(cmd)

    # -- context menu ------------------------------------------------------

    def _show_context_menu(self, row: Gtk.Widget, cmd: dict, x: float, y: float) -> None:
        popover = Gtk.Popover()
        popover.set_parent(row)
        popover.set_has_arrow(False)
        rect = Gdk.Rectangle()
        rect.x, rect.y, rect.width, rect.height = int(x), int(y), 1, 1
        popover.set_pointing_to(rect)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        fav_label = "Remove favorite" if cmd.get("is_favorite") else "Add favorite"
        for label, handler in (
            ("Edit", lambda: self._open_edit_dialog(cmd)),
            ("Duplicate", lambda: self._duplicate_command(cmd)),
            (fav_label, lambda: self._toggle_favorite(cmd)),
            ("Delete", lambda: self._delete_command(cmd)),
        ):
            btn = Gtk.Button(label=label)
            btn.add_css_class("flat")
            btn.set_halign(Gtk.Align.FILL)
            btn.get_child().set_xalign(0)
            if label == "Delete":
                btn.add_css_class("destructive-action")
            btn.connect("clicked", lambda _b, h=handler: (popover.popdown(), h()))
            box.append(btn)
        popover.set_child(box)
        popover.popup()

    # -- sending -----------------------------------------------------------

    def _send_command(self, cmd: dict) -> None:
        terminal = self.window.get_active_terminal()
        if terminal is None:
            self.window.toast("Open a terminal tab first")
            return
        if cmd.get("has_placeholders"):
            dlg = PlaceholderDialog(self.window, cmd)
            dlg.connect("send", lambda _d, filled: self._feed(filled, cmd.get("id")))
            dlg.present()
        else:
            self._feed(cmd.get("command", ""), cmd.get("id"))

    def _feed(self, text: str, cmd_id: str | None) -> None:
        terminal = self.window.get_active_terminal()
        if terminal is None:
            self.window.toast("Open a terminal tab first")
            return
        insert_only = bool(self.store._config.get_setting("terminal.insert_only", False))
        data = text.encode("utf-8") if insert_only else (text + "\n").encode("utf-8")
        try:
            terminal.feed_child(data)
        except Exception:
            logger.error("Failed to send command to terminal", exc_info=True)
            return
        terminal.grab_focus()
        if cmd_id:
            self.store.record_use(cmd_id)
        if self.store._config.get_setting("terminal.auto_hide_sidebar", False):
            GLib.idle_add(lambda: self.window.set_sidebar_visible(False))

    # -- actions -----------------------------------------------------------

    def _open_edit_dialog(self, cmd: dict | None) -> None:
        dlg = CommandEditDialog(self.window, self.store, cmd)
        dlg.connect("saved", lambda _d, _saved: self.refresh())
        dlg.present()

    def _open_add_folder_dialog(self) -> None:
        dlg = AddFolderDialog(self.window)
        dlg.connect("created", lambda _d, name: (self.store.add_folder(name), self.refresh()))
        dlg.present()

    def _delete_command(self, cmd: dict) -> None:
        self.store.delete_command(cmd["id"])
        self.refresh()

    def _duplicate_command(self, cmd: dict) -> None:
        self.store.duplicate_command(cmd["id"])
        self.refresh()

    def _toggle_favorite(self, cmd: dict) -> None:
        cmd["is_favorite"] = not cmd.get("is_favorite", False)
        self.store.update_command(cmd["id"], is_favorite=cmd["is_favorite"])
        self.refresh()


def _scrolled(child: Gtk.Widget) -> Gtk.ScrolledWindow:
    scr = Gtk.ScrolledWindow()
    scr.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scr.set_vexpand(True)
    scr.set_child(child)
    return scr


def _clear(listbox: Gtk.ListBox) -> None:
    while (child := listbox.get_first_child()) is not None:
        listbox.remove(child)
