"""
Command card widget.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gdk, GLib

from commando.models.command import Command
from commando.logger import get_logger

logger = get_logger(__name__)


class CommandCard(Gtk.Button):
    """A card widget representing a command (Bazaar-style)."""
    
    # Color mapping
    COLORS = {
        "blue": "#3584e4",
        "green": "#2ec27e",
        "yellow": "#e5a50a",
        "orange": "#ff7800",
        "red": "#e01b24",
        "purple": "#9141ac",
        "pink": "#c061cb",
        "brown": "#986a44",
        "gray": "#626880",
    }
    
    def __init__(self, command: Command, on_click=None, on_double_click=None, main_view=None):
        """Initialize the card."""
        super().__init__()
        self.command = command
        self.on_click = on_click
        self.on_double_click = on_double_click
        self.main_view = main_view
        
        # Add card CSS classes for Bazaar-style design (exactly like Bazaar)
        self.add_css_class("card")
        self.add_css_class("app-tile")
        
        # Set fixed size for uniform cards (Bazaar-style)
        self.set_size_request(280, -1)  # Fixed width, flexible height
        
        # Main content box - Bazaar-style horizontal layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        main_box.set_can_focus(False)  # Prevent focus on inner box
        
        # Icon - Bazaar uses 64px icons
        icon = Gtk.Image.new_from_icon_name(self.command.icon)
        icon.set_pixel_size(64)
        icon.add_css_class("icon-dropshadow")
        main_box.append(icon)
        
        # Text content box
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        text_box.set_valign(Gtk.Align.CENTER)
        text_box.set_hexpand(True)
        
        # Title row with number
        title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        title_row.set_margin_end(12)
        
        # Title label (Bazaar-style heading)
        title_label = Gtk.Label(label=self.command.title)
        title_label.set_xalign(0.0)
        title_label.set_ellipsize(3)  # END ellipsize
        title_label.set_max_width_chars(18)
        title_label.add_css_class("heading")
        title_row.append(title_label)
        
        # Number badge (small)
        number_label = Gtk.Label(label=f"#{self.command.number}")
        number_label.add_css_class("caption")
        number_label.add_css_class("dim-label")
        title_row.append(number_label)
        
        text_box.append(title_row)
        
        # Description/Command preview (Bazaar-style - 2 lines max)
        if self.command.command:
            desc_label = Gtk.Label(label=self.command.command)
            desc_label.set_xalign(0.0)
            desc_label.set_yalign(0.0)
            desc_label.set_wrap(True)
            desc_label.set_ellipsize(3)  # END ellipsize
            desc_label.set_vexpand(True)
            desc_label.set_lines(2)
            desc_label.set_max_width_chars(15)
            desc_label.set_single_line_mode(False)
            text_box.append(desc_label)
        elif self.command.description:
            desc_label = Gtk.Label(label=self.command.description)
            desc_label.set_xalign(0.0)
            desc_label.set_yalign(0.0)
            desc_label.set_wrap(True)
            desc_label.set_ellipsize(3)
            desc_label.set_vexpand(True)
            desc_label.set_lines(2)
            desc_label.set_max_width_chars(15)
            desc_label.set_single_line_mode(False)
            text_box.append(desc_label)
        
        main_box.append(text_box)
        
        # Set the main box as button child
        self.set_child(main_box)
        
        # Store main_box reference
        self.main_box = main_box
        
        # Connect button click
        self.connect("clicked", self._on_button_clicked)
        
        # Double-click gesture
        double_click = Gtk.GestureClick()
        double_click.set_button(1)  # Left button
        double_click.connect("pressed", self._on_double_click)
        self.add_controller(double_click)
        
        # Right-click menu
        right_click = Gtk.GestureClick(button=3)
        right_click.connect("pressed", self._on_right_click)
        self.add_controller(right_click)
        
        # Keyboard navigation
        self.set_focusable(True)
        self.set_can_focus(True)
    
    def _on_button_clicked(self, button):
        """Handle button click."""
        if self.on_click:
            self.on_click(self.command)
    
    def _on_double_click(self, gesture, n_press, x, y):
        """Handle double-click."""
        if n_press == 2 and self.on_double_click:
            self.on_double_click(self.command)
    
    
    def _on_right_click(self, gesture, n_press, x, y):
        """Handle right-click to show context menu."""
        if n_press == 1:
            self._show_context_menu(gesture, x, y)
    
    def _show_context_menu(self, gesture, x, y):
        """Show context menu for editing."""
        if not self.main_view:
            return
        
        # Create a simple popover menu
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)
        
        edit_btn = Gtk.Button(label="Edit")
        edit_btn.connect("clicked", lambda _: self._on_edit_clicked())
        box.append(edit_btn)
        
        delete_btn = Gtk.Button(label="Delete")
        delete_btn.connect("clicked", lambda _: self._on_delete_clicked())
        box.append(delete_btn)
        
        popover = Gtk.Popover()
        popover.set_child(box)
        popover.set_parent(self)
        popover.set_pointing_to(Gdk.Rectangle(x=x, y=y, width=1, height=1))
        popover.popup()
    
    def _on_edit_clicked(self):
        """Handle edit button click."""
        from commando.dialogs.card_editor import CardEditorDialog
        from gi.repository import Gtk
        
        # Get the parent window for modal dialog
        parent = self.get_root()
        dialog = CardEditorDialog(self.command, parent=parent if isinstance(parent, Gtk.Window) else None)
        dialog.set_saved_callback(lambda cmd: self.main_view._on_command_saved(dialog, cmd))
        
        # Present dialog - Adw.Dialog is modal by default when presented
        dialog.present()
    
    def _on_delete_clicked(self):
        """Handle delete button click."""
        from gi.repository import Adw
        dialog = Adw.MessageDialog(
            heading="Delete Command?",
            body=f"Are you sure you want to delete '{self.command.title}'?",
            parent=self.get_root()
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self._on_delete_response)
        dialog.present()
    
    def _on_delete_response(self, dialog, response):
        """Handle delete dialog response."""
        if response == "delete":
            self.main_view.storage.delete(self.command.number)
            self.main_view._load_commands()
        # Adw.Dialog uses close() instead of destroy()
        dialog.close()
    
    def update_command(self, command: Command):
        """Update the card with a new command."""
        self.command = command
        # Rebuild the card
        # For simplicity, we'll just update the visible elements
        # In a full implementation, you'd rebuild the entire card
        logger.debug(f"Card updated for command #{command.number}")

