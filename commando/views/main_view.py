"""
Main view with command cards.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib

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
        
        # Main scrolled window
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        # Make scrolled window expand to fill available space
        self.scrolled.set_vexpand(True)
        self.scrolled.set_hexpand(True)
        # ScrolledWindow should not take focus - let FlowBox receive it
        self.scrolled.set_focusable(False)
        self.scrolled.set_can_focus(False)
        
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
        self.flow_box.set_activate_on_single_click(False)
        # Connect to selection changed to handle Enter key
        self.flow_box.connect("selected-children-changed", self._on_selection_changed)
        # Add keyboard controller to MainView so it receives events even if FlowBox doesn't have focus
        # This ensures keyboard navigation works even when FlowBox focus fails
        # Use CAPTURE phase to intercept events before they reach child widgets
        key_controller = Gtk.EventControllerKey()
        key_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_controller)
        
        self.scrolled.set_child(self.flow_box)
        
        self.set_child(main_box)
        
        # Load commands
        self._load_commands()
        
        # MainView should be focusable to receive keyboard events for navigation
        # But we'll try to pass focus to FlowBox when possible
        self.set_focusable(True)
        self.set_can_focus(True)
    
    def _create_toolbar(self):
        """Create the toolbar with search and controls."""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        toolbar.set_margin_start(24)
        toolbar.set_margin_end(24)
        toolbar.set_margin_top(12)
        toolbar.set_margin_bottom(12)
        
        # Search entry wrapped in a revealer (hidden by default)
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search commands...")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self._on_search_changed)
        
        # Wrap search entry in a revealer
        self.search_revealer = Gtk.Revealer()
        self.search_revealer.set_child(self.search_entry)
        self.search_revealer.set_reveal_child(False)  # Hidden by default
        self.search_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        toolbar.append(self.search_revealer)
        
        # Sort combo
        self.sort_combo = Gtk.ComboBoxText()
        self.sort_combo.append("number", "Number")
        self.sort_combo.append("title", "Title")
        self.sort_combo.append("tag", "Tag")
        self.sort_combo.append("category", "Category")
        self.sort_combo.set_active_id("number")
        self.sort_combo.connect("changed", self._on_sort_changed)
        toolbar.append(self.sort_combo)
        
        # Layout toggle (default: grid layout, active state)
        layout_toggle = Gtk.ToggleButton()
        layout_toggle.set_icon_name("view-grid-symbolic")
        layout_toggle.set_tooltip_text("Grid Layout (click for List Layout)")
        layout_toggle.set_active(True)  # Grid is default
        layout_toggle.connect("toggled", self._on_layout_toggled)
        self.layout_toggle = layout_toggle  # Store reference for tooltip updates
        toolbar.append(layout_toggle)
        
        # New command button
        new_button = Gtk.Button(icon_name="list-add-symbolic")
        new_button.set_tooltip_text("New Command")
        new_button.connect("clicked", self._on_new_command)
        toolbar.append(new_button)
        
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
        
        # Select first card and focus FlowBox after commands are loaded
        GLib.idle_add(self._select_first_card_and_focus)
    
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
    
    def _on_search_changed(self, entry):
        """Handle search text changes."""
        query = entry.get_text().lower()
        if not query:
            # Show all cards
            for card in self.cards.values():
                card.set_visible(True)
        else:
            # Filter cards
            for number, card in self.cards.items():
                command = card.command
                match = (
                    query in command.title.lower() or
                    query in command.command.lower() or
                    query in command.tag.lower() or
                    query in command.category.lower() or
                    query in str(command.number)
                )
                card.set_visible(match)
    
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
        """Handle card click - select the card only."""
        logger.debug(f"Card clicked: {command.title}")
        # Single click - only select the card, don't execute
        # Find the card in the FlowBox and select it
        card = self.cards.get(command.number)
        if card:
            # Find the FlowBoxChild that contains this card
            for child in self.flow_box:
                if child.get_child() == card:
                    self.flow_box.select_child(child)
                    # Ensure FlowBox has focus for keyboard navigation
                    self.flow_box.grab_focus()
                    logger.debug(f"Card {command.number} selected")
                    break
    
    def _on_card_double_click(self, command: Command):
        """Handle card double-click."""
        logger.info(f"Executing command: {command.title}")
        self.execute_command(command)
    
    def execute_command(self, command: Command):
        """Execute a command."""
        # Only switch to terminal view if command doesn't have no_terminal flag
        if not getattr(command, 'no_terminal', False):
            self._switch_to_terminal_view()
            # Focus the terminal after switching
            self._focus_terminal()
        # Execute the command
        self.executor.execute(command)
    
    def _focus_terminal(self):
        """Focus the terminal view."""
        # Find the parent window and get terminal view
        parent = self.get_parent()
        while parent is not None:
            if isinstance(parent, Adw.ViewStack):
                # Get the terminal view from the stack
                terminal_view = parent.get_child_by_name("terminal")
                if terminal_view and hasattr(terminal_view, 'focus_current_terminal'):
                    # Use GLib.idle_add to ensure focus happens after view switch
                    GLib.idle_add(terminal_view.focus_current_terminal)
                break
            parent = parent.get_parent()
    
    def _switch_to_terminal_view(self):
        """Switch to the terminal view."""
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
    
    def _select_first_card_and_focus(self, retry_count=0):
        """Select the first card and focus the FlowBox."""
        MAX_RETRIES = 10  # Prevent infinite loops
        
        if retry_count >= MAX_RETRIES:
            logger.warning("First card selection and focus failed after maximum retries")
            return False
        
        first_child = self.flow_box.get_first_child()
        if first_child:
            self.flow_box.select_child(first_child)
            # Focus the FlowBox
            if self.flow_box.get_visible() and self.flow_box.get_can_focus():
                self.flow_box.grab_focus()
                logger.debug("First card selected and FlowBox focused")
                return False  # Success, don't repeat
            else:
                # Retry if not ready
                GLib.timeout_add(50, lambda: self._select_first_card_and_focus(retry_count + 1))
                return False  # Don't repeat in this call
        return False  # Don't repeat
    
    def _on_selection_changed(self, flow_box):
        """Handle selection change in flow box."""
        # This is called when selection changes, but we don't need to do anything here
        # The Enter key handler will execute the selected command
        pass
    
    def _on_key_pressed(self, controller, keyval, keycode, state):
        """Handle keyboard input on main view."""
        from gi.repository import Gdk
        
        # Only handle keys when main view is visible and has cards
        if not self.flow_box.get_visible() or len(self.cards) == 0:
            return False
        
        # Check if we're actually in the main view (not in terminal or web view)
        # Get parent window to check current view
        parent = self.get_parent()
        while parent is not None:
            if isinstance(parent, Adw.ViewStack):
                if parent.get_visible_child() != self:
                    # Not in main view, don't handle keys
                    return False
                break
            parent = parent.get_parent()
        
        logger.debug(f"MainView key pressed: keyval={keyval}, main_view_has_focus={self.has_focus()}, flow_box_has_focus={self.flow_box.has_focus()}")
        
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
            else:
                # No selection, select first card
                first_child = self.flow_box.get_first_child()
                if first_child:
                    self.flow_box.select_child(first_child)
                return True
        
        # Handle arrow key navigation
        elif keyval in (Gdk.KEY_Up, Gdk.KEY_Down, Gdk.KEY_Left, Gdk.KEY_Right, 
                        Gdk.KEY_KP_Up, Gdk.KEY_KP_Down, Gdk.KEY_KP_Left, Gdk.KEY_KP_Right):
            logger.debug(f"Arrow key pressed: {keyval}, handling navigation")
            result = self._handle_arrow_key(keyval)
            logger.debug(f"Arrow key handling result: {result}")
            return result
        
        return False  # Event not handled
    
    def _handle_arrow_key(self, keyval):
        """Handle arrow key navigation."""
        from gi.repository import Gdk
        
        # Ensure a card is selected before navigating
        selected = self.flow_box.get_selected_children()
        current_child = selected[0] if selected else None
        
        if not current_child:
            # No selection, select first child
            first_child = self.flow_box.get_first_child()
            if first_child:
                self.flow_box.select_child(first_child)
                self._scroll_to_child(first_child)
                logger.debug("Selected first card in arrow key handler")
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
                    return True
        
        elif keyval in (Gdk.KEY_Left, Gdk.KEY_KP_Left):
            # Move left (previous card)
            next_index = current_index - 1
            if next_index >= 0:
                next_child = self.flow_box.get_child_at_index(next_index)
                if next_child:
                    self.flow_box.select_child(next_child)
                    self._scroll_to_child(next_child)
                    return True
        
        elif keyval in (Gdk.KEY_Down, Gdk.KEY_KP_Down):
            # Move down (next row)
            next_index = current_index + max_children_per_line
            if next_index < total_children:
                next_child = self.flow_box.get_child_at_index(next_index)
                if next_child:
                    self.flow_box.select_child(next_child)
                    self._scroll_to_child(next_child)
                    return True
        
        elif keyval in (Gdk.KEY_Up, Gdk.KEY_KP_Up):
            # Move up (previous row)
            next_index = current_index - max_children_per_line
            if next_index >= 0:
                next_child = self.flow_box.get_child_at_index(next_index)
                if next_child:
                    self.flow_box.select_child(next_child)
                    self._scroll_to_child(next_child)
                    return True
        
        return True  # Event handled (even if no movement)
    
    def _scroll_to_child(self, child):
        """Scroll the scrolled window to make the child visible."""
        # Get the allocation of the child
        allocation = child.get_allocation()
        if allocation.height > 0:
            # Scroll to make the child visible
            self.scrolled.get_vadjustment().set_value(allocation.y)
    
    def cleanup(self):
        """Clean up resources."""
        logger.debug("Cleaning up main view")

