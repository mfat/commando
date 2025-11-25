"""
Web view using WebKit.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")

from gi.repository import Gtk, Adw, WebKit

from commando.logger import get_logger

logger = get_logger(__name__)


class WebView(Adw.Bin):
    """Web view for displaying web pages."""
    
    def __init__(self):
        """Initialize the web view."""
        super().__init__()
        
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Toolbar (creates webkit_view)
        toolbar = self._create_toolbar()
        main_box.append(toolbar)
        
        # Scrolled window - make it expand
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_child(self.webkit_view)
        main_box.append(scrolled)
        
        self.set_child(main_box)
    
    def _create_toolbar(self):
        """Create toolbar for web view."""
        # Create web view first (needed for toolbar)
        self.webkit_view = WebKit.WebView()
        self.webkit_view.load_uri("about:blank")
        
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        toolbar.set_margin_start(12)
        toolbar.set_margin_end(12)
        toolbar.set_margin_top(12)
        toolbar.set_margin_bottom(12)
        
        # Back button
        back_btn = Gtk.Button(icon_name="go-previous-symbolic")
        back_btn.set_tooltip_text("Back")
        back_btn.connect("clicked", lambda _: self.webkit_view.go_back())
        toolbar.append(back_btn)
        
        # Forward button
        forward_btn = Gtk.Button(icon_name="go-next-symbolic")
        forward_btn.set_tooltip_text("Forward")
        forward_btn.connect("clicked", lambda _: self.webkit_view.go_forward())
        toolbar.append(forward_btn)
        
        # Reload button
        reload_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        reload_btn.set_tooltip_text("Reload")
        reload_btn.connect("clicked", lambda _: self.webkit_view.reload())
        toolbar.append(reload_btn)
        
        toolbar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        
        # URL entry
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("Enter URL or search...")
        self.url_entry.set_hexpand(True)
        self.url_entry.connect("activate", self._on_url_activate)
        toolbar.append(self.url_entry)
        
        # Go button
        go_btn = Gtk.Button(label="Go")
        go_btn.connect("clicked", self._on_go_clicked)
        toolbar.append(go_btn)
        
        # Connect to web view signals
        self.webkit_view.connect("notify::uri", self._on_uri_changed)
        
        return toolbar
    
    def _on_url_activate(self, entry):
        """Handle URL entry activation."""
        self._load_url(entry.get_text())
    
    def _on_go_clicked(self, button):
        """Handle Go button click."""
        self._load_url(self.url_entry.get_text())
    
    def _load_url(self, url: str):
        """Load a URL."""
        url = url.strip()
        if not url:
            return
        
        # Add protocol if missing
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        self.webkit_view.load_uri(url)
        logger.info(f"Loading URL: {url}")
    
    def _on_uri_changed(self, web_view, param):
        """Handle URI change."""
        uri = web_view.get_uri()
        if uri:
            self.url_entry.set_text(uri)
    
    def load_uri(self, uri: str):
        """Load a URI."""
        self.webkit_view.load_uri(uri)
    
    def cleanup(self):
        """Clean up resources."""
        logger.debug("Cleaning up web view")

