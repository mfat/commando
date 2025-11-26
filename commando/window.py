"""
Main window class.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, Gio

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
        
        # Connect to window focus events to handle focus properly when returning from external apps
        self.connect("notify::has-focus", self._on_window_focus_changed)
        
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
        
        # Set main box as content
        self.set_content(self.main_box)
        
        # Create views
        try:
            self.main_view = MainView()
            logger.debug("MainView created")
        except Exception as e:
            logger.error(f"Failed to create MainView: {e}", exc_info=True)
            raise
        
        try:
            self.terminal_view = TerminalView()
            logger.debug("TerminalView created")
        except Exception as e:
            logger.error(f"Failed to create TerminalView: {e}", exc_info=True)
            # Create a placeholder view instead
            self.terminal_view = Gtk.Label(label="Terminal view unavailable")
        
        try:
            self.web_view = WebView()
            logger.debug("WebView created")
        except Exception as e:
            logger.error(f"Failed to create WebView: {e}", exc_info=True)
            # Create a placeholder view instead
            self.web_view = Gtk.Label(label="Web view unavailable")
        
        # Connect executor to terminal view
        if hasattr(self.main_view, 'executor'):
            self.main_view.executor.set_terminal_view(self.terminal_view)
        
        # Add views to stack
        self.stack.add_titled(self.main_view, "main", "Commands")
        self.stack.add_titled(self.terminal_view, "terminal", "Terminal")
        self.stack.add_titled(self.web_view, "web", "Web")
        
        # Set main view as default
        self.stack.set_visible_child_name("main")
        
        # Update speed dial with main_view reference
        self.speed_dial.main_view = self.main_view
        
        # Update home button icon to reflect initial state
        self._update_home_button_icon()
        
        # Connect menu actions
        self._setup_menu_actions()
        
        # Apply theme
        self._apply_theme()
        
        # Keyboard navigation
        self._setup_keyboard_navigation()
        
        logger.info("CommandoWindow initialized")
    
    def _create_header_bar(self):
        """Create the header bar."""
        # AdwApplicationWindow doesn't support set_titlebar()
        # Instead, we create a headerbar and add it to the content
        header = Adw.HeaderBar()
        self.header = header
        
        # Home button (to go back to main view)
        self.home_button = Gtk.Button()
        self.home_button.set_icon_name("utilities-terminal-symbolic")
        self.home_button.set_tooltip_text("Go to Terminal")
        self.home_button.connect("clicked", self._on_home_clicked)
        header.pack_start(self.home_button)
        
        # Menu button
        menu = Gtk.MenuButton()
        menu.set_icon_name("open-menu-symbolic")
        menu_model = self._create_menu_model()
        menu.set_menu_model(menu_model)
        header.pack_end(menu)
        
        # Theme toggle
        self.theme_toggle = Gtk.ToggleButton()
        self.theme_toggle.set_icon_name("night-light-symbolic")
        self.theme_toggle.set_tooltip_text("Theme")
        self.theme_toggle.connect("toggled", self._on_theme_toggled)
        header.pack_end(self.theme_toggle)
        
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
        
        # Add stack to main box - make it expand to fill available space
        self.stack.set_vexpand(True)
        self.stack.set_hexpand(True)
        self.main_box.append(self.stack)
        
        # Connect to stack's visible-child-changed signal to focus FlowBox when main view is shown
        self.stack.connect("notify::visible-child", self._on_stack_visible_child_changed)
        
        # Connect to window's realize and visible signals to focus FlowBox when window is first shown
        self.connect("realize", self._on_window_realize)
        self.connect("notify::visible", self._on_window_visible_changed)
        
        # Connect to stack's visible-child-changed signal to focus FlowBox when main view is shown
        self.stack.connect("notify::visible-child", self._on_stack_visible_child_changed)
        
        # Connect to window's realize and visible signals to focus FlowBox when window is first shown
        self.connect("realize", self._on_window_realize)
        self.connect("notify::visible", self._on_window_visible_changed)
    
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
        
        # Update theme icon after applying theme
        if hasattr(self, 'theme_toggle'):
            self._update_theme_icon()
    
    def _update_theme_icon(self):
        """Update theme toggle icon based on current theme."""
        if not hasattr(self, 'theme_toggle'):
            return
        
        # Use night-light-symbolic for all modes
        self.theme_toggle.set_icon_name("night-light-symbolic")
        
        # Update tooltip based on current theme
        style_manager = Adw.StyleManager.get_default()
        current = style_manager.get_color_scheme()
        
        if current == Adw.ColorScheme.FORCE_LIGHT:
            self.theme_toggle.set_tooltip_text("Switch to Dark Mode")
        elif current == Adw.ColorScheme.FORCE_DARK:
            self.theme_toggle.set_tooltip_text("Switch to Light Mode")
        else:
            self.theme_toggle.set_tooltip_text("Switch to Light Mode")
    
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
        
        # Update icon after theme change
        self._update_theme_icon()
    
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
        
        # Ctrl+Shift+F to toggle search bar
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
        
        # Ctrl+Shift+E to toggle between main view and terminal view
        shortcut = Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Primary><Shift>e"),
            Gtk.CallbackAction.new(lambda *args: self._on_home_clicked(self.home_button))
        )
        shortcut_controller.add_shortcut(shortcut)
        
        self.add_controller(shortcut_controller)
        
        # Add a minimal window-level keyboard controller to consume unhandled events
        # This prevents error tones when the window regains focus but no widget has focus yet
        from gi.repository import Gdk
        key_controller = Gtk.EventControllerKey()
        key_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        key_controller.connect("key-pressed", self._on_window_key_pressed)
        self.add_controller(key_controller)
    
    def _on_window_key_pressed(self, controller, keyval, keycode, state):
        """Handle keyboard input at window level - only consume events to prevent error tones."""
        from gi.repository import Gdk
        
        # Only handle when main view is visible and we're trying to prevent error tones
        if self.stack.get_visible_child() != self.main_view:
            return False
        
        # If MainView or FlowBox has focus, let them handle it - don't intercept at all
        if hasattr(self.main_view, 'flow_box') and self.main_view.flow_box.has_focus():
            return False
        if self.main_view.has_focus():
            return False
        if hasattr(self.main_view, 'search_entry') and self.main_view.search_entry.has_focus():
            return False
        
        # Only handle arrow keys and Enter to prevent error tones
        # Forward to MainView's handler if it can handle it
        is_arrow = keyval in (Gdk.KEY_Up, Gdk.KEY_Down, Gdk.KEY_Left, Gdk.KEY_Right,
                              Gdk.KEY_KP_Up, Gdk.KEY_KP_Down, Gdk.KEY_KP_Left, Gdk.KEY_KP_Right)
        is_enter = keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter)
        
        if is_arrow or is_enter:
            # Try to forward to MainView's handler
            if hasattr(self.main_view, '_on_key_pressed'):
                result = self.main_view._on_key_pressed(controller, keyval, keycode, state)
                if result:
                    return True
            # If MainView can't handle it, consume it anyway to prevent error tone
            return True
        
        # For all other keys (including number keys), don't consume them
        # Let them pass through to MainView's controller which uses CAPTURE phase
        return False
    
    # Removed _on_window_key_pressed - MainView's keyboard controller handles all keyboard events
    # This prevents unhandled events from causing error tones
    
    def _toggle_search(self, *args):
        """Toggle search bar visibility and focus it when shown."""
        if hasattr(self.main_view, "search_revealer"):
            current_state = self.main_view.search_revealer.get_reveal_child()
            self.main_view.search_revealer.set_reveal_child(not current_state)
            if not current_state:
                # Search bar is being shown, focus it
                GLib.idle_add(self.main_view.search_entry.grab_focus)
    
    def _on_home_clicked(self, button):
        """Handle home button click - toggle between main view and terminal view."""
        current_view = self.stack.get_visible_child_name()
        
        if current_view == "main":
            # Switch to terminal view
            self.stack.set_visible_child_name("terminal")
            # Focus terminal after switching
            def focus_terminal():
                if hasattr(self.terminal_view, 'focus_current_terminal'):
                    self.terminal_view.focus_current_terminal()
                    return False
                return False
            GLib.timeout_add(100, focus_terminal)
        else:
            # Switch to main view
            # First, remove focus from terminal view if it has focus
            if hasattr(self, 'terminal_view') and self.terminal_view.has_focus():
                # Remove focus from terminal by focusing the window itself temporarily
                self.grab_focus()
                logger.debug("Removed focus from terminal view")
            
            self.stack.set_visible_child_name("main")
            # Reset number input when switching to main view
            if hasattr(self.main_view, '_reset_number_input'):
                self.main_view._reset_number_input()
            
            # The _on_stack_visible_child_changed handler will focus MainView
            # But we also ensure focus here with multiple retries
            def focus_main_view():
                if hasattr(self.main_view, 'flow_box'):
                    # Ensure MainView is visible and realized
                    if not self.main_view.get_visible() or not self.main_view.get_realized():
                        logger.debug("MainView not ready yet, will retry")
                        return True  # Retry
                    
                    # Ensure a card is selected
                    selected = self.main_view.flow_box.get_selected_children()
                    if not selected:
                        first_child = self.main_view.flow_box.get_first_child()
                        if first_child:
                            self.main_view.flow_box.select_child(first_child)
                            logger.debug("Selected first card after home button")
                    
                    # Focus MainView so it can receive keyboard events
                    self.main_view.grab_focus()
                    has_focus = self.main_view.has_focus()
                    logger.debug(f"MainView focused after home button: has_focus={has_focus}")
                    
                    if not has_focus:
                        # Retry if focus failed
                        return True
                    return False  # Success, don't retry
                return False
            
            # Use multiple timeouts with increasing delays
            GLib.timeout_add(100, focus_main_view)
            GLib.timeout_add(200, focus_main_view)
            GLib.timeout_add(400, focus_main_view)
        
        # Update home button icon after view change
        self._update_home_button_icon()
    
    def _update_home_button_icon(self):
        """Update home button icon and tooltip based on current view."""
        if not hasattr(self, 'home_button') or not hasattr(self, 'stack'):
            return
        
        current_view = self.stack.get_visible_child_name()
        if current_view == "main":
            # Show terminal icon when in main view (clicking will go to terminal)
            self.home_button.set_icon_name("utilities-terminal-symbolic")
            self.home_button.set_tooltip_text("Go to Terminal")
        else:
            # Show home icon when in terminal view (clicking will go to main view)
            self.home_button.set_icon_name("go-home-symbolic")
            self.home_button.set_tooltip_text("Go to Commands")
    
    def _on_window_realize(self, window):
        """Handle window realization - focus MainView when window is first shown."""
        # When window is realized, focus MainView if main view is visible
        if self.stack.get_visible_child() == self.main_view:
            if hasattr(self.main_view, 'flow_box'):
                def focus_main_view():
                    # Ensure a card is selected
                    selected = self.main_view.flow_box.get_selected_children()
                    if not selected:
                        first_child = self.main_view.flow_box.get_first_child()
                        if first_child:
                            self.main_view.flow_box.select_child(first_child)
                    
                    # Focus MainView so it can receive keyboard events
                    self.main_view.grab_focus()
                    logger.debug(f"MainView focused on window realize: has_focus={self.main_view.has_focus()}")
                    return False
                GLib.timeout_add(150, focus_main_view)
    
    def _on_window_visible_changed(self, window, param):
        """Handle window visibility change - focus MainView when window becomes visible."""
        if window.get_visible() and self.stack.get_visible_child() == self.main_view:
            if hasattr(self.main_view, 'flow_box'):
                def focus_main_view():
                    # Ensure a card is selected
                    selected = self.main_view.flow_box.get_selected_children()
                    if not selected:
                        first_child = self.main_view.flow_box.get_first_child()
                        if first_child:
                            self.main_view.flow_box.select_child(first_child)
                    
                    # Focus MainView so it can receive keyboard events
                    self.main_view.grab_focus()
                    logger.debug(f"MainView focused on window visible: has_focus={self.main_view.has_focus()}")
                    return False
                GLib.timeout_add(150, focus_main_view)
    
    def _focus_flowbox(self, retry_count=0):
        """Focus the FlowBox."""
        MAX_RETRIES = 10  # Prevent infinite loops
        
        if retry_count >= MAX_RETRIES:
            logger.warning("FlowBox focus failed after maximum retries")
            return False
        
        if hasattr(self.main_view, 'flow_box'):
            flow_box = self.main_view.flow_box
            if flow_box.get_visible():
                # Ensure parent widgets allow focus to pass through
                # ScrolledWindow should allow focus to reach FlowBox
                if hasattr(self.main_view, 'scrolled'):
                    self.main_view.scrolled.set_focusable(False)
                    self.main_view.scrolled.set_can_focus(False)
                
                # MainView should be focusable to receive keyboard events
                # But we'll still try to focus FlowBox for better UX
                self.main_view.set_focusable(True)
                self.main_view.set_can_focus(True)
                
                # Ensure a card is selected (required for keyboard navigation)
                selected = flow_box.get_selected_children()
                if not selected:
                    # No card selected, select the first one
                    first_child = flow_box.get_first_child()
                    if first_child:
                        flow_box.select_child(first_child)
                        logger.debug("Selected first card in _focus_flowbox")
                
                # Ensure FlowBox can receive focus
                flow_box.set_can_focus(True)
                flow_box.set_focusable(True)
                
                # Ensure FlowBox is realized before trying to focus
                if not flow_box.get_realized():
                    logger.debug(f"FlowBox not realized yet, will retry (attempt {retry_count + 1})")
                    GLib.timeout_add(50, lambda: self._focus_flowbox(retry_count + 1))
                    return False  # Don't repeat in this call
                
                # Try to grab focus
                flow_box.grab_focus()
                # Verify focus was actually set
                if flow_box.has_focus():
                    logger.debug("FlowBox focused successfully - has_focus=True")
                    return False  # Success, don't repeat
                else:
                    logger.debug(f"FlowBox grab_focus() called but has_focus() is False - retrying (attempt {retry_count + 1})")
                    # Try again after a short delay if not ready yet
                    GLib.timeout_add(50, lambda: self._focus_flowbox(retry_count + 1))
                    return False  # Don't repeat in this call
            else:
                logger.debug(f"FlowBox not visible yet, will retry (attempt {retry_count + 1})")
                # Try again after a short delay if not visible yet
                GLib.timeout_add(50, lambda: self._focus_flowbox(retry_count + 1))
                return False  # Don't repeat in this call
        else:
            logger.debug("FlowBox not found in main_view")
        return False  # Don't repeat
    
    def _on_stack_visible_child_changed(self, stack, param):
        """Handle stack visible child change - focus MainView when main view is shown."""
        # Update home button icon when view changes
        self._update_home_button_icon()
        
        visible_child = stack.get_visible_child()
        if visible_child == self.main_view:
            # Reset number input when returning to main view
            if hasattr(self.main_view, '_reset_number_input'):
                self.main_view._reset_number_input()
            # Main view is now visible, remove focus from terminal if it has it
            if hasattr(self, 'terminal_view') and self.terminal_view.has_focus():
                # Remove focus from terminal by focusing the window itself temporarily
                self.grab_focus()
                logger.debug("Removed focus from terminal view in stack change")
            
            # Main view is now visible, focus MainView so it can receive keyboard events
            def focus_main_view():
                if hasattr(self.main_view, 'flow_box'):
                    # Ensure MainView is visible and realized
                    if not self.main_view.get_visible() or not self.main_view.get_realized():
                        logger.debug("MainView not ready yet in stack change, will retry")
                        return True  # Retry
                    
                    # Ensure a card is selected
                    selected = self.main_view.flow_box.get_selected_children()
                    if not selected:
                        first_child = self.main_view.flow_box.get_first_child()
                        if first_child:
                            self.main_view.flow_box.select_child(first_child)
                            logger.debug("Selected first card after stack change")
                    
                    # Focus MainView so it can receive keyboard events
                    self.main_view.grab_focus()
                    has_focus = self.main_view.has_focus()
                    logger.debug(f"MainView focused after stack change: has_focus={has_focus}")
                    
                    if not has_focus:
                        # Retry if focus failed
                        return True
                    return False  # Success, don't retry
                return False
            
            # Use multiple timeouts with increasing delays
            GLib.timeout_add(100, focus_main_view)
            GLib.timeout_add(200, focus_main_view)
            GLib.timeout_add(400, focus_main_view)
    
    def _on_settings(self, action, param):
        """Open settings dialog."""
        from commando.dialogs.settings import SettingsDialog
        dialog = SettingsDialog(parent=self)
        dialog.present()
    
    def _on_about(self, action, param):
        """Show about dialog."""
        from commando.dialogs.about import create_about_dialog

        dialog = create_about_dialog()
        dialog.present(self)
    
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
    
    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up window")
        try:
            if hasattr(self, "main_view"):
                logger.debug("Cleaning up main view")
                self.main_view.cleanup()
            if hasattr(self, "terminal_view"):
                logger.debug("Cleaning up terminal view")
                self.terminal_view.cleanup()
            if hasattr(self, "web_view"):
                logger.debug("Cleaning up web view")
                self.web_view.cleanup()
            logger.info("Window cleanup complete")
        except Exception as e:
            logger.error(f"Error during window cleanup: {e}", exc_info=True)
    
    def _on_window_focus_changed(self, window, param):
        """Handle window focus changes - ensure proper focus when returning from external apps."""
        if window.get_has_focus():
            # Window regained focus - set focus immediately to prevent unhandled keyboard events
            current_view = self.stack.get_visible_child_name()
            
            if current_view == "main":
                # In main view - ensure MainView has focus immediately
                if hasattr(self, 'main_view'):
                    # Remove focus from search entry if it's hidden and has focus
                    if hasattr(self.main_view, 'search_revealer') and not self.main_view.search_revealer.get_reveal_child():
                        if hasattr(self.main_view, 'search_entry') and self.main_view.search_entry.has_focus():
                            self.main_view.search_entry.set_focusable(False)
                            self.main_view.search_entry.set_can_focus(False)
                    
                    # Give focus to MainView immediately
                    self.main_view.grab_focus()
                    logger.debug("Gave focus to MainView after window regained focus")
                    
                    # Also ensure it stays focused
                    def ensure_focus():
                        if not self.main_view.has_focus():
                            self.main_view.grab_focus()
                        return False
                    GLib.idle_add(ensure_focus)
            elif current_view == "terminal":
                # In terminal view - ensure terminal has focus
                if hasattr(self, 'terminal_view'):
                    self.terminal_view.focus_current_terminal()
                    logger.debug("Gave focus to terminal after window regained focus")

