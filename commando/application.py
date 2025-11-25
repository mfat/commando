"""
Main application class.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib

from commando.logger import get_logger
from commando.window import CommandoWindow
from commando.config import Config

logger = get_logger(__name__)


class CommandoApplication(Adw.Application):
    """Main application class."""
    
    def __init__(self):
        """Initialize the application."""
        super().__init__(
            application_id="com.github.commando",
            flags=0
        )
        self.config = Config()
        self.window = None
        
        # Connect signals
        self.connect("activate", self.on_activate)
        self.connect("shutdown", self.on_shutdown)
        
        logger.info("CommandoApplication initialized")
    
    def on_activate(self, app):
        """Handle application activation."""
        logger.debug("Application activated")
        
        try:
            if self.window is None:
                logger.debug("Creating CommandoWindow")
                self.window = CommandoWindow(application=app)
                logger.debug("CommandoWindow created successfully")
            
            logger.debug("Presenting window")
            self.window.present()
            logger.debug("Window presented")
        except Exception as e:
            logger.error(f"Error during window activation: {e}", exc_info=True)
            raise
    
    def on_shutdown(self, app):
        """Handle application shutdown."""
        logger.info("Application shutting down")
        if self.window:
            self.window.cleanup()

