"""
About dialog.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from commando import __version__

class AboutDialog(Adw.AboutWindow):
    """About dialog."""
    
    def __init__(self, **kwargs):
        """Initialize about dialog."""
        super().__init__(**kwargs)
        
        self.set_application_name("Commando")
        self.set_version(__version__)
        self.set_application_icon("com.github.commando")
        self.set_developer_name("Commando Developers")
        self.set_license_type(Gtk.License.GPL_3_0)
        self.set_website("https://github.com/commando/commando")
        self.set_issue_url("https://github.com/commando/commando/issues")
        
        self.set_copyright("© 2024 Commando Developers")
        self.set_developers(["Commando Team"])
        
        self.set_comments(
            "A GNOME application for saving and running user-defined Linux commands."
        )

