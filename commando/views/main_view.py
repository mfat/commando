"""
Main view with command cards.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, GObject

from commando.models.command import Command
from commando.storage.command_storage import CommandStorage
from commando.storage.default_commands import is_default_command
from commando.widgets.command_card import CommandCard
from commando.dialogs.card_editor import CardEditorDialog
from commando.executor import CommandExecutor
from commando.logger import get_logger
from commando.config import Config

logger = get_logger(__name__)


class MainView(Adw.Bin):
    """Main view displaying command cards with Bazaar-style navigation."""
    
    def __init__(self):
        """Initialize the main view."""
        super().__init__()
        self.storage = CommandStorage()
        self.executor = CommandExecutor()
        self.config = Config()
        self.cards: dict[int, CommandCard] = {}
        self.number_input = ""  # Track number input for card selection
        self.number_input_timeout_id = None  # Timeout ID for resetting number input
        self.current_category = "all"  # Track current category
        
        # Create category stack for navigation (Bazaar-style)
        self.category_stack = Adw.ViewStack()
        self.category_stack.set_transition_duration(300)
        # Enable transitions (if available in this version)
        try:
            self.category_stack.set_transition_type(Adw.ViewStackTransitionType.SLIDE)
        except AttributeError:
            pass  # Not available in this version
        
        # Create category views first (needed for toggles)
        self._create_category_views()
        
        # Create toggle buttons box (Bazaar-style)
        section_toggles_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        section_toggles_box.set_halign(Gtk.Align.CENTER)
        section_toggles_box.set_size_request(800, -1)  # width-request: 800
        section_toggles_box.set_margin_top(12)
        section_toggles_box.set_margin_bottom(12)
        section_toggles_box.set_hexpand(True)  # Allow horizontal expansion
        
        # Create Adw.ToggleGroup (exactly like Bazaar)
        self.toggle_group = Adw.ToggleGroup()
        self.toggle_group.set_hexpand(True)
        self.toggle_group.set_halign(Gtk.Align.FILL)
        self.toggle_group.set_homogeneous(True)  # Make buttons equal size like Bazaar
        # Apply the exact same CSS classes as Bazaar's ToggleGroup
        self.toggle_group.add_css_class("round")
        self.toggle_group.add_css_class("huge")
        
        # Create Adw.Toggle widgets (exactly like Bazaar)
        self.trending_toggle = Adw.Toggle(label="Trending")
        self.trending_toggle.set_name("trending")
        self.toggle_group.add(self.trending_toggle)
        
        self.popular_toggle = Adw.Toggle(label="Popular")
        self.popular_toggle.set_name("popular")
        self.toggle_group.add(self.popular_toggle)
        
        self.new_toggle = Adw.Toggle(label="New")
        self.new_toggle.set_name("new")
        self.toggle_group.add(self.new_toggle)
        
        self.updated_toggle = Adw.Toggle(label="Updated")
        self.updated_toggle.set_name("updated")
        self.toggle_group.add(self.updated_toggle)
        
        # Apply Bazaar-style CSS (exact CSS from Bazaar)
        self._apply_toggle_styles()
        
        # Add toggle group to the box
        section_toggles_box.append(self.toggle_group)
        
        # Set default active toggle by name (Adw.ToggleGroup manages active state)
        self.toggle_group.set_active_name("trending")
        
        # Bind ViewStack to ToggleGroup bidirectionally (exactly like Bazaar)
        # visible-child-name: bind section_toggles.active-name bidirectional
        self.toggle_group.bind_property(
            "active-name", 
            self.category_stack, 
            "visible-child-name",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE
        )
        
        # Also connect to handle category loading
        self.category_stack.connect("notify::visible-child-name", self._on_stack_changed)
        
        # Toolbar
        toolbar = self._create_toolbar()
        
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(toolbar)
        main_box.append(section_toggles_box)
        main_box.append(self.category_stack)
        
        self.set_child(main_box)
        
        # Load commands
        self._load_commands()
        
        # MainView should be focusable to receive keyboard events for navigation
        self.set_focusable(True)
        self.set_can_focus(True)
        
        # Reset number input when view becomes visible
        self.connect("notify::visible", self._on_visibility_changed)
        
        # Connect to stack changes to update current category
        self.category_stack.connect("notify::visible-child", self._on_category_changed)
    
    def _create_category_views(self):
        """Create views for each category (Bazaar-style)."""
        # Trending view
        self.trending_view = self._create_card_view("trending")
        self.category_stack.add_titled(self.trending_view, "trending", "Trending")
        
        # Popular view
        self.popular_view = self._create_card_view("popular")
        self.category_stack.add_titled(self.popular_view, "popular", "Popular")
        
        # New view
        self.new_view = self._create_card_view("new")
        self.category_stack.add_titled(self.new_view, "new", "New")
        
        # Updated view
        self.updated_view = self._create_card_view("updated")
        self.category_stack.add_titled(self.updated_view, "updated", "Updated")
        
        # Set default view
        self.category_stack.set_visible_child_name("trending")
    
    def _create_card_view(self, category_name: str) -> Adw.Bin:
        """Create a card view for a specific category."""
        view = Adw.Bin()
        
        # Main scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_focusable(False)
        scrolled.set_can_focus(False)
        
        # Flow box for cards (Bazaar-style - uniform card sizes)
        flow_box = Gtk.FlowBox()
        flow_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        flow_box.set_homogeneous(True)  # Make all cards the same size (Bazaar-style)
        flow_box.set_max_children_per_line(4)
        flow_box.set_min_children_per_line(1)
        flow_box.set_row_spacing(12)
        flow_box.set_column_spacing(12)
        flow_box.set_margin_start(24)
        flow_box.set_margin_end(24)
        flow_box.set_margin_top(24)
        flow_box.set_margin_bottom(24)
        flow_box.set_valign(Gtk.Align.START)
        flow_box.set_focusable(True)
        flow_box.set_can_focus(True)
        flow_box.set_activate_on_single_click(False)
        flow_box.connect("selected-children-changed", self._on_selection_changed)
        
        scrolled.set_child(flow_box)
        view.set_child(scrolled)
        
        # Store flow_box reference in view
        view.flow_box = flow_box
        view.scrolled = scrolled
        view.category_name = category_name
        
        return view
    
    def _apply_toggle_styles(self):
        """Apply Bazaar-style CSS to toggle buttons and cards (exact CSS from Bazaar)."""
        css = """
        /* Exact CSS from Bazaar - line 299-306 of style.css */
        toggle-group.huge,
        toggle-group.huge * {
            border-radius: 9999px;
        }
        
        .huge > toggle {
            padding: 3px 12px;
        }
        
        /* Bazaar-style card styling */
        flowbox > child {
            padding: 0;
            margin: 6px 6px;
            border-radius: 12px;
            transition: background-color 200ms;
        }
        
        button.card.app-tile {
            border-radius: 12px;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        
        # Apply to the main view so it cascades to children
        context = self.get_style_context()
        context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
    def _on_stack_changed(self, stack, param):
        """Handle stack visible child change (Bazaar-style)."""
        visible_child_name = stack.get_visible_child_name()
        if visible_child_name:
            self.current_category = visible_child_name
            self._load_commands_for_category(visible_child_name)
    
    def _on_category_changed(self, stack, param):
        """Handle category change (legacy method, kept for compatibility)."""
        self._on_stack_changed(stack, param)
    
    def _get_current_flow_box(self):
        """Get the flow box for the current category."""
        visible_child = self.category_stack.get_visible_child()
        if visible_child and hasattr(visible_child, 'flow_box'):
            return visible_child.flow_box
        return self.trending_view.flow_box  # Fallback to trending view
    
    def _get_current_scrolled(self):
        """Get the scrolled window for the current category."""
        visible_child = self.category_stack.get_visible_child()
        if visible_child and hasattr(visible_child, 'scrolled'):
            return visible_child.scrolled
        return self.trending_view.scrolled  # Fallback to trending view
    
    def _on_visibility_changed(self, widget, param):
        """Handle visibility changes - reset number input when view becomes visible."""
        if self.get_visible():
            self._reset_number_input()
            logger.debug("MainView became visible, reset number input")
            # Ensure keyboard controller is active by ensuring MainView can receive focus
            if not self.has_focus():
                # Try to grab focus to ensure keyboard events are received
                GLib.idle_add(self.grab_focus)
    
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
        self.search_entry.connect("activate", self._on_search_activate)
        
        # Wrap search entry in a revealer for smooth animation
        self.search_revealer = Gtk.Revealer()
        self.search_revealer.set_child(self.search_entry)
        self.search_revealer.set_reveal_child(False)  # Hidden by default
        # Use CROSSFADE for smoother animation in horizontal toolbar
        self.search_revealer.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
        # Set transition duration for smooth animation (default is 250ms, but we can make it smoother)
        self.search_revealer.set_transition_duration(200)  # 200ms for smooth but responsive animation
        # Don't reserve space when hidden
        self.search_revealer.set_vexpand(False)
        self.search_revealer.set_hexpand(True)  # Allow to expand horizontally
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
        """Load and display commands for all categories."""
        # Load commands for the current category
        current_category = self.category_stack.get_visible_child_name() or "all"
        self._load_commands_for_category(current_category)
    
    def _load_commands_for_category(self, category_name: str):
        """Load and display commands for a specific category."""
        # Get the view for this category
        view = self.category_stack.get_child_by_name(category_name)
        if not view or not hasattr(view, 'flow_box'):
            return
        
        flow_box = view.flow_box
        
        # Get all commands
        commands = self.storage.get_all()
        
        # Filter out default commands if setting is disabled
        show_defaults = self.config.get("general.show_default_cards", True)
        if not show_defaults:
            commands = [cmd for cmd in commands if not is_default_command(cmd)]
        
        # Filter commands by category
        commands = self._filter_commands_by_category(commands, category_name)
        
        self._sort_commands(commands)
        
        # Clear existing cards
        children = []
        child = flow_box.get_first_child()
        while child is not None:
            children.append(child)
            child = child.get_next_sibling()
        
        for child in children:
            flow_box.remove(child)
        
        # Create cards for this category
        for command in commands:
            # Reuse existing card if available, otherwise create new one
            if command.number in self.cards:
                card = self.cards[command.number]
            else:
                card = CommandCard(
                    command,
                    on_click=self._on_card_click,
                    on_double_click=self._on_card_double_click,
                    main_view=self
                )
                self.cards[command.number] = card
            
            flow_box.append(card)
        
        # Select first card and focus FlowBox after commands are loaded
        GLib.idle_add(lambda: self._select_first_card_and_focus(flow_box))
    
    def _filter_commands_by_category(self, commands: list[Command], category_name: str) -> list[Command]:
        """Filter commands based on category name (Bazaar-style categories)."""
        if category_name == "trending":
            # For trending, return all commands (can be enhanced with usage metrics)
            return commands
        elif category_name == "popular":
            # For popular, return all commands (can be enhanced with popularity metrics)
            return commands
        elif category_name == "new":
            # For new, return all commands (can be enhanced with creation date)
            return commands
        elif category_name == "updated":
            # For updated, return all commands (can be enhanced with modification date)
            return commands
        return commands
    
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
        flow_box = self._get_current_flow_box()
        query = entry.get_text().lower()
        if not query:
            # Show all cards - iterate through FlowBox children to show both card and wrapper
            for child in flow_box:
                card = child.get_child()
                if isinstance(card, CommandCard):
                    child.set_visible(True)
                    card.set_visible(True)
            # Select first card when search is cleared
            first_child = flow_box.get_first_child()
            if first_child:
                flow_box.select_child(first_child)
        else:
            # Filter cards - hide/show both FlowBoxChild and card
            first_visible_child = None
            for child in flow_box:
                card = child.get_child()
                if isinstance(card, CommandCard):
                    command = card.command
                    # Handle None values for tag and category
                    tag = command.tag.lower() if command.tag else ""
                    category = command.category.lower() if command.category else ""
                    match = (
                        query in command.title.lower() or
                        query in command.command.lower() or
                        query in tag or
                        query in category or
                        query in str(command.number)
                    )
                    # Set visibility on both the FlowBoxChild wrapper and the card itself
                    child.set_visible(match)
                    card.set_visible(match)
                    # Track first visible card for selection
                    if match and first_visible_child is None:
                        first_visible_child = child
            
            # Select first visible card after filtering
            if first_visible_child:
                flow_box.select_child(first_visible_child)
    
    def _on_search_activate(self, entry):
        """Handle Enter key press in search entry - execute first matching command."""
        flow_box = self._get_current_flow_box()
        # Get the first visible card and execute it
        for child in flow_box:
            if child.get_visible():
                card = child.get_child()
                if isinstance(card, CommandCard):
                    logger.info(f"Executing command from search Enter: {card.command.title}")
                    self.execute_command(card.command)
                    # Clear search and hide search bar
                    entry.set_text("")
                    if hasattr(self, 'search_revealer'):
                        self.search_revealer.set_reveal_child(False)
                    break
    
    def _on_sort_changed(self, combo):
        """Handle sort change."""
        sort_id = combo.get_active_id()
        self.config.set("main_view.sort_by", sort_id)
        self._load_commands()
    
    def _on_layout_toggled(self, button):
        """Handle layout toggle."""
        flow_box = self._get_current_flow_box()
        if button.get_active():
            # Grid layout (default)
            flow_box.set_max_children_per_line(4)
            button.set_tooltip_text("Grid Layout (click for List Layout)")
        else:
            # List layout
            flow_box.set_max_children_per_line(1)
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
        flow_box = self._get_current_flow_box()
        # Single click - only select the card, don't execute
        # Find the card in the FlowBox and select it
        card = self.cards.get(command.number)
        if card:
            # Find the FlowBoxChild that contains this card
            for child in flow_box:
                if child.get_child() == card:
                    flow_box.select_child(child)
                    # Ensure FlowBox has focus for keyboard navigation
                    flow_box.grab_focus()
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
    
    def _select_first_card_and_focus(self, flow_box=None, retry_count=0):
        """Select the first card and focus the FlowBox."""
        if flow_box is None:
            flow_box = self._get_current_flow_box()
        MAX_RETRIES = 10  # Prevent infinite loops
        
        if retry_count >= MAX_RETRIES:
            logger.warning("First card selection and focus failed after maximum retries")
            return False
        
        first_child = flow_box.get_first_child()
        if first_child:
            flow_box.select_child(first_child)
            # Focus the FlowBox
            if flow_box.get_visible() and flow_box.get_can_focus():
                flow_box.grab_focus()
                logger.debug("First card selected and FlowBox focused")
                return False  # Success, don't repeat
            else:
                # Retry if not ready
                GLib.timeout_add(50, lambda: self._select_first_card_and_focus(flow_box, retry_count + 1))
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
        
        flow_box = self._get_current_flow_box()
        
        # Log ALL key presses at the very start to debug
        logger.debug(f"MainView._on_key_pressed START: keyval={keyval}, flow_box_visible={flow_box.get_visible()}, cards_count={len(self.cards)}, main_view_has_focus={self.has_focus()}")
        
        # Only handle keys when main view is visible and has cards
        if not flow_box.get_visible() or len(self.cards) == 0:
            logger.debug("Skipping: flow_box not visible or no cards")
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
        
        logger.debug(f"MainView key pressed: keyval={keyval}, main_view_has_focus={self.has_focus()}, flow_box_has_focus={flow_box.has_focus()}, number_input='{self.number_input}'")
        
        # Handle number keys for card selection (check this first, before other keys)
        if self._is_number_key(keyval):
            number = self._get_number_from_keyval(keyval)
            if number is not None:
                logger.debug(f"Number key detected: {number}, current input: '{self.number_input}'")
                self._handle_number_key(number)
                return True
        
        # Check if Enter or Return key was pressed
        if keyval == Gdk.KEY_Return or keyval == Gdk.KEY_KP_Enter:
            selected = flow_box.get_selected_children()
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
                first_child = flow_box.get_first_child()
                if first_child:
                    flow_box.select_child(first_child)
                return True
        
        # Handle arrow key navigation
        elif keyval in (Gdk.KEY_Up, Gdk.KEY_Down, Gdk.KEY_Left, Gdk.KEY_Right, 
                        Gdk.KEY_KP_Up, Gdk.KEY_KP_Down, Gdk.KEY_KP_Left, Gdk.KEY_KP_Right):
            logger.debug(f"Arrow key pressed: {keyval}, handling navigation")
            result = self._handle_arrow_key(keyval)
            logger.debug(f"Arrow key handling result: {result}")
            # Reset number input when arrow keys are pressed
            self._reset_number_input()
            return result
        
        # Reset number input for any other key (except modifiers)
        else:
            # Don't reset on modifier keys
            from gi.repository import Gdk
            if keyval not in (Gdk.KEY_Shift_L, Gdk.KEY_Shift_R, Gdk.KEY_Control_L, Gdk.KEY_Control_R,
                             Gdk.KEY_Alt_L, Gdk.KEY_Alt_R, Gdk.KEY_Meta_L, Gdk.KEY_Meta_R):
                self._reset_number_input()
        
        return False  # Event not handled
    
    def _handle_arrow_key(self, keyval):
        """Handle arrow key navigation."""
        from gi.repository import Gdk
        
        flow_box = self._get_current_flow_box()
        
        # Ensure a card is selected before navigating
        selected = flow_box.get_selected_children()
        current_child = selected[0] if selected else None
        
        if not current_child:
            # No selection, select first child
            first_child = flow_box.get_first_child()
            if first_child:
                flow_box.select_child(first_child)
                self._scroll_to_child(first_child)
                logger.debug("Selected first card in arrow key handler")
            return True
        
        # Get current index
        current_index = current_child.get_index()
        max_children_per_line = flow_box.get_max_children_per_line()
        
        # Count total children by iterating
        total_children = 0
        child = flow_box.get_first_child()
        while child is not None:
            total_children += 1
            child = child.get_next_sibling()
        
        # Determine next index based on arrow key
        if keyval in (Gdk.KEY_Right, Gdk.KEY_KP_Right):
            # Move right (next card)
            next_index = current_index + 1
            if next_index < total_children:
                next_child = flow_box.get_child_at_index(next_index)
                if next_child:
                    flow_box.select_child(next_child)
                    self._scroll_to_child(next_child)
                    return True
        
        elif keyval in (Gdk.KEY_Left, Gdk.KEY_KP_Left):
            # Move left (previous card)
            next_index = current_index - 1
            if next_index >= 0:
                next_child = flow_box.get_child_at_index(next_index)
                if next_child:
                    flow_box.select_child(next_child)
                    self._scroll_to_child(next_child)
                    return True
        
        elif keyval in (Gdk.KEY_Down, Gdk.KEY_KP_Down):
            # Move down (next row)
            next_index = current_index + max_children_per_line
            if next_index < total_children:
                next_child = flow_box.get_child_at_index(next_index)
                if next_child:
                    flow_box.select_child(next_child)
                    self._scroll_to_child(next_child)
                    return True
        
        elif keyval in (Gdk.KEY_Up, Gdk.KEY_KP_Up):
            # Move up (previous row)
            next_index = current_index - max_children_per_line
            if next_index >= 0:
                next_child = flow_box.get_child_at_index(next_index)
                if next_child:
                    flow_box.select_child(next_child)
                    self._scroll_to_child(next_child)
                    return True
        
        return True  # Event handled (even if no movement)
    
    def _is_number_key(self, keyval):
        """Check if keyval is a number key (0-9)."""
        from gi.repository import Gdk
        number_keys = (
            Gdk.KEY_0, Gdk.KEY_1, Gdk.KEY_2, Gdk.KEY_3, Gdk.KEY_4,
            Gdk.KEY_5, Gdk.KEY_6, Gdk.KEY_7, Gdk.KEY_8, Gdk.KEY_9,
            Gdk.KEY_KP_0, Gdk.KEY_KP_1, Gdk.KEY_KP_2, Gdk.KEY_KP_3, Gdk.KEY_KP_4,
            Gdk.KEY_KP_5, Gdk.KEY_KP_6, Gdk.KEY_KP_7, Gdk.KEY_KP_8, Gdk.KEY_KP_9
        )
        return keyval in number_keys
    
    def _get_number_from_keyval(self, keyval):
        """Get the numeric value from a keyval."""
        from gi.repository import Gdk
        # Regular number keys
        if Gdk.KEY_0 <= keyval <= Gdk.KEY_9:
            return keyval - Gdk.KEY_0
        # Keypad number keys
        elif Gdk.KEY_KP_0 <= keyval <= Gdk.KEY_KP_9:
            return keyval - Gdk.KEY_KP_0
        return None
    
    def _reset_number_input(self):
        """Reset the number input buffer."""
        if self.number_input_timeout_id:
            GLib.source_remove(self.number_input_timeout_id)
            self.number_input_timeout_id = None
        self.number_input = ""
    
    def _handle_number_key(self, number):
        """Handle number key press for card selection."""
        flow_box = self._get_current_flow_box()
        
        # Cancel any existing timeout
        if self.number_input_timeout_id:
            GLib.source_remove(self.number_input_timeout_id)
            self.number_input_timeout_id = None
        
        # Append the number to the input string
        self.number_input += str(number)
        logger.debug(f"Number input updated to: '{self.number_input}'")
        
        # Try to find and select the card with this number
        try:
            card_number = int(self.number_input)
            logger.debug(f"Looking for card #{card_number}, available cards: {list(self.cards.keys())}")
            card = self.cards.get(card_number)
            if card:
                logger.debug(f"Found card #{card_number}: {card.command.title}")
                # Find the FlowBoxChild that contains this card
                for child in flow_box:
                    if child.get_child() == card:
                        # Make sure the card is visible
                        if child.get_visible() and card.get_visible():
                            logger.debug(f"Selecting card #{card_number} via number input")
                            flow_box.select_child(child)
                            self._scroll_to_child(child)
                            # Reset input after successful selection
                            self._reset_number_input()
                            return
                        else:
                            logger.debug(f"Card #{card_number} found but not visible")
            else:
                logger.debug(f"Card #{card_number} not found in cards dictionary")
        except ValueError as e:
            logger.debug(f"Error converting '{self.number_input}' to int: {e}")
        
        # Set a timeout to reset the number input if no valid card is found
        # This allows users to type multi-digit numbers
        def reset_input():
            logger.debug(f"Resetting number input after timeout")
            self._reset_number_input()
            return False
        
        self.number_input_timeout_id = GLib.timeout_add(1000, reset_input)  # Reset after 1 second
    
    def _scroll_to_child(self, child):
        """Scroll the scrolled window to make the child visible."""
        scrolled = self._get_current_scrolled()
        # Get the allocation of the child
        allocation = child.get_allocation()
        if allocation.height > 0:
            # Scroll to make the child visible
            scrolled.get_vadjustment().set_value(allocation.y)
    
    def cleanup(self):
        """Clean up resources."""
        logger.debug("Cleaning up main view")

