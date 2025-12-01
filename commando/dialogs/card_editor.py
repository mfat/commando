"""
Card editor dialog.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib

from commando.models.command import Command
from commando.logger import get_logger

logger = get_logger(__name__)


class CardEditorDialog(Adw.Window):
    """Dialog for editing command card properties."""
    
    # Available colors
    COLORS = [
        ("blue", "Blue"),
        ("green", "Green"),
        ("yellow", "Yellow"),
        ("orange", "Orange"),
        ("red", "Red"),
        ("purple", "Purple"),
        ("pink", "Pink"),
        ("brown", "Brown"),
        ("gray", "Gray"),
    ]
    
    def __init__(self, command: Command, parent=None, **kwargs):
        """Initialize the editor dialog.
        
        Args:
            command: Command to edit
            parent: Parent window (Gtk.Window) for modal dialog
        """
        super().__init__(**kwargs)
        self.command = command
        self.original_command = Command(**command.to_dict())
        self.saved_callback = None
        
        self.set_title("Edit Command")
        self.set_default_size(600, 700)
        self.set_modal(True)
        self.set_resizable(True)
        self.set_deletable(True)
        
        # Set parent window for proper centering
        if parent:
            self.set_transient_for(parent)
        
        # Create headerbar for draggable window
        # Adw.Window doesn't support set_titlebar(), so we add it to content
        headerbar = Adw.HeaderBar()
        headerbar.set_title_widget(Gtk.Label(label="Edit Command"))
        headerbar.set_show_end_title_buttons(True)
        headerbar.set_show_start_title_buttons(False)
        
        # Main box with proper spacing for dialog
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_start(24)
        main_box.set_margin_end(24)
        main_box.set_margin_top(24)
        main_box.set_margin_bottom(24)
        
        # Set reasonable width constraints for the dialog
        main_box.set_size_request(500, -1)  # Minimum width of 500px
        
        # Number
        number_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        number_label = Gtk.Label(label="Number:")
        number_label.set_halign(Gtk.Align.START)
        number_label.set_size_request(120, -1)  # set_min_width doesn't exist in GTK4
        number_box.append(number_label)
        
        self.number_entry = Gtk.SpinButton()
        self.number_entry.set_adjustment(Gtk.Adjustment(value=command.number, lower=1, upper=9999, step_increment=1))
        self.number_entry.set_numeric(True)
        number_box.append(self.number_entry)
        main_box.append(number_box)
        
        # Title
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        title_label = Gtk.Label(label="Title:")
        title_label.set_halign(Gtk.Align.START)
        title_label.set_size_request(120, -1)
        title_box.append(title_label)
        
        self.title_entry = Gtk.Entry()
        self.title_entry.set_text(command.title)
        self.title_entry.set_hexpand(True)
        title_box.append(self.title_entry)
        main_box.append(title_box)
        
        # Command
        cmd_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        cmd_label = Gtk.Label(label="Command:")
        cmd_label.set_halign(Gtk.Align.START)
        cmd_box.append(cmd_label)
        
        self.command_text = Gtk.TextView()
        self.command_text.set_wrap_mode(Gtk.WrapMode.WORD)
        buffer = self.command_text.get_buffer()
        buffer.set_text(command.command)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(100)
        scrolled.set_child(self.command_text)
        cmd_box.append(scrolled)
        main_box.append(cmd_box)
        
        # Icon
        icon_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        icon_label = Gtk.Label(label="Icon:")
        icon_label.set_halign(Gtk.Align.START)
        icon_label.set_size_request(120, -1)
        icon_box.append(icon_label)
        
        self.icon_entry = Gtk.Entry()
        self.icon_entry.set_text(command.icon)
        self.icon_entry.set_placeholder_text("icon-name-symbolic")
        self.icon_entry.set_hexpand(True)
        icon_box.append(self.icon_entry)
        main_box.append(icon_box)
        
        # Color
        color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        color_label = Gtk.Label(label="Color:")
        color_label.set_halign(Gtk.Align.START)
        color_label.set_size_request(120, -1)
        color_box.append(color_label)
        
        self.color_combo = Gtk.ComboBoxText()
        for color_id, color_name in self.COLORS:
            self.color_combo.append(color_id, color_name)
        self.color_combo.set_active_id(command.color)
        color_box.append(self.color_combo)
        main_box.append(color_box)
        
        # Tag
        tag_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        tag_label = Gtk.Label(label="Tag:")
        tag_label.set_halign(Gtk.Align.START)
        tag_label.set_size_request(120, -1)
        tag_box.append(tag_label)
        
        self.tag_entry = Gtk.Entry()
        self.tag_entry.set_text(command.tag)
        self.tag_entry.set_hexpand(True)
        tag_box.append(self.tag_entry)
        main_box.append(tag_box)
        
        # Category
        category_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        category_label = Gtk.Label(label="Category:")
        category_label.set_halign(Gtk.Align.START)
        category_label.set_size_request(120, -1)
        category_box.append(category_label)
        
        self.category_entry = Gtk.Entry()
        self.category_entry.set_text(command.category)
        self.category_entry.set_hexpand(True)
        category_box.append(self.category_entry)
        main_box.append(category_box)
        
        # Description
        desc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        desc_label = Gtk.Label(label="Description:")
        desc_label.set_halign(Gtk.Align.START)
        desc_box.append(desc_label)
        
        self.desc_text = Gtk.TextView()
        self.desc_text.set_wrap_mode(Gtk.WrapMode.WORD)
        buffer = self.desc_text.get_buffer()
        buffer.set_text(command.description)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(80)
        scrolled.set_child(self.desc_text)
        desc_box.append(scrolled)
        main_box.append(desc_box)
        
        # Run mode
        run_mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        run_mode_label = Gtk.Label(label="Run Mode:")
        run_mode_label.set_halign(Gtk.Align.START)
        run_mode_label.set_size_request(120, -1)
        run_mode_box.append(run_mode_label)
        
        self.run_mode_combo = Gtk.ComboBoxText()
        self.run_mode_combo.append("1", "Execute command")
        self.run_mode_combo.append("2", "Type command (user runs manually)")
        run_mode = getattr(command, 'run_mode', 1)
        self.run_mode_combo.set_active_id(str(run_mode))
        self.run_mode_combo.set_tooltip_text("Mode 1: Execute command immediately\nMode 2: Type command in terminal, user can edit/add arguments before running")
        run_mode_box.append(self.run_mode_combo)
        main_box.append(run_mode_box)
        
        # No terminal option
        no_terminal_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.no_terminal_check = Gtk.CheckButton(label="No terminal")
        self.no_terminal_check.set_tooltip_text("Run command directly without opening a terminal")
        self.no_terminal_check.set_active(getattr(command, 'no_terminal', False))
        no_terminal_box.append(self.no_terminal_check)
        no_terminal_box.set_halign(Gtk.Align.START)
        main_box.append(no_terminal_box)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_margin_start(24)
        button_box.set_margin_end(24)
        button_box.set_margin_bottom(24)
        button_box.set_halign(Gtk.Align.END)
        
        # Cancel button
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda _: self._on_cancel())
        button_box.append(cancel_btn)
        
        # Save button
        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", lambda _: self._on_save())
        button_box.append(save_btn)
        
        main_box.append(button_box)
        
        # Create main container with headerbar at top
        # This makes the window draggable via the headerbar
        main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_container.append(headerbar)
        main_container.append(main_box)
        
        # Set as window content
        self.set_content(main_container)
    
    def set_saved_callback(self, callback):
        """Set callback to be called when command is saved."""
        self.saved_callback = callback
    
    def _on_cancel(self):
        """Handle cancel button."""
        self.close()
    
    def _on_save(self):
        """Handle save button."""
        # Get values
        number = int(self.number_entry.get_value())
        title = self.title_entry.get_text()
        
        buffer = self.command_text.get_buffer()
        start, end = buffer.get_bounds()
        command = buffer.get_text(start, end, False)
        
        icon = self.icon_entry.get_text()
        color = self.color_combo.get_active_id()
        tag = self.tag_entry.get_text()
        category = self.category_entry.get_text()
        
        buffer = self.desc_text.get_buffer()
        start, end = buffer.get_bounds()
        description = buffer.get_text(start, end, False)
        
        no_terminal = self.no_terminal_check.get_active()
        run_mode = int(self.run_mode_combo.get_active_id())
        
        # Update command
        self.command.number = number
        self.command.title = title
        self.command.command = command
        self.command.icon = icon
        self.command.color = color
        self.command.tag = tag
        self.command.category = category
        self.command.description = description
        self.command.no_terminal = no_terminal
        self.command.run_mode = run_mode
        
        # Call callback if set
        if self.saved_callback:
            self.saved_callback(self.command)
        logger.info(f"Command saved: {self.command.title}")
        
        # Close dialog
        self.close()

