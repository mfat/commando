"""
Terminal view with tabs.
"""

import os
import signal
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Vte", "3.91")

from gi.repository import Gtk, Adw, Vte, GLib, Gdk, Pango, Gio

from commando.logger import get_logger
from commando.config import Config

logger = get_logger(__name__)


class TerminalView(Adw.Bin):
    """Terminal view with tab support."""
    
    def __init__(self):
        """Initialize the terminal view."""
        super().__init__()
        self.config = Config()
        self.terminals: list[Vte.Terminal] = []
        self.terminal_pids: dict[Vte.Terminal, int] = {}  # Store PID for each terminal
        
        # Make TerminalView focusable
        self.set_focusable(True)
        self.set_can_focus(True)
        
        # Tab view
        self.tab_view = Adw.TabView()
        self.tab_overview = Adw.TabOverview()
        self.tab_overview.set_view(self.tab_view)
        
        # Connect to tab view signals to focus terminal when tab is selected
        self.tab_view.connect("notify::selected-page", self._on_tab_selected)
        
        # Add keyboard controller to handle shortcuts even when terminal has focus
        # Use CAPTURE phase to intercept events before they reach child widgets
        key_controller = Gtk.EventControllerKey()
        key_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_controller)
        
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Toolbar
        toolbar = self._create_toolbar()
        main_box.append(toolbar)
        
        # Tab bar
        self.tab_bar = Adw.TabBar(view=self.tab_view)
        main_box.append(self.tab_bar)
        
        # Tab view (the actual content) - make it expand
        self.tab_view.set_vexpand(True)
        self.tab_view.set_hexpand(True)
        main_box.append(self.tab_view)
        
        self.set_child(main_box)
        
        # Don't create initial terminal - create terminals only when commands are executed
    
    def _create_toolbar(self):
        """Create toolbar for terminal."""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        toolbar.set_margin_start(12)
        toolbar.set_margin_end(12)
        toolbar.set_margin_top(12)
        toolbar.set_margin_bottom(12)
        
        # New tab button
        new_tab_btn = Gtk.Button(icon_name="tab-new-symbolic")
        new_tab_btn.set_tooltip_text("New Tab")
        new_tab_btn.connect("clicked", lambda _: self._create_terminal_tab())
        toolbar.append(new_tab_btn)
        
        # Close tab button
        close_tab_btn = Gtk.Button(icon_name="window-close-symbolic")
        close_tab_btn.set_tooltip_text("Close Tab")
        close_tab_btn.connect("clicked", self._on_close_tab)
        toolbar.append(close_tab_btn)
        
        toolbar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        
        # Settings button
        settings_btn = Gtk.Button(icon_name="emblem-system-symbolic")
        settings_btn.set_tooltip_text("Terminal Settings")
        settings_btn.connect("clicked", self._on_settings)
        toolbar.append(settings_btn)
        
        return toolbar
    
    def _create_terminal_tab(self, command_to_execute: str = None):
        """
        Create a new terminal tab.
        
        Args:
            command_to_execute: Optional command to execute once terminal is ready
        """
        try:
            # Create terminal
            terminal = Vte.Terminal()
            terminal.set_size(80, 24)
            
            # Make terminal focusable and ensure it can receive keyboard input
            terminal.set_focusable(True)
            terminal.set_can_focus(True)
            # Ensure terminal receives keyboard events
            terminal.set_can_target(True)
            
            # Add keyboard controller to intercept Ctrl+Shift+E even when terminal has focus
            # Use CAPTURE phase to intercept events before VTE processes them
            terminal_key_controller = Gtk.EventControllerKey()
            terminal_key_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
            terminal_key_controller.connect("key-pressed", self._on_terminal_key_pressed)
            terminal.add_controller(terminal_key_controller)
            
            # Configure terminal
            self._configure_terminal(terminal)
            
            # Spawn shell - use user's default shell from $SHELL
            # This ensures zsh, fish, or other shells work correctly
            shell = GLib.getenv("SHELL")
            if not shell:
                # Try to find a shell in common locations
                for shell_path in ["/bin/zsh", "/bin/bash", "/usr/bin/zsh", "/usr/bin/bash", "/bin/sh"]:
                    if os.path.exists(shell_path) and os.access(shell_path, os.X_OK):
                        shell = shell_path
                        break
                # Final fallback
                if not shell:
                    shell = "/bin/bash"
            
            # For bash and zsh, spawn as login shell to read .bashrc/.zshrc
            # For other shells, check if they support -l flag
            shell_name = os.path.basename(shell) if shell else "bash"
            if shell_name in ["bash", "zsh"]:
                shell_args = [shell, "-l"]
            else:
                # For other shells (fish, etc.), just use the shell
                # They typically read their config automatically
                shell_args = [shell]
            
            logger.debug(f"Spawning shell: {' '.join(shell_args)} (from $SHELL={GLib.getenv('SHELL')})")
            
            # Callback to execute command once terminal is ready
            # VTE spawn_async callback signature: (terminal, pid, error, user_data)
            def on_spawn_complete(terminal, pid, error, user_data):
                if pid > 0 and error is None:
                    # Store the child PID for later cleanup
                    # The PID is passed directly as the second parameter
                    self.terminal_pids[terminal] = pid
                    logger.info(f"Stored PID {pid} for terminal in spawn callback")
                    
                    if command_to_execute:
                        # Small delay to ensure shell is ready
                        def execute_cmd():
                            try:
                                terminal.feed_child(command_to_execute.encode() + b"\n")
                                # Ensure terminal can receive focus
                                terminal.set_focusable(True)
                                terminal.set_can_focus(True)
                                terminal.set_can_target(True)
                                # Focus the terminal with multiple attempts
                                def focus_terminal():
                                    terminal.grab_focus()
                                    logger.debug(f"Focused terminal after command execution: {command_to_execute}")
                                    return False
                                # Try focusing immediately and with delays
                                GLib.idle_add(focus_terminal)
                                GLib.timeout_add(50, focus_terminal)
                                GLib.timeout_add(200, focus_terminal)
                                logger.info(f"Executed command in new terminal tab: {command_to_execute}")
                            except Exception as e:
                                logger.error(f"Failed to execute command in terminal: {e}")
                            return False  # Don't repeat
                        GLib.timeout_add(100, execute_cmd)  # 100ms delay
                elif error:
                    logger.error(f"Failed to spawn terminal: {error}")
            
            terminal.spawn_async(
                Vte.PtyFlags.DEFAULT,
                None,  # working_directory - None means use current directory
                shell_args,
                None,  # envv - None means inherit environment (includes $SHELL)
                GLib.SpawnFlags.DEFAULT,
                None,  # child_setup
                None,  # child_setup_data
                -1,    # timeout_ms
                None,  # cancellable
                on_spawn_complete,  # callback when spawn completes
                None   # user_data
            )
            
            # Wrap terminal in a box for proper sizing
            terminal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            terminal_box.append(terminal)
            
            # Create page
            page = self.tab_view.append(terminal_box)
            page.set_title("Terminal")
            icon = Gio.ThemedIcon.new("terminal-symbolic")
            page.set_icon(icon)
            
            self.terminals.append(terminal)
            
            # Set as current page (this will be done automatically by append, but ensure it)
            self.tab_view.set_selected_page(page)
            
            # If no command to execute, focus the terminal after creation
            if not command_to_execute:
                # Focus the terminal after a short delay to ensure it's ready
                def focus_new_terminal():
                    terminal.set_focusable(True)
                    terminal.set_can_focus(True)
                    terminal.set_can_target(True)
                    terminal.grab_focus()
                    logger.debug("Focused new terminal tab")
                    return False
                GLib.timeout_add(200, focus_new_terminal)
            
            logger.info("Created new terminal tab")
            
            return terminal  # Return terminal for potential use
        except Exception as e:
            logger.error(f"Failed to create terminal tab: {e}", exc_info=True)
            # Create a placeholder instead of failing completely
            terminal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            placeholder = Gtk.Label(label="Terminal unavailable")
            placeholder.set_halign(Gtk.Align.CENTER)
            placeholder.set_valign(Gtk.Align.CENTER)
            terminal_box.append(placeholder)
            
            # Create page
            page = self.tab_view.append(terminal_box)
            page.set_title("Terminal")
            icon = Gio.ThemedIcon.new("terminal-symbolic")
            page.set_icon(icon)
    
    def _configure_terminal(self, terminal: Vte.Terminal):
        """Configure terminal appearance and behavior."""
        # Font
        font_str = self.config.get("terminal.font", "Monospace 12")
        try:
            font_desc = Pango.FontDescription.from_string(font_str)
            terminal.set_font(font_desc)
        except Exception as e:
            logger.warning(f"Failed to set font '{font_str}': {e}")
            # Use default font
            font_desc = Pango.FontDescription.from_string("Monospace 12")
            terminal.set_font(font_desc)
        
        # Scrollback
        scrollback = self.config.get("terminal.scrollback_lines", 10000)
        terminal.set_scrollback_lines(scrollback)
        
        # Cursor
        cursor_blink = self.config.get("terminal.cursor_blink", True)
        terminal.set_cursor_blink_mode(
            Vte.CursorBlinkMode.ON if cursor_blink else Vte.CursorBlinkMode.OFF
        )
        
        cursor_shape_str = self.config.get("terminal.cursor_shape", "block")
        cursor_shape_map = {
            "block": Vte.CursorShape.BLOCK,
            "ibeam": Vte.CursorShape.IBEAM,
            "underline": Vte.CursorShape.UNDERLINE,
        }
        terminal.set_cursor_shape(cursor_shape_map.get(cursor_shape_str, Vte.CursorShape.BLOCK))
        
        # Colors
        bg_color = self.config.get("terminal.background_color")
        fg_color = self.config.get("terminal.foreground_color")
        
        if bg_color:
            bg = Gdk.RGBA()
            bg.parse(bg_color)
            terminal.set_color_background(bg)
        
        if fg_color:
            fg = Gdk.RGBA()
            fg.parse(fg_color)
            terminal.set_color_foreground(fg)
        
        # Palette
        palette_str = self.config.get("terminal.palette")
        if palette_str:
            palette = [Gdk.RGBA() for _ in range(16)]
            colors = palette_str.split(":")
            for i, color_str in enumerate(colors[:16]):
                if color_str:
                    palette[i].parse(color_str)
            terminal.set_colors(None, None, palette)
    
    def _on_close_tab(self, button):
        """Close current tab."""
        page = self.tab_view.get_selected_page()
        if page:
            child = page.get_child()
            # Terminal is wrapped in a box
            if isinstance(child, Gtk.Box) and child.get_first_child():
                terminal = child.get_first_child()
                if isinstance(terminal, Vte.Terminal) and terminal in self.terminals:
                    self.terminals.remove(terminal)
            self.tab_view.close_page(page)
    
    def _on_settings(self, button):
        """Open terminal settings."""
        # This would open a settings dialog
        logger.debug("Terminal settings clicked")
    
    def execute_command(self, command: str, create_new_tab: bool = True):
        """
        Execute a command in a terminal.
        
        Args:
            command: Command to execute
            create_new_tab: If True, create a new tab for this command. If False, use current tab.
        """
        if create_new_tab:
            # Create a new terminal tab with the command to execute
            # The command will be executed once the terminal is ready
            self._create_terminal_tab(command_to_execute=command)
        else:
            # Use current tab and execute immediately
            page = self.tab_view.get_selected_page()
            if page:
                child = page.get_child()
                # Terminal is wrapped in a box
                if isinstance(child, Gtk.Box) and child.get_first_child():
                    terminal = child.get_first_child()
                    if isinstance(terminal, Vte.Terminal):
                        # Execute the command
                        terminal.feed_child(command.encode() + b"\n")
                        # Give focus to the terminal so user can interact with it
                        terminal.grab_focus()
                        logger.info(f"Executed command in terminal: {command}")
    
    def _on_tab_selected(self, tab_view, param):
        """Handle tab selection change - focus the terminal in the selected tab."""
        GLib.idle_add(self.focus_current_terminal)
    
    def _on_key_pressed(self, controller, keyval, keycode, state):
        """Handle keyboard input - intercept Ctrl+Shift+E to toggle views."""
        logger.debug(f"TerminalView._on_key_pressed: keyval={keyval}, state={state}")
        result = self._handle_toggle_shortcut(keyval, state)
        if result:
            return True  # Event handled
        return False  # Event not handled
    
    def _on_terminal_key_pressed(self, controller, keyval, keycode, state):
        """Handle keyboard input on terminal widget - intercept Ctrl+Shift+E."""
        # This is called when the terminal widget itself has focus
        logger.debug(f"Vte.Terminal._on_terminal_key_pressed: keyval={keyval}, state={state}")
        if self._handle_toggle_shortcut(keyval, state):
            return True  # Event handled, prevent terminal from processing it
        return False  # Let terminal process the event
    
    def _handle_toggle_shortcut(self, keyval, state):
        """Handle Ctrl+Shift+E shortcut to toggle views."""
        # Check for Ctrl+Shift+E (E key with Ctrl and Shift modifiers)
        ctrl_mask = Gdk.ModifierType.CONTROL_MASK
        shift_mask = Gdk.ModifierType.SHIFT_MASK
        
        if (keyval == Gdk.KEY_e or keyval == Gdk.KEY_E) and \
           (state & ctrl_mask) and (state & shift_mask):
            # Find the parent window and call the toggle method
            # Pass self so the window knows which terminal triggered it
            parent = self.get_root()
            logger.debug(f"Ctrl+Shift+E pressed in terminal, parent: {parent}, has toggle method: {hasattr(parent, '_toggle_cards_terminal') if parent else False}")
            if parent and hasattr(parent, '_toggle_cards_terminal'):
                parent._toggle_cards_terminal(from_terminal=self)
                return True  # Event handled
            else:
                logger.warning(f"Could not find parent window or toggle method. Parent: {parent}")
        return False  # Event not handled
    
    def focus_current_terminal(self):
        """Focus the current terminal tab."""
        # If no tabs exist, create one first
        if self.tab_view.get_n_pages() == 0:
            self._create_terminal_tab()
            # Use a timeout to focus after the terminal is created
            GLib.timeout_add(200, self._focus_terminal_after_creation)
            return True
        
        page = self.tab_view.get_selected_page()
        if page:
            child = page.get_child()
            # Terminal is wrapped in a box
            if isinstance(child, Gtk.Box) and child.get_first_child():
                terminal = child.get_first_child()
                if isinstance(terminal, Vte.Terminal):
                    # Ensure terminal can receive focus and keyboard input
                    terminal.set_focusable(True)
                    terminal.set_can_focus(True)
                    terminal.set_can_target(True)
                    # Focus the terminal
                    terminal.grab_focus()
                    logger.debug("Terminal focused")
                    # Also ensure the TerminalView itself can receive focus
                    self.set_focusable(True)
                    self.set_can_focus(True)
                    return True
        
        # If no terminal found, try to create one and focus it
        if self.tab_view.get_n_pages() == 0:
            self._create_terminal_tab()
            GLib.timeout_add(200, self._focus_terminal_after_creation)
        
        return False
    
    def _focus_terminal_after_creation(self):
        """Focus terminal after it's been created (callback for timeout)."""
        page = self.tab_view.get_selected_page()
        if page:
            child = page.get_child()
            if isinstance(child, Gtk.Box) and child.get_first_child():
                terminal = child.get_first_child()
                if isinstance(terminal, Vte.Terminal):
                    terminal.set_focusable(True)
                    terminal.set_can_focus(True)
                    terminal.set_can_target(True)
                    terminal.grab_focus()
                    logger.debug("Terminal focused after creation")
                    # Also ensure the TerminalView itself can receive focus
                    self.set_focusable(True)
                    self.set_can_focus(True)
                    return False  # Don't repeat
        return False  # Don't repeat
    
    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up terminal view")
        
        # Close all terminal tabs
        try:
            # Get all pages and close them
            pages = []
            n_pages = self.tab_view.get_n_pages()
            logger.info(f"Closing {n_pages} terminal tab(s)")
            
            for i in range(n_pages):
                page = self.tab_view.get_nth_page(i)
                if page:
                    pages.append(page)
            
            for idx, page in enumerate(pages):
                try:
                    child = page.get_child()
                    if isinstance(child, Gtk.Box) and child.get_first_child():
                        terminal = child.get_first_child()
                        if isinstance(terminal, Vte.Terminal):
                            logger.info(f"Closing terminal {idx + 1}/{len(pages)}")
                            
                            # Get child PID from stored dict or try to get it from PTY
                            child_pid = None
                            
                            # First, try to get from stored PIDs
                            if terminal in self.terminal_pids:
                                child_pid = self.terminal_pids[terminal]
                                logger.info(f"Found stored PID {child_pid} for terminal {idx + 1}")
                            else:
                                logger.debug(f"Terminal {idx + 1} not found in stored PIDs (total stored: {len(self.terminal_pids)})")
                            
                            # Note: We can't get PID from PTY object directly in VTE 3.91
                            # The PID must be stored when the terminal spawns via the callback
                            
                            # Kill the process if we have a PID
                            if child_pid and child_pid > 0:
                                logger.info(f"Terminating child process {child_pid} for terminal {idx + 1}")
                                
                                # Try to get the process group ID and kill the entire group
                                # This ensures all child processes are terminated
                                try:
                                    pgid = os.getpgid(child_pid)
                                    logger.info(f"Process group ID: {pgid} for PID {child_pid}")
                                    
                                    # Kill the entire process group with SIGTERM first
                                    try:
                                        os.killpg(pgid, signal.SIGTERM)
                                        logger.info(f"Sent SIGTERM to process group {pgid}")
                                    except ProcessLookupError:
                                        logger.info(f"Process group {pgid} already terminated")
                                    except Exception as e:
                                        logger.warning(f"Error sending SIGTERM to process group {pgid}: {e}")
                                    
                                    # Also send SIGKILL to the process group (force kill)
                                    try:
                                        os.killpg(pgid, signal.SIGKILL)
                                        logger.info(f"Sent SIGKILL to process group {pgid}")
                                    except ProcessLookupError:
                                        logger.info(f"Process group {pgid} already terminated")
                                    except Exception as e:
                                        logger.warning(f"Error sending SIGKILL to process group {pgid}: {e}")
                                except (ProcessLookupError, OSError):
                                    # Process doesn't exist or we can't get PGID, try killing just the PID
                                    logger.debug(f"Could not get process group, killing PID {child_pid} directly")
                                    try:
                                        os.kill(child_pid, signal.SIGTERM)
                                        os.kill(child_pid, signal.SIGKILL)
                                        logger.info(f"Killed process {child_pid} directly")
                                    except ProcessLookupError:
                                        logger.info(f"Process {child_pid} already terminated")
                                    except Exception as e:
                                        logger.warning(f"Error killing process {child_pid}: {e}")
                            else:
                                logger.warning(f"Could not get child PID for terminal {idx + 1}")
                            
                            # Note: In VTE, we don't need to explicitly close the PTY.
                            # Killing the child process will cause the PTY to close automatically.
                            # The terminal will clean up when the process is terminated.
                            
                            # Remove from stored PIDs
                            if terminal in self.terminal_pids:
                                del self.terminal_pids[terminal]
                except Exception as e:
                    logger.warning(f"Error closing terminal page {idx + 1}: {e}")
        except Exception as e:
            logger.error(f"Error during terminal cleanup: {e}", exc_info=True)
        
        # Clear the terminals list
        self.terminals.clear()
        logger.info("Terminal view cleanup complete")

