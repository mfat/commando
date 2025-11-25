"""
Main window class.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Vte", "3.91")

from gi.repository import Gtk, Adw, GLib, Gio, Vte, Pango
import os

from commando.logger import get_logger
from commando.config import Config
from commando.views.main_view import MainView
from commando.views.terminal_view import TerminalView
from commando.views.web_view import WebView
from commando.widgets.speed_dial import SpeedDial

logger = get_logger(__name__)


class CommandoWindow(Adw.ApplicationWindow):
    """Main application window."""
    
    def __init__(self, **kwargs):
        """Initialize the window."""
        super().__init__(**kwargs)
        self.config = Config()
        
        self.set_title("Commando")
        self.set_default_size(1200, 800)
        
        # Connect close request to ensure proper cleanup and quit
        self.connect("close-request", self._on_close_request)
        
        # Create header bar
        self._create_header_bar()
        
        # Create main box with headerbar
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Add headerbar to main box
        self.main_box.append(self.header)
        
        # Create view switcher first (needed before creating views)
        self._create_view_switcher()
        
        # Speed dial (positioned after header, before stack, hidden by default)
        self.speed_dial = SpeedDial(None)  # Will be set after main_view is created
        self.main_box.append(self.speed_dial)
        
        # Create paned widget for resizable bottom terminal
        # This allows the user to drag to resize the terminal
        self.main_paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.main_paned.set_vexpand(True)
        self.main_paned.set_hexpand(True)
        self.main_box.append(self.main_paned)
        
        # Set main box as content
        self.set_content(self.main_box)
        
        # Initialize embedded terminal variables (bottom terminal in main window)
        self.embedded_terminal_view = None
        self.embedded_terminal_widget = None
        
        # Setup bottom terminal based on config (after views are created)
        
        # Create views
        try:
            self.main_view = MainView()
            logger.debug("MainView created")
        except Exception as e:
            logger.error(f"Failed to create MainView: {e}", exc_info=True)
            raise
        
        try:
            self.standalone_terminal_view = TerminalView()
            logger.debug("StandaloneTerminalView created")
        except Exception as e:
            logger.error(f"Failed to create StandaloneTerminalView: {e}", exc_info=True)
            # Create a placeholder view instead
            self.standalone_terminal_view = Gtk.Label(label="Terminal view unavailable")
        
        try:
            self.web_view = WebView()
            logger.debug("WebView created")
        except Exception as e:
            logger.error(f"Failed to create WebView: {e}", exc_info=True)
            # Create a placeholder view instead
            self.web_view = Gtk.Label(label="Web view unavailable")
        
        # Connect executor to standalone terminal view
        if hasattr(self.main_view, 'executor'):
            self.main_view.executor.set_terminal_view(self.standalone_terminal_view)
        
        # Add views to stack
        self.stack.add_titled(self.main_view, "main", "Commands")
        self.stack.add_titled(self.standalone_terminal_view, "terminal", "Terminal")
        self.stack.add_titled(self.web_view, "web", "Web")
        
        # Connect to stack's visible-child-changed signal to focus FlowBox when main view is shown
        self.stack.connect("notify::visible-child", self._on_stack_visible_child_changed)
        
        # Connect to window's realize and map signals to focus FlowBox when window is first shown
        self.connect("realize", self._on_window_realize)
        self.connect("notify::visible", self._on_window_visible_changed)
        
        # Set stack as the first (top) child of the paned directly
        # No need for an extra content_box wrapper
        self.main_paned.set_start_child(self.stack)
        # The bottom terminal will be set as the second (bottom) child when created
        
        # Update speed dial with main_view reference
        self.speed_dial.main_view = self.main_view
        
        # Connect menu actions
        self._setup_menu_actions()
        
        # Apply theme
        self._apply_theme()
        
        # Keyboard navigation
        self._setup_keyboard_navigation()
        
        # Setup bottom terminal based on config
        self._setup_bottom_terminal()
        
        logger.info("CommandoWindow initialized")
    
    def _create_header_bar(self):
        """Create the header bar."""
        # AdwApplicationWindow doesn't support set_titlebar()
        # Instead, we create a headerbar and add it to the content
        header = Adw.HeaderBar()
        self.header = header
        
        # Home button (to go back to main view)
        home_button = Gtk.Button()
        home_button.set_icon_name("go-home-symbolic")
        home_button.set_tooltip_text("Go to Commands")
        home_button.connect("clicked", self._on_home_clicked)
        header.pack_start(home_button)
        
        # Search button
        search_button = Gtk.Button()
        search_button.set_icon_name("system-search-symbolic")
        search_button.set_tooltip_text("Search Commands")
        search_button.connect("clicked", self._on_search_clicked)
        header.pack_start(search_button)
        
        # Menu button
        menu = Gtk.MenuButton()
        menu.set_icon_name("open-menu-symbolic")
        menu_model = self._create_menu_model()
        menu.set_menu_model(menu_model)
        header.pack_end(menu)
        
        # Theme toggle
        theme_toggle = Gtk.ToggleButton()
        theme_toggle.set_icon_name("dark-mode-symbolic")
        theme_toggle.connect("toggled", self._on_theme_toggled)
        header.pack_end(theme_toggle)
        
        # View switcher will be added here
    
    def _create_menu_model(self):
        """Create the application menu model."""
        menu = Gio.Menu()
        
        # File section
        file_section = Gio.Menu()
        file_section.append("New Command", "app.new_command")
        file_section.append("Import", "app.import")
        file_section.append("Export", "app.export")
        menu.append_section(None, file_section)
        
        # View section
        view_section = Gio.Menu()
        view_section.append("Settings", "app.settings")
        menu.append_section(None, view_section)
        
        # Help section
        help_section = Gio.Menu()
        help_section.append("About", "app.about")
        menu.append_section(None, help_section)
        
        return menu
    
    def _create_view_switcher(self):
        """Create the view switcher."""
        self.stack = Adw.ViewStack()
        self.view_switcher = Adw.ViewSwitcherBar()
        self.view_switcher.set_stack(self.stack)
        
        self.header.set_title_widget(self.view_switcher)
        
        # Stack will be added to paned later (not to main_box)
        # Make it expand to fill available space
        self.stack.set_vexpand(True)
        self.stack.set_hexpand(True)
    
    def _apply_theme(self):
        """Apply the current theme."""
        theme = self.config.get("theme", "system")
        style_manager = Adw.StyleManager.get_default()
        
        if theme == "light":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        elif theme == "dark":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.PREFER_DARK)
    
    def _on_theme_toggled(self, button):
        """Handle theme toggle."""
        style_manager = Adw.StyleManager.get_default()
        current = style_manager.get_color_scheme()
        
        if current == Adw.ColorScheme.FORCE_LIGHT:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            self.config.set("theme", "dark")
        elif current == Adw.ColorScheme.FORCE_DARK:
            style_manager.set_color_scheme(Adw.ColorScheme.PREFER_DARK)
            self.config.set("theme", "system")
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            self.config.set("theme", "light")
    
    def _setup_menu_actions(self):
        """Set up menu actions."""
        app = self.get_application()
        
        # New command
        action = Gio.SimpleAction.new("new_command", None)
        action.connect("activate", lambda a, p: self.main_view._on_new_command(None))
        app.add_action(action)
        
        # Settings
        action = Gio.SimpleAction.new("settings", None)
        action.connect("activate", self._on_settings)
        app.add_action(action)
        
        # About
        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self._on_about)
        app.add_action(action)
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation shortcuts."""
        # Create shortcut controller
        shortcut_controller = Gtk.ShortcutController()
        shortcut_controller.set_scope(Gtk.ShortcutScope.GLOBAL)
        
        # Ctrl+K to show speed dial
        shortcut = Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Primary>k"),
            Gtk.CallbackAction.new(lambda *args: self.speed_dial._show_speed_dial())
        )
        shortcut_controller.add_shortcut(shortcut)
        
        # Ctrl+Shift+F to toggle search
        shortcut = Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Primary><Shift>f"),
            Gtk.CallbackAction.new(self._toggle_search)
        )
        shortcut_controller.add_shortcut(shortcut)
        
        # Ctrl+N for new command
        shortcut = Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Primary>n"),
            Gtk.CallbackAction.new(lambda *args: self.main_view._on_new_command(None))
        )
        shortcut_controller.add_shortcut(shortcut)
        
        # Ctrl+, for settings
        shortcut = Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Primary>comma"),
            Gtk.CallbackAction.new(lambda *args: self._on_settings(None, None))
        )
        shortcut_controller.add_shortcut(shortcut)
        
        # Ctrl+Shift+E to toggle between cards view and terminal
        shortcut = Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Primary><Shift>e"),
            Gtk.CallbackAction.new(self._toggle_cards_terminal)
        )
        shortcut_controller.add_shortcut(shortcut)
        
        self.add_controller(shortcut_controller)
    
    def _on_search_clicked(self, button):
        """Handle search button click - toggle search bar."""
        if hasattr(self.main_view, "toggle_search"):
            self.main_view.toggle_search()
    
    def _toggle_search(self, *args):
        """Toggle search bar visibility (keyboard shortcut)."""
        if hasattr(self.main_view, "toggle_search"):
            self.main_view.toggle_search()
    
    def _on_home_clicked(self, button):
        """Handle home button click - switch to main view."""
        self.stack.set_visible_child_name("main")
        # Focus will be set by _on_stack_visible_child_changed
    
    def _toggle_cards_terminal(self, *args, from_terminal=None):
        """
        Toggle between cards view and terminal view (Ctrl+Shift+E).
        
        Args:
            from_terminal: TerminalView instance that triggered the toggle, or None
        """
        current_view = self.stack.get_visible_child_name()
        
        # Determine which terminal is active
        # If from_terminal is provided, we know which one triggered it
        is_embedded_terminal = False
        if from_terminal:
            is_embedded_terminal = (from_terminal == self.embedded_terminal_view)
        else:
            # Check if embedded terminal is active by checking focus
            focus_widget = self.get_focus()
            if focus_widget and self.embedded_terminal_view:
                # Walk up the widget tree to see if focus is in embedded terminal
                parent = focus_widget
                while parent:
                    if parent == self.embedded_terminal_view or parent == self.embedded_terminal_widget:
                        is_embedded_terminal = True
                        break
                    parent = parent.get_parent() if hasattr(parent, 'get_parent') else None
                    if parent == self.standalone_terminal_view:
                        # Focus is in standalone terminal view, not embedded
                        break
        
        if current_view == "main":
            # Switch to terminal - prefer embedded terminal if enabled, otherwise standalone terminal view
            if self.embedded_terminal_view and self.embedded_terminal_widget and self.embedded_terminal_widget.get_visible():
                # Embedded terminal is available, focus it
                if hasattr(self.embedded_terminal_view, 'focus_current_terminal'):
                    GLib.timeout_add(100, self.embedded_terminal_view.focus_current_terminal)
                    GLib.timeout_add(300, self.embedded_terminal_view.focus_current_terminal)
            else:
                # Switch to standalone terminal view
                self.stack.set_visible_child_name("terminal")
                # Focus the terminal
                if hasattr(self.standalone_terminal_view, 'focus_current_terminal'):
                    GLib.timeout_add(100, self.standalone_terminal_view.focus_current_terminal)
                    GLib.timeout_add(300, self.standalone_terminal_view.focus_current_terminal)
        elif current_view == "terminal" or is_embedded_terminal:
            # Switch to main (cards) view - either from terminal view or bottom terminal
            self.stack.set_visible_child_name("main")
            # Explicitly focus FlowBox after switching
            def focus_flowbox():
                if hasattr(self.main_view, 'flow_box'):
                    if self.main_view.flow_box.get_visible() and self.main_view.flow_box.get_can_focus():
                        self.main_view.flow_box.grab_focus()
                        logger.debug("FlowBox focused after toggle from terminal")
                        return False
                return True  # Try again if not ready
            
            # Try multiple times with increasing delays
            GLib.timeout_add(50, focus_flowbox)
            GLib.timeout_add(150, focus_flowbox)
            GLib.timeout_add(300, focus_flowbox)
        else:
            # If in web view or other, switch to main view
            self.stack.set_visible_child_name("main")
            # Focus FlowBox
            GLib.timeout_add(150, self._focus_flowbox)
    
    def _on_window_realize(self, window):
        """Handle window realization - focus FlowBox when window is first shown."""
        # When window is realized, focus the FlowBox if main view is visible
        if self.stack.get_visible_child() == self.main_view:
            if hasattr(self.main_view, 'flow_box'):
                # Use a small timeout to ensure everything is ready
                GLib.timeout_add(150, self._focus_flowbox)
    
    def _on_window_visible_changed(self, window, param):
        """Handle window visibility change - focus FlowBox when window becomes visible."""
        if window.get_visible() and self.stack.get_visible_child() == self.main_view:
            if hasattr(self.main_view, 'flow_box'):
                # Use a small timeout to ensure everything is ready
                GLib.timeout_add(150, self._focus_flowbox)
    
    def _focus_flowbox(self):
        """Focus the FlowBox."""
        if hasattr(self.main_view, 'flow_box'):
            # Make sure FlowBox is visible and can receive focus
            if self.main_view.flow_box.get_visible() and self.main_view.flow_box.get_can_focus():
                self.main_view.flow_box.grab_focus()
                logger.debug("FlowBox focused")
            else:
                # Try again after a short delay if not ready yet
                GLib.timeout_add(50, self._focus_flowbox)
                return True  # Repeat
        return False  # Don't repeat
    
    def _on_stack_visible_child_changed(self, stack, param):
        """Handle stack visible child change - focus FlowBox when main view is shown."""
        visible_child = stack.get_visible_child()
        if visible_child == self.main_view:
            # Main view is now visible, focus the FlowBox
            if hasattr(self.main_view, 'flow_box'):
                # Use a small delay to ensure the view is fully visible
                GLib.timeout_add(50, self._focus_flowbox)
    
    def _on_settings(self, action, param):
        """Open settings dialog."""
        from commando.dialogs.settings import SettingsDialog
        dialog = SettingsDialog(parent=self)
        dialog.present()
    
    def _on_about(self, action, param):
        """Show about dialog."""
        from commando.dialogs.about import AboutDialog
        dialog = AboutDialog(parent=self)
        dialog.present()
    
    def _on_close_request(self, window):
        """Handle window close request."""
        logger.debug("Window close requested")
        # Cleanup will be handled by application shutdown signal
        # Explicitly quit the application to ensure Python process exits
        app = self.get_application()
        if app:
            app.quit()
        # Return False to allow default close behavior
        return False
    
    def _setup_bottom_terminal(self):
        """Setup embedded terminal widget based on config."""
        show_terminal = self.config.get("terminal.show_in_main_window", False)
        if show_terminal:
            self._create_bottom_terminal()
        else:
            self._remove_bottom_terminal()
    
    def _create_bottom_terminal(self):
        """Create embedded terminal widget (bottom terminal in main window)."""
        if self.embedded_terminal_view is not None and self.embedded_terminal_widget is not None:
            # Already exists, make sure it's visible and in the paned
            if self.main_paned.get_end_child() != self.embedded_terminal_widget:
                # Widget exists but not in paned, add it back
                self.main_paned.set_end_child(self.embedded_terminal_widget)
            self.embedded_terminal_widget.set_visible(True)
            return
        
        try:
            # Create full TerminalView (with tabs support)
            self.embedded_terminal_view = TerminalView()
            
            # Set minimum height for the terminal view
            self.embedded_terminal_view.set_size_request(-1, 150)  # Minimum 150px height
            
            # Create a frame/container for the terminal
            frame = Gtk.Frame()
            frame.set_margin_start(0)
            frame.set_margin_end(0)
            frame.set_margin_top(0)
            frame.set_margin_bottom(0)
            # Make frame focusable so clicks can focus the terminal
            frame.set_focusable(True)
            frame.set_can_focus(False)  # Frame itself shouldn't take focus, but should pass it to child
            frame.set_child(self.embedded_terminal_view)
            
            # Connect to frame click to focus terminal
            click_controller = Gtk.GestureClick()
            click_controller.connect("pressed", lambda *args: self._focus_embedded_terminal_on_click())
            frame.add_controller(click_controller)
            
            # Set the frame as the second (bottom) child of the paned
            # This makes it resizable via drag
            self.main_paned.set_end_child(frame)
            self.main_paned.set_resize_end_child(True)  # Allow resizing
            self.main_paned.set_shrink_end_child(False)  # Don't shrink below minimum
            
            # Set initial position so terminal gets about 200px initially
            # Use a timeout to set position after the widget is allocated
            def set_initial_position():
                allocation = self.main_paned.get_allocation()
                if allocation.height > 0:
                    # Set position so terminal gets about 200px
                    initial_pos = allocation.height - 200
                    if initial_pos > 100:  # Ensure reasonable minimum for top pane
                        self.main_paned.set_position(initial_pos)
                        return False  # Don't repeat
                # If not allocated yet, try again
                return True  # Repeat until allocated
            
            # Try to set position after a short delay to ensure widget is allocated
            GLib.timeout_add(100, set_initial_position)
            
            self.embedded_terminal_widget = frame
            
            # Ensure embedded terminal can receive focus
            self.embedded_terminal_view.set_focusable(True)
            self.embedded_terminal_view.set_can_focus(True)
            
            # Update executor to use embedded terminal when visible
            if hasattr(self.main_view, 'executor'):
                self.main_view.executor.embedded_terminal_view = self.embedded_terminal_view
                logger.debug("Connected embedded terminal to executor")
            
            logger.info("Embedded terminal created with full TerminalView (resizable)")
            
            # Ensure embedded terminal can receive focus
            self.embedded_terminal_view.set_focusable(True)
            self.embedded_terminal_view.set_can_focus(True)
        except Exception as e:
            logger.error(f"Failed to create embedded terminal: {e}", exc_info=True)
    
    def _focus_embedded_terminal_on_click(self):
        """Focus the embedded terminal when clicked."""
        if self.embedded_terminal_view:
            def focus_terminal():
                if self.embedded_terminal_view:
                    self.embedded_terminal_view.focus_current_terminal()
                return False
            # Try multiple times to ensure focus works
            GLib.idle_add(focus_terminal)
            GLib.timeout_add(50, focus_terminal)
            GLib.timeout_add(200, focus_terminal)
    
    def _remove_bottom_terminal(self):
        """Remove embedded terminal widget."""
        if self.embedded_terminal_view is not None:
            # Cleanup the terminal view
            self.embedded_terminal_view.cleanup()
            
            # Remove from paned
            if self.embedded_terminal_widget:
                self.main_paned.set_end_child(None)
            
            self.embedded_terminal_widget = None
            self.embedded_terminal_view = None
            
            # Update executor to remove embedded terminal reference
            if hasattr(self.main_view, 'executor'):
                self.main_view.executor.embedded_terminal_view = None
            
            logger.info("Embedded terminal removed")
    
    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up window")
        try:
            # Clean up bottom terminal
            self._remove_bottom_terminal()
            
            if hasattr(self, "main_view"):
                logger.debug("Cleaning up main view")
                self.main_view.cleanup()
            if hasattr(self, "standalone_terminal_view"):
                logger.debug("Cleaning up standalone terminal view")
                self.standalone_terminal_view.cleanup()
            if hasattr(self, "web_view"):
                logger.debug("Cleaning up web view")
                self.web_view.cleanup()
            logger.info("Window cleanup complete")
        except Exception as e:
            logger.error(f"Error during window cleanup: {e}", exc_info=True)

