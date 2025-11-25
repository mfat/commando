"""
Main view with command cards.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, Gdk

from commando.models.command import Command
from commando.storage.command_storage import CommandStorage
from commando.widgets.command_card import CommandCard
from commando.dialogs.card_editor import CardEditorDialog
from commando.executor import CommandExecutor
from commando.logger import get_logger
from commando.config import Config

logger = get_logger(__name__)


class MainView(Adw.Bin):
    """Main view displaying command cards."""
    
    def __init__(self):
        """Initialize the main view."""
        super().__init__()
        self.storage = CommandStorage()
        self.executor = CommandExecutor()
        self.config = Config()
        self.cards: dict[int, CommandCard] = {}
        
        # Number input for direct card selection
        self.number_input = ""
        self.number_input_timeout_id = None
        
        # Number input for direct card selection
        self.number_input = ""
        self.number_input_timeout_id = None
        
        # Main scrolled window
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        # Make scrolled window expand to fill available space
        self.scrolled.set_vexpand(True)
        self.scrolled.set_hexpand(True)
        
        # Toolbar
        toolbar = self._create_toolbar()
        
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(toolbar)
        main_box.append(self.scrolled)
        
        # Flow box for cards
        self.flow_box = Gtk.FlowBox()
        self.flow_box.set_selection_mode(Gtk.SelectionMode.SINGLE)  # Enable selection for keyboard navigation
        self.flow_box.set_homogeneous(False)  # Don't force equal sizes
        self.flow_box.set_max_children_per_line(4)
        self.flow_box.set_min_children_per_line(1)
        self.flow_box.set_row_spacing(12)
        self.flow_box.set_column_spacing(12)
        self.flow_box.set_margin_start(24)
        self.flow_box.set_margin_end(24)
        self.flow_box.set_margin_top(24)
        self.flow_box.set_margin_bottom(24)
        # Align items to start (top) to prevent stretching
        self.flow_box.set_valign(Gtk.Align.START)
        # Make FlowBox focusable for keyboard navigation
        self.flow_box.set_focusable(True)
        self.flow_box.set_can_focus(True)
        # Prevent FlowBox from expanding children
        # Connect to selection changed to handle Enter key
        self.flow_box.connect("selected-children-changed", self._on_selection_changed)
        # Add keyboard controller for Enter key
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.flow_box.add_controller(key_controller)
        self.flow_box.set_activate_on_single_click(False)
        
        self.scrolled.set_child(self.flow_box)
        
        self.set_child(main_box)
        
        # Load commands
        self._load_commands()
        
        # Keyboard navigation
        self.set_focusable(True)
        self.set_can_focus(True)
    
    def _create_toolbar(self):
        """Create the toolbar with search and controls."""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Search entry wrapped in a revealer (hidden by default)
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search commands...")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self._on_search_changed)
        self.search_entry.connect("activate", self._on_search_activate)
        
        # Wrap search entry in a revealer
        self.search_revealer = Gtk.Revealer()
        self.search_revealer.set_child(self.search_entry)
        self.search_revealer.set_reveal_child(False)  # Hidden by default
        self.search_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.search_revealer.set_margin_start(24)
        self.search_revealer.set_margin_end(24)
        self.search_revealer.set_margin_top(0)
        self.search_revealer.set_margin_bottom(0)
        toolbar.append(self.search_revealer)
        
        # Controls box (sort, layout, new button)
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        controls_box.set_margin_start(24)
        controls_box.set_margin_end(24)
        controls_box.set_margin_top(12)
        controls_box.set_margin_bottom(12)
        
        # Sort combo
        self.sort_combo = Gtk.ComboBoxText()
        self.sort_combo.append("number", "Number")
        self.sort_combo.append("title", "Title")
        self.sort_combo.append("tag", "Tag")
        self.sort_combo.append("category", "Category")
        self.sort_combo.set_active_id("number")
        self.sort_combo.connect("changed", self._on_sort_changed)
        controls_box.append(self.sort_combo)
        
        # Layout toggle (default: grid layout, active state)
        layout_toggle = Gtk.ToggleButton()
        layout_toggle.set_icon_name("view-grid-symbolic")
        layout_toggle.set_tooltip_text("Grid Layout (click for List Layout)")
        layout_toggle.set_active(True)  # Grid is default
        layout_toggle.connect("toggled", self._on_layout_toggled)
        self.layout_toggle = layout_toggle  # Store reference for tooltip updates
        controls_box.append(layout_toggle)
        
        # New command button
        new_button = Gtk.Button(icon_name="list-add-symbolic")
        new_button.set_tooltip_text("New Command")
        new_button.connect("clicked", self._on_new_command)
        controls_box.append(new_button)
        
        toolbar.append(controls_box)
        
        return toolbar
    
    def _load_commands(self):
        """Load and display commands."""
        commands = self.storage.get_all()
        self._sort_commands(commands)
        
        # Clear existing cards - get all children first, then remove them
        # This avoids issues with modifying the container while iterating
        children = []
        child = self.flow_box.get_first_child()
        while child is not None:
            children.append(child)
            child = child.get_next_sibling()
        
        for child in children:
            self.flow_box.remove(child)
        
        self.cards.clear()
        
        # Create cards
        for command in commands:
            # Skip if card already exists (shouldn't happen after clear, but safety check)
            if command.number in self.cards:
                continue
                
            card = CommandCard(
                command,
                on_click=self._on_card_click,
                on_double_click=self._on_card_double_click,
                main_view=self
            )
            self.flow_box.append(card)
            self.cards[command.number] = card
        
        # Select the first card after loading (use idle_add to ensure widgets are allocated)
        GLib.idle_add(self._select_first_card)
    
    def _sort_commands(self, commands: list[Command]):
        """Sort commands based on current sort setting."""
        sort_by = self.config.get("main_view.sort_by", "number")
        ascending = self.config.get("main_view.sort_ascending", True)
        
        if sort_by == "number":
            commands.sort(key=lambda c: c.number, reverse=not ascending)
        elif sort_by == "title":
            commands.sort(key=lambda c: c.title.lower(), reverse=not ascending)
        elif sort_by == "tag":
            commands.sort(key=lambda c: c.tag.lower(), reverse=not ascending)
        elif sort_by == "category":
            commands.sort(key=lambda c: c.category.lower(), reverse=not ascending)
    
    def toggle_search(self):
        """Toggle search bar visibility."""
        current_state = self.search_revealer.get_reveal_child()
        self.search_revealer.set_reveal_child(not current_state)
        if not current_state:
            # Search bar is being shown, focus it
            GLib.idle_add(self.search_entry.grab_focus)
        return not current_state
    
    def _on_search_changed(self, entry):
        """Handle search text changes."""
        query = entry.get_text().lower()
        if not query:
            # Show all cards
            for card in self.cards.values():
                card.set_visible(True)
            # Also show all FlowBoxChildren
            child = self.flow_box.get_first_child()
            while child is not None:
                child.set_visible(True)
                child = child.get_next_sibling()
            # Select first card when search is cleared
            GLib.idle_add(self._select_first_card)
        else:
            # Filter cards - hide both the card and its FlowBoxChild wrapper
            first_visible_child = None
            child = self.flow_box.get_first_child()
            while child is not None:
                card = child.get_child()
                if isinstance(card, CommandCard):
                    command = card.command
                    match = (
                        query in command.title.lower() or
                        query in command.command.lower() or
                        query in (command.tag or "").lower() or
                        query in (command.category or "").lower() or
                        query in str(command.number)
                    )
                    # Hide both the card and its FlowBoxChild wrapper
                    card.set_visible(match)
                    child.set_visible(match)
                    # Track first visible child for selection
                    if match and first_visible_child is None:
                        first_visible_child = child
                child = child.get_next_sibling()
            
            # Select the first matching card
            if first_visible_child:
                self.flow_box.select_child(first_visible_child)
                self._scroll_to_child(first_visible_child)
                # Ensure FlowBox has focus
                GLib.idle_add(self.flow_box.grab_focus)
    
    def _on_search_activate(self, entry):
        """Handle Enter key in search entry - execute first matching command."""
        query = entry.get_text().lower().strip()
        if not query:
            return
        
        # Find the first visible (matching) card in FlowBox order
        # This ensures we get the first match as displayed visually
        child = self.flow_box.get_first_child()
        while child is not None:
            card = child.get_child()
            if isinstance(card, CommandCard) and card.get_visible():
                # Found first matching card, execute it
                logger.info(f"Executing first search match: {card.command.title}")
                self.execute_command(card.command)
                # Clear search and hide search bar
                entry.set_text("")
                self.search_revealer.set_reveal_child(False)
                # Return focus to FlowBox
                GLib.idle_add(self.flow_box.grab_focus)
                break
            child = child.get_next_sibling()
    
    def _on_sort_changed(self, combo):
        """Handle sort change."""
        sort_id = combo.get_active_id()
        self.config.set("main_view.sort_by", sort_id)
        self._load_commands()
    
    def _on_layout_toggled(self, button):
        """Handle layout toggle."""
        if button.get_active():
            # Grid layout (default)
            self.flow_box.set_max_children_per_line(4)
            button.set_tooltip_text("Grid Layout (click for List Layout)")
        else:
            # List layout
            self.flow_box.set_max_children_per_line(1)
            button.set_tooltip_text("List Layout (click for Grid Layout)")
    
    def _on_new_command(self, button):
        """Handle new command button."""
        next_number = self.storage.get_next_number()
        new_command = Command(
            number=next_number,
            title="New Command",
            command="",
        )
        self._edit_command(new_command)
    
    def _on_card_click(self, command: Command):
        """Handle card click - only select, don't execute."""
        logger.debug(f"Card clicked: {command.title}")
        # Single click - just select the card (execution happens on Enter or double-click)
        # Find the FlowBoxChild that contains this card and select it
        card = self.cards.get(command.number)
        if card:
            # Find the FlowBoxChild that contains this card
            for child in self.flow_box:
                if child.get_child() == card:
                    self.flow_box.select_child(child)
                    # Ensure FlowBox has focus so arrow keys work
                    self.flow_box.grab_focus()
                    break
    
    def _on_card_double_click(self, command: Command):
        """Handle card double-click."""
        logger.info(f"Executing command: {command.title}")
        self.execute_command(command)
    
    def _select_first_card(self):
        """Select the first card in the flow box."""
        first_child = self.flow_box.get_child_at_index(0)
        if first_child:
            self.flow_box.select_child(first_child)
            # Don't grab focus here - let the window handle it after it's shown
        return False  # Don't repeat (for GLib.idle_add)
    
    def _on_selection_changed(self, flow_box):
        """Handle selection change in flow box."""
        # When selection changes, ensure FlowBox has focus so arrow keys continue to work
        # This is especially important when bottom terminal is active
        if flow_box.get_selected_children():
            # Use idle_add to ensure focus happens after selection is complete
            GLib.idle_add(self.flow_box.grab_focus)
    
    def _on_key_pressed(self, controller, keyval, keycode, state):
        """Handle keyboard input on flow box."""
        # Check if Enter or Return key was pressed
        if keyval == Gdk.KEY_Return or keyval == Gdk.KEY_KP_Enter:
            selected = self.flow_box.get_selected_children()
            if selected:
                # Get the first selected child
                child = selected[0]
                # Get the card widget from the child
                card = child.get_child()
                if isinstance(card, CommandCard):
                    logger.info(f"Executing command from Enter key: {card.command.title}")
                    self.execute_command(card.command)
                return True  # Event handled
        
        # Handle number key presses for direct card selection
        if self._is_number_key(keyval):
            return self._handle_number_key(keyval)
        
        # Handle arrow key navigation
        elif keyval in (Gdk.KEY_Up, Gdk.KEY_Down, Gdk.KEY_Left, Gdk.KEY_Right, 
                        Gdk.KEY_KP_Up, Gdk.KEY_KP_Down, Gdk.KEY_KP_Left, Gdk.KEY_KP_Right):
            return self._handle_arrow_key(keyval)
        
        return False  # Event not handled
    
    def _is_number_key(self, keyval):
        """Check if keyval is a number key (0-9)."""
        return (Gdk.KEY_0 <= keyval <= Gdk.KEY_9) or (Gdk.KEY_KP_0 <= keyval <= Gdk.KEY_KP_9)
    
    def _get_number_from_keyval(self, keyval):
        """Convert keyval to a number string."""
        if Gdk.KEY_0 <= keyval <= Gdk.KEY_9:
            return str(keyval - Gdk.KEY_0)
        elif Gdk.KEY_KP_0 <= keyval <= Gdk.KEY_KP_9:
            return str(keyval - Gdk.KEY_KP_0)
        return None
    
    def _handle_number_key(self, keyval):
        """Handle number key press for direct card selection."""
        number_str = self._get_number_from_keyval(keyval)
        if number_str is None:
            return False
        
        # Cancel previous timeout
        if self.number_input_timeout_id:
            GLib.source_remove(self.number_input_timeout_id)
            self.number_input_timeout_id = None
        
        # Append to number input
        self.number_input += number_str
        
        # Try to find and select the card
        try:
            number = int(self.number_input)
            card = self.cards.get(number)
            if card:
                # Find the FlowBoxChild that contains this card
                for child in self.flow_box:
                    if child.get_child() == card:
                        self.flow_box.select_child(child)
                        self._scroll_to_child(child)
                        # Ensure FlowBox maintains focus
                        self.flow_box.grab_focus()
                        logger.debug(f"Selected card #{number} via number input")
                        break
        except ValueError:
            pass
        
        # Set timeout to reset number input after 1 second of no input
        self.number_input_timeout_id = GLib.timeout_add(1000, self._reset_number_input)
        
        return True  # Event handled
    
    def _reset_number_input(self):
        """Reset the number input."""
        self.number_input = ""
        self.number_input_timeout_id = None
        return False  # Don't repeat
    
    def _handle_arrow_key(self, keyval):
        """Handle arrow key navigation."""
        selected = self.flow_box.get_selected_children()
        current_child = selected[0] if selected else None
        
        if not current_child:
            # No selection, select first child
            first_child = self.flow_box.get_child_at_index(0)
            if first_child:
                self.flow_box.select_child(first_child)
                self._scroll_to_child(first_child)
            return True
        
        # Get current index
        current_index = current_child.get_index()
        max_children_per_line = self.flow_box.get_max_children_per_line()
        
        # Count total children by iterating
        total_children = 0
        child = self.flow_box.get_first_child()
        while child is not None:
            total_children += 1
            child = child.get_next_sibling()
        
        # Determine next index based on arrow key
        if keyval in (Gdk.KEY_Right, Gdk.KEY_KP_Right):
            # Move right (next card)
            next_index = current_index + 1
            if next_index < total_children:
                next_child = self.flow_box.get_child_at_index(next_index)
                if next_child:
                    self.flow_box.select_child(next_child)
                    self._scroll_to_child(next_child)
                    # Ensure FlowBox maintains focus
                    self.flow_box.grab_focus()
                    return True
        
        elif keyval in (Gdk.KEY_Left, Gdk.KEY_KP_Left):
            # Move left (previous card)
            next_index = current_index - 1
            if next_index >= 0:
                next_child = self.flow_box.get_child_at_index(next_index)
                if next_child:
                    self.flow_box.select_child(next_child)
                    self._scroll_to_child(next_child)
                    # Ensure FlowBox maintains focus
                    self.flow_box.grab_focus()
                    return True
        
        elif keyval in (Gdk.KEY_Down, Gdk.KEY_KP_Down):
            # Move down (next row)
            next_index = current_index + max_children_per_line
            if next_index < total_children:
                next_child = self.flow_box.get_child_at_index(next_index)
                if next_child:
                    self.flow_box.select_child(next_child)
                    self._scroll_to_child(next_child)
                    # Ensure FlowBox maintains focus
                    self.flow_box.grab_focus()
                    return True
        
        elif keyval in (Gdk.KEY_Up, Gdk.KEY_KP_Up):
            # Move up (previous row)
            next_index = current_index - max_children_per_line
            if next_index >= 0:
                next_child = self.flow_box.get_child_at_index(next_index)
                if next_child:
                    self.flow_box.select_child(next_child)
                    self._scroll_to_child(next_child)
                    # Ensure FlowBox maintains focus
                    self.flow_box.grab_focus()
                    return True
        
        return True  # Event handled (even if no movement)
    
    def _scroll_to_child(self, child):
        """Scroll the scrolled window to make the child visible."""
        # Get the allocation of the child
        allocation = child.get_allocation()
        if allocation.height == 0:
            # Child not allocated yet, try again later
            GLib.idle_add(lambda: self._scroll_to_child(child))
            return
        
        # Get the scrolled window
        scrolled = self.scrolled
        
        # Get the adjustment
        vadjustment = scrolled.get_vadjustment()
        if vadjustment:
            # Calculate the position we need to scroll to
            child_y = allocation.y
            child_height = allocation.height
            view_height = vadjustment.get_page_size()
            
            # Get current scroll position
            current_value = vadjustment.get_value()
            
            # Check if child is visible
            if child_y < current_value:
                # Child is above visible area, scroll up
                vadjustment.set_value(child_y)
            elif child_y + child_height > current_value + view_height:
                # Child is below visible area, scroll down
                vadjustment.set_value(child_y + child_height - view_height)
    
    def execute_command(self, command: Command):
        """Execute a command."""
        # Only switch to terminal view if command doesn't have no_terminal flag
        # AND embedded terminal is not available
        if not getattr(command, 'no_terminal', False):
            # Check if embedded terminal is available
            # If it is, don't switch views - command will execute in embedded terminal
            if not hasattr(self.executor, 'embedded_terminal_view') or not self.executor.embedded_terminal_view:
                # No embedded terminal, switch to standalone terminal view
                self._switch_to_terminal_view()
                # Focus the terminal after switching
                self._focus_terminal()
            else:
                # Embedded terminal is available, focus it instead
                self._focus_embedded_terminal()
        # Execute the command
        self.executor.execute(command)
    
    def _focus_terminal(self):
        """Focus the standalone terminal view."""
        # Find the parent window and get standalone terminal view
        parent = self.get_parent()
        while parent is not None:
            if isinstance(parent, Adw.ViewStack):
                # Get the standalone terminal view from the stack
                standalone_terminal_view = parent.get_child_by_name("terminal")
                if standalone_terminal_view and hasattr(standalone_terminal_view, 'focus_current_terminal'):
                    # Use GLib.idle_add to ensure focus happens after view switch
                    GLib.idle_add(standalone_terminal_view.focus_current_terminal)
                break
            parent = parent.get_parent()
    
    def _focus_embedded_terminal(self):
        """Focus the embedded terminal (bottom terminal in main window)."""
        if hasattr(self.executor, 'embedded_terminal_view') and self.executor.embedded_terminal_view:
            # Focus the embedded terminal - use timeout to ensure it's ready
            def focus_terminal():
                if self.executor.embedded_terminal_view:
                    self.executor.embedded_terminal_view.focus_current_terminal()
                return False  # Don't repeat
            
            # Try multiple times with increasing delays to ensure terminal is ready
            GLib.timeout_add(50, focus_terminal)
            GLib.timeout_add(200, focus_terminal)
            GLib.timeout_add(500, focus_terminal)
    
    def _switch_to_terminal_view(self):
        """Switch to the standalone terminal view."""
        # Find the parent Adw.ViewStack
        parent = self.get_parent()
        while parent is not None:
            if isinstance(parent, Adw.ViewStack):
                parent.set_visible_child_name("terminal")
                break
            parent = parent.get_parent()
    
    def get_command_by_number(self, number: int) -> Command | None:
        """Get command by number."""
        return self.storage.get_by_number(number)
    
    def _edit_command(self, command: Command):
        """Open editor for a command."""
        # Get the parent window for modal dialog
        parent = self.get_root()
        dialog = CardEditorDialog(command, parent=parent if isinstance(parent, Gtk.Window) else None)
        dialog.set_saved_callback(lambda cmd: self._on_command_saved(dialog, cmd))
        
        # Present dialog - Adw.Dialog is modal by default when presented
        dialog.present()
    
    def _on_command_saved(self, dialog, command: Command):
        """Handle command saved from editor."""
        # Check if command exists before deciding to add or update
        existing = self.storage.get_by_number(command.number)
        if existing:
            self.storage.update(command)
        else:
            # Only add if it doesn't exist
            if not self.storage.add(command):
                logger.warning(f"Failed to add command #{command.number} - may already exist")
        
        # Reload commands to refresh the view
        self._load_commands()
        
        # Adw.Dialog uses close() instead of destroy()
        dialog.close()
    
    def cleanup(self):
        """Clean up resources."""
        logger.debug("Cleaning up main view")

