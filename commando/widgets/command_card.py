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


class CommandCard(Adw.Bin):
    """A card widget representing a command."""
    
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
        
        # Add card CSS class (like in the example)
        self.add_css_class("card")
        
        # Set margins
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        
        # Prevent expansion
        self.set_vexpand(False)
        self.set_hexpand(False)
        
        # Main content box - this will be the actual card content
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        # Prevent main box from expanding - CRITICAL
        main_box.set_vexpand(False)
        main_box.set_hexpand(False)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        
        # Header with icon and number
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        # Icon
        icon = Gtk.Image.new_from_icon_name(self.command.icon)
        icon.set_pixel_size(32)
        header_box.append(icon)
        
        # Title and number
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        title_label = Gtk.Label(label=self.command.title)
        title_label.set_halign(Gtk.Align.START)
        title_label.add_css_class("title-4")
        title_box.append(title_label)
        
        number_label = Gtk.Label(label=f"#{self.command.number}")
        number_label.set_halign(Gtk.Align.START)
        number_label.add_css_class("caption")
        number_label.add_css_class("dim-label")
        title_box.append(number_label)
        
        header_box.append(title_box)
        header_box.set_hexpand(True)
        
        main_box.append(header_box)
        
        # Command preview
        if self.command.command:
            cmd_label = Gtk.Label(label=self.command.command)
            cmd_label.set_halign(Gtk.Align.START)
            cmd_label.add_css_class("caption")
            cmd_label.add_css_class("monospace")
            cmd_label.set_wrap(True)
            cmd_label.set_max_width_chars(40)
            main_box.append(cmd_label)
        
        # Tag
        if self.command.tag:
            tag_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            tag_label = Gtk.Label(label=self.command.tag)
            tag_label.add_css_class("chip")
            tag_label.add_css_class("tag")
            tag_box.append(tag_label)
            tag_box.set_halign(Gtk.Align.START)
            main_box.append(tag_box)
        
        # Create card frame - this will contain the content
        self.frame = Gtk.Frame()
        # CRITICAL: Prevent frame from expanding
        self.frame.set_vexpand(False)
        self.frame.set_hexpand(False)
        
        # Set the main_box as the frame's child directly
        self.frame.set_child(main_box)
        
        # Set the frame as the Bin's child
        # CRITICAL: The Bin must not expand - it should size to its content
        self.set_vexpand(False)
        self.set_hexpand(False)
        self.set_child(self.frame)
        
        # Store main_box reference
        self.main_box = main_box
        
        # Apply color
        self._apply_color()
        
        # Hover effect using EventControllerMotion - attach to the card itself
        motion_controller = Gtk.EventControllerMotion()
        motion_controller.connect("enter", self._on_hover_enter)
        motion_controller.connect("leave", self._on_hover_leave)
        # Attach to the card Bin
        self.add_controller(motion_controller)
        
        # Gesture for clicks
        click_controller = Gtk.GestureClick()
        click_controller.connect("pressed", self._on_click)
        self.add_controller(click_controller)
        
        # Right-click menu
        right_click = Gtk.GestureClick(button=3)
        right_click.connect("pressed", self._on_right_click)
        self.add_controller(right_click)
        
        # Keyboard navigation
        self.set_focusable(True)
        self.set_can_focus(True)
    
    def _apply_color(self):
        """Apply color styling to the card."""
        color_hex = self.COLORS.get(self.command.color, self.COLORS["blue"])
        
        # Create a CSS provider for this card
        card_class = f"commando-card-{self.command.number}"
        
        # Apply border and hover to the card Bin itself
        css = f"""
        .{card_class} {{
            border-left: 4px solid {color_hex};
        }}
        .{card_class}.hover-active {{
            background: alpha(@theme_bg_color, 0.1);
        }}
        """
        
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        
        # Add custom class to the card Bin for border and hover
        self.add_css_class(card_class)
        
        # Apply the style to the card
        context = self.get_style_context()
        context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
    def _on_hover_enter(self, controller, x, y):
        """Handle mouse enter - apply hover class to card."""
        self.add_css_class("hover-active")
    
    def _on_hover_leave(self, controller):
        """Handle mouse leave - remove hover class from card."""
        self.remove_css_class("hover-active")
    
    def _on_click(self, gesture, n_press, x, y):
        """Handle click events."""
        if n_press == 1:
            if self.on_click:
                self.on_click(self.command)
        elif n_press == 2:
            if self.on_double_click:
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

