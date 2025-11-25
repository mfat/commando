"""
Speed dial widget for quick command execution.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib

from commando.logger import get_logger

logger = get_logger(__name__)


class SpeedDial(Gtk.Revealer):
    """Speed dial entry for quick command execution."""
    
    def __init__(self, main_view=None):
        """Initialize speed dial."""
        super().__init__()
        self.main_view = main_view
        self.current_number = ""
        
        # Entry box
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_start(24)
        box.set_margin_end(24)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.add_css_class("speed-dial")
        
        # Entry
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Type command number and press Enter...")
        self.entry.set_hexpand(True)
        self.entry.connect("activate", self._on_activate)
        self.entry.connect("changed", self._on_changed)
        box.append(self.entry)
        
        # Label showing command preview
        self.preview_label = Gtk.Label()
        self.preview_label.set_halign(Gtk.Align.START)
        self.preview_label.add_css_class("caption")
        self.preview_label.add_css_class("dim-label")
        box.append(self.preview_label)
        
        self.set_child(box)
        self.set_reveal_child(False)
        self.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        # Don't take up space when hidden
        self.set_vexpand(False)
        self.set_hexpand(False)
    
    def _show_speed_dial(self, *args):
        """Show the speed dial."""
        self.set_reveal_child(True)
        self.entry.grab_focus()
        self.entry.set_text("")
        self.current_number = ""
        self.preview_label.set_text("")
    
    def _on_changed(self, entry):
        """Handle text changes."""
        if not self.main_view:
            return
        text = entry.get_text().strip()
        if text.isdigit():
            self.current_number = text
            # Update preview
            command = self.main_view.get_command_by_number(int(text))
            if command:
                self.preview_label.set_text(f"→ {command.title}: {command.command}")
            else:
                self.preview_label.set_text("Command not found")
        else:
            self.current_number = ""
            self.preview_label.set_text("")
    
    def _on_activate(self, entry):
        """Handle Enter key press."""
        if not self.main_view:
            return
        if self.current_number:
            number = int(self.current_number)
            command = self.main_view.get_command_by_number(number)
            if command:
                self.main_view.execute_command(command)
                self.set_reveal_child(False)
                self.entry.set_text("")
                self.current_number = ""
                self.preview_label.set_text("")
            else:
                logger.warning(f"Command #{number} not found")
        else:
            self.set_reveal_child(False)

