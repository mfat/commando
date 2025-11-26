"""
About dialog.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from commando import __version__


def create_about_dialog(**kwargs) -> Adw.AboutDialog:
    """
    Build and configure the about dialog without subclassing final Adw
    widgets. Adw.AboutDialog replaces the deprecated Adw.AboutWindow in
    libadwaita ≥ 1.5.
    """
    dialog = Adw.AboutDialog(**kwargs)

    dialog.set_application_name("Commando")
    dialog.set_version(__version__)
    dialog.set_application_icon("com.github.commando")
    dialog.set_developer_name("Commando Developers")
    dialog.set_license_type(Gtk.License.GPL_3_0)
    dialog.set_website("https://github.com/commando/commando")
    dialog.set_issue_url("https://github.com/commando/commando/issues")

    dialog.set_copyright("© 2024 Commando Developers")
    dialog.set_developers(["Commando Team"])

    dialog.set_comments(
        "A GNOME application for saving and running user-defined Linux commands."
    )

    return dialog

