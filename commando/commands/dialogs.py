"""Modal dialogs for the command sidebar: placeholders, edit, new folder."""

from __future__ import annotations

import re

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, GObject, Gtk  # noqa: E402

from .store import CommandStore

PLACEHOLDER_RE = re.compile(r"\$\{([^}]+)\}")


def parse_placeholders(command: str) -> list[str]:
    """Return the unique ``${VAR}`` names in *command*, in first-seen order."""
    seen: list[str] = []
    for var in PLACEHOLDER_RE.findall(command):
        if var not in seen:
            seen.append(var)
    return seen


class PlaceholderDialog(Adw.Window):
    """Fill in ``${VAR}`` placeholders before sending a command."""

    __gsignals__ = {
        "send": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self, parent: Gtk.Window, cmd: dict) -> None:
        super().__init__()
        self._cmd = cmd
        self._entries: dict[str, Adw.EntryRow] = {}
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_default_size(420, -1)
        self.set_title("Fill Placeholders")
        self._build_ui()

    def _build_ui(self) -> None:
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(root)

        header = Adw.HeaderBar()
        cancel = Gtk.Button(label="Cancel")
        cancel.connect("clicked", lambda _b: self.close())
        header.pack_start(cancel)
        send = Gtk.Button(label="Send")
        send.add_css_class("suggested-action")
        send.connect("clicked", self._on_confirm)
        header.pack_end(send)
        root.append(header)

        key = Gtk.EventControllerKey()
        key.connect("key-pressed", self._on_key)
        self.add_controller(key)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        body.set_margin_start(16)
        body.set_margin_end(16)
        body.set_margin_top(12)
        body.set_margin_bottom(16)
        root.append(body)

        title = Gtk.Label()
        title.set_markup(f'<b>{GLib.markup_escape_text(self._cmd.get("name", ""))}</b>')
        title.set_xalign(0)
        body.append(title)

        group = Adw.PreferencesGroup()
        for var in parse_placeholders(self._cmd.get("command", "")):
            row = Adw.EntryRow(title=f"${{{var}}}")
            row.connect("entry-activated", self._on_confirm)
            row.connect("notify::text", lambda *_a: self._update_preview())
            self._entries[var] = row
            group.add(row)
        body.append(group)

        self._preview = Gtk.Label(label=self._cmd.get("command", ""))
        self._preview.set_xalign(0)
        self._preview.set_wrap(True)
        self._preview.add_css_class("monospace")
        self._preview.add_css_class("dim-label")
        body.append(self._preview)

    def _substitute(self, fallback_to_var: bool) -> str:
        result = self._cmd.get("command", "")
        for var, entry in self._entries.items():
            text = entry.get_text()
            if not text and fallback_to_var:
                text = f"${{{var}}}"
            result = result.replace(f"${{{var}}}", text)
        return result

    def _update_preview(self) -> None:
        self._preview.set_text(self._substitute(fallback_to_var=True))

    def _on_key(self, _ctrl, keyval, _keycode, _state) -> bool:
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False

    def _on_confirm(self, *_a) -> None:
        self.emit("send", self._substitute(fallback_to_var=False))
        self.close()


class CommandEditDialog(Adw.Window):
    """Create or edit a command snippet."""

    __gsignals__ = {
        "saved": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self, parent: Gtk.Window, store: CommandStore,
                 cmd: dict | None = None) -> None:
        super().__init__()
        self._store = store
        self._cmd = cmd
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_default_size(520, 580)
        self.set_title("Edit Command" if cmd else "New Command")
        self._build_ui()

    def _build_ui(self) -> None:
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(root)

        header = Adw.HeaderBar()
        cancel = Gtk.Button(label="Cancel")
        cancel.connect("clicked", lambda _b: self.close())
        header.pack_start(cancel)
        save = Gtk.Button(label="Save")
        save.add_css_class("suggested-action")
        save.connect("clicked", self._on_save)
        header.pack_end(save)
        root.append(header)

        scr = Gtk.ScrolledWindow()
        scr.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scr.set_vexpand(True)
        root.append(scr)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        body.set_margin_start(16)
        body.set_margin_end(16)
        body.set_margin_top(12)
        body.set_margin_bottom(16)
        scr.set_child(body)

        details = Adw.PreferencesGroup(title="Command Details")
        body.append(details)

        self._name_row = Adw.EntryRow(title="Name *")
        self._desc_row = Adw.EntryRow(title="Description")
        self._tags_row = Adw.EntryRow(title="Tags (comma-separated)")
        details.add(self._name_row)
        details.add(self._desc_row)
        details.add(self._tags_row)

        folders = self._store.get_folders()
        self._folder_ids = [None] + [f["id"] for f in folders]
        model = Gtk.StringList()
        model.append("(No folder)")
        for f in folders:
            model.append(f["name"])
        self._folder_row = Adw.ComboRow(title="Folder")
        self._folder_row.set_model(model)
        details.add(self._folder_row)

        cmd_group = Adw.PreferencesGroup(title="Command *")
        body.append(cmd_group)
        frame = Gtk.Frame()
        frame.add_css_class("card")
        cmd_group.add(frame)
        self._cmd_view = Gtk.TextView()
        self._cmd_view.set_size_request(-1, 96)
        self._cmd_view.set_monospace(True)
        self._cmd_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        for setter in ("set_top_margin", "set_bottom_margin",
                       "set_left_margin", "set_right_margin"):
            getattr(self._cmd_view, setter)(8)
        frame.set_child(self._cmd_view)

        opts = Adw.PreferencesGroup(title="Options")
        body.append(opts)
        self._placeholder_row = Adw.SwitchRow(
            title="Has Placeholders", subtitle="Use ${VAR} syntax in command")
        self._favorite_row = Adw.SwitchRow(title="Favorite")
        opts.add(self._placeholder_row)
        opts.add(self._favorite_row)

        if self._cmd:
            self._populate(self._cmd)

    def _populate(self, cmd: dict) -> None:
        self._name_row.set_text(cmd.get("name", ""))
        self._desc_row.set_text(cmd.get("description", ""))
        self._tags_row.set_text(", ".join(cmd.get("tags", [])))
        self._cmd_view.get_buffer().set_text(cmd.get("command", ""))
        self._placeholder_row.set_active(cmd.get("has_placeholders", False))
        self._favorite_row.set_active(cmd.get("is_favorite", False))
        fid = cmd.get("folder_id")
        if fid in self._folder_ids:
            self._folder_row.set_selected(self._folder_ids.index(fid))

    def _on_save(self, *_a) -> None:
        name = self._name_row.get_text().strip()
        buf = self._cmd_view.get_buffer()
        command = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False).strip()
        if not name or not command:
            return

        tags_raw = self._tags_row.get_text().strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        idx = self._folder_row.get_selected()
        folder_id = self._folder_ids[idx] if 0 <= idx < len(self._folder_ids) else None

        fields = dict(
            description=self._desc_row.get_text().strip(),
            tags=tags,
            folder_id=folder_id,
            has_placeholders=self._placeholder_row.get_active(),
            is_favorite=self._favorite_row.get_active(),
        )
        if self._cmd:
            self._store.update_command(self._cmd["id"], name=name, command=command, **fields)
            saved = next((c for c in self._store.get_commands()
                          if c["id"] == self._cmd["id"]), None)
        else:
            saved = self._store.add_command(name, command, **fields)

        self.emit("saved", saved)
        self.close()


class AddFolderDialog(Adw.Window):
    """Name a new folder."""

    __gsignals__ = {
        "created": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self, parent: Gtk.Window) -> None:
        super().__init__()
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_default_size(360, -1)
        self.set_title("New Folder")
        self._build_ui()

    def _build_ui(self) -> None:
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(root)

        header = Adw.HeaderBar()
        cancel = Gtk.Button(label="Cancel")
        cancel.connect("clicked", lambda _b: self.close())
        header.pack_start(cancel)
        create = Gtk.Button(label="Create")
        create.add_css_class("suggested-action")
        create.connect("clicked", self._on_create)
        header.pack_end(create)
        root.append(header)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        body.set_margin_start(16)
        body.set_margin_end(16)
        body.set_margin_top(12)
        body.set_margin_bottom(16)
        root.append(body)

        group = Adw.PreferencesGroup()
        self._name_row = Adw.EntryRow(title="Folder Name")
        self._name_row.connect("entry-activated", self._on_create)
        group.add(self._name_row)
        body.append(group)

    def _on_create(self, *_a) -> None:
        name = self._name_row.get_text().strip()
        if name:
            self.emit("created", name)
            self.close()
