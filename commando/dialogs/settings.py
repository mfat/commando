"""
Settings dialog.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from commando.logger import get_logger
from commando.config import Config

logger = get_logger(__name__)


class SettingsDialog(Adw.PreferencesWindow):
    """Settings dialog."""
    
    def __init__(self, **kwargs):
        """Initialize settings dialog."""
        super().__init__(**kwargs)
        self.config = Config()
        
        self.set_title("Settings")
        self.set_default_size(600, 700)
        
        # Terminal page
        self._create_terminal_page()
        
        # Appearance page
        self._create_appearance_page()
        
        # General page
        self._create_general_page()
    
    def _create_terminal_page(self):
        """Create terminal settings page."""
        page = Adw.PreferencesPage(title="Terminal", icon_name="terminal-symbolic")
        
        # Terminal group
        group = Adw.PreferencesGroup(title="Terminal Settings")
        
        # Font
        font_row = Adw.ActionRow(title="Font")
        font_entry = Gtk.Entry()
        font_entry.set_text(self.config.get("terminal.font", "Monospace 12"))
        font_entry.connect("changed", self._on_font_changed)
        font_row.add_suffix(font_entry)
        group.add(font_row)
        
        # Scrollback lines
        scrollback_row = Adw.ActionRow(title="Scrollback Lines")
        scrollback_spin = Gtk.SpinButton()
        scrollback_spin.set_adjustment(
            Gtk.Adjustment(
                value=self.config.get("terminal.scrollback_lines", 10000),
                lower=100,
                upper=100000,
                step_increment=1000
            )
        )
        scrollback_spin.set_numeric(True)
        scrollback_spin.connect("value-changed", self._on_scrollback_changed)
        scrollback_row.add_suffix(scrollback_spin)
        group.add(scrollback_row)
        
        # Cursor blink
        cursor_blink_row = Adw.ActionRow(title="Cursor Blink")
        cursor_blink_switch = Gtk.Switch()
        cursor_blink_switch.set_active(self.config.get("terminal.cursor_blink", True))
        cursor_blink_switch.connect("notify::active", self._on_cursor_blink_changed)
        cursor_blink_row.add_suffix(cursor_blink_switch)
        group.add(cursor_blink_row)
        
        # External terminal
        external_row = Adw.ActionRow(title="External Terminal")
        external_entry = Gtk.Entry()
        external_entry.set_text(self.config.get("terminal.external_terminal", "") or "")
        external_entry.set_placeholder_text("e.g., gnome-terminal, xterm")
        external_entry.connect("changed", self._on_external_terminal_changed)
        external_row.add_suffix(external_entry)
        group.add(external_row)
        
        # Show terminal in main window
        show_terminal_row = Adw.ActionRow(
            title="Show Terminal in Main Window",
            subtitle="Display a terminal widget at the bottom of the main window"
        )
        show_terminal_switch = Gtk.Switch()
        show_terminal_switch.set_active(self.config.get("terminal.show_in_main_window", False))
        show_terminal_switch.connect("notify::active", self._on_show_terminal_changed)
        show_terminal_row.add_suffix(show_terminal_switch)
        group.add(show_terminal_row)
        
        page.add(group)
        self.add(page)
    
    def _create_appearance_page(self):
        """Create appearance settings page."""
        page = Adw.PreferencesPage(title="Appearance", icon_name="preferences-desktop-theme-symbolic")
        
        # Theme group
        group = Adw.PreferencesGroup(title="Theme")
        
        # Theme selection
        theme_row = Adw.ActionRow(title="Theme")
        theme_combo = Gtk.ComboBoxText()
        theme_combo.append("system", "System")
        theme_combo.append("light", "Light")
        theme_combo.append("dark", "Dark")
        theme_combo.set_active_id(self.config.get("theme", "system"))
        theme_combo.connect("changed", self._on_theme_changed)
        theme_row.add_suffix(theme_combo)
        group.add(theme_row)
        
        page.add(group)
        self.add(page)
    
    def _create_general_page(self):
        """Create general settings page."""
        page = Adw.PreferencesPage(title="General", icon_name="emblem-system-symbolic")
        
        # Logging group
        group = Adw.PreferencesGroup(title="Logging")
        
        # Log level
        log_level_row = Adw.ActionRow(title="Log Level")
        log_level_combo = Gtk.ComboBoxText()
        log_level_combo.append("DEBUG", "Debug")
        log_level_combo.append("INFO", "Info")
        log_level_combo.append("WARNING", "Warning")
        log_level_combo.append("ERROR", "Error")
        log_level_combo.set_active_id(self.config.get("logging.level", "INFO"))
        log_level_combo.connect("changed", self._on_log_level_changed)
        log_level_row.add_suffix(log_level_combo)
        group.add(log_level_row)
        
        page.add(group)
        self.add(page)
    
    def _on_font_changed(self, entry):
        """Handle font change."""
        self.config.set("terminal.font", entry.get_text())
    
    def _on_scrollback_changed(self, spin):
        """Handle scrollback change."""
        self.config.set("terminal.scrollback_lines", int(spin.get_value()))
    
    def _on_cursor_blink_changed(self, switch, param):
        """Handle cursor blink change."""
        self.config.set("terminal.cursor_blink", switch.get_active())
    
    def _on_external_terminal_changed(self, entry):
        """Handle external terminal change."""
        text = entry.get_text().strip()
        self.config.set("terminal.external_terminal", text if text else None)
    
    def _on_show_terminal_changed(self, switch, param):
        """Handle show terminal in main window change."""
        self.config.set("terminal.show_in_main_window", switch.get_active())
        # Notify the main window to update immediately
        # Get the parent window from the dialog
        parent = self.get_transient_for()
        if parent and hasattr(parent, '_setup_bottom_terminal'):
            parent._setup_bottom_terminal()
    
    def _on_theme_changed(self, combo):
        """Handle theme change."""
        theme = combo.get_active_id()
        self.config.set("theme", theme)
        # Apply theme immediately
        style_manager = Adw.StyleManager.get_default()
        if theme == "light":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        elif theme == "dark":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.PREFER_DARK)
    
    def _on_log_level_changed(self, combo):
        """Handle log level change."""
        level = combo.get_active_id()
        self.config.set("logging.level", level)
        from commando.logger import set_log_level, LogLevel
        set_log_level(LogLevel[level])

