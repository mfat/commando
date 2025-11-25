#!/usr/bin/env python3
"""
Main entry point for Commando application.
"""

import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Vte", "3.91")
gi.require_version("WebKit", "6.0")

from gi.repository import Gtk, Adw, GLib

from commando.application import CommandoApplication
from commando.logger import setup_logging, get_logger

logger = get_logger(__name__)


def main():
    """Main entry point."""
    setup_logging()
    logger.info("Starting Commando application")
    
    app = CommandoApplication()
    exit_status = app.run(sys.argv)
    
    logger.info(f"Commando application exited with status {exit_status}")
    return exit_status


if __name__ == "__main__":
    sys.exit(main())

