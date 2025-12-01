"""
Default commands that are created on first run.
"""

from commando.models.command import Command
from typing import List, Set


def get_default_commands() -> List[Command]:
    """Get the list of default commands to create on first run."""
    return [
        # System Information
        Command(
            number=1,
            title="Disk Usage",
            command="df -h",
            icon="drive-harddisk-symbolic",
            color="blue",
            category="System",
            description="Show disk space usage for all mounted filesystems"
        ),
        Command(
            number=2,
            title="Memory Usage",
            command="free -h",
            icon="memory-symbolic",
            color="blue",
            category="System",
            description="Display memory usage information"
        ),
        Command(
            number=3,
            title="System Uptime",
            command="uptime",
            icon="preferences-system-time-symbolic",
            color="blue",
            category="System",
            description="Show how long the system has been running"
        ),
        Command(
            number=4,
            title="Process List",
            command="ps aux --sort=-%mem | head -20",
            icon="utilities-system-monitor-symbolic",
            color="blue",
            category="System",
            description="Show top processes by memory usage"
        ),
        
        # Package Management
        Command(
            number=5,
            title="Update Packages (Fedora)",
            command="sudo dnf update",
            icon="software-update-available-symbolic",
            color="green",
            category="Packages",
            description="Update all installed packages (Fedora/RHEL)"
        ),
        Command(
            number=6,
            title="Update Packages (Debian/Ubuntu)",
            command="sudo apt update && sudo apt upgrade",
            icon="software-update-available-symbolic",
            color="green",
            category="Packages",
            description="Update all installed packages (Debian/Ubuntu)"
        ),
        Command(
            number=7,
            title="Update Packages (Arch)",
            command="sudo pacman -Syu",
            icon="software-update-available-symbolic",
            color="green",
            category="Packages",
            description="Update all installed packages (Arch Linux)"
        ),
        Command(
            number=8,
            title="Search Package (Fedora)",
            command="dnf search ",
            icon="system-search-symbolic",
            color="green",
            category="Packages",
            description="Search for packages (add search term after command)"
        ),
        
        # File Operations
        Command(
            number=9,
            title="Find Files",
            command="find . -name ",
            icon="system-file-manager-symbolic",
            color="yellow",
            category="Files",
            description="Find files by name (add pattern after command)"
        ),
        Command(
            number=10,
            title="Search in Files",
            command="grep -r ",
            icon="edit-find-symbolic",
            color="yellow",
            category="Files",
            description="Search for text in files (add search term after command)"
        ),
        Command(
            number=11,
            title="List Large Files",
            command=r"find . -type f -size +100M -exec ls -lh {} \;",
            icon="document-open-symbolic",
            color="yellow",
            category="Files",
            description="Find files larger than 100MB"
        ),
        Command(
            number=12,
            title="Disk Usage by Directory",
            command="du -h --max-depth=1 | sort -hr | head -10",
            icon="folder-symbolic",
            color="yellow",
            category="Files",
            description="Show disk usage by directory"
        ),
        
        # Network
        Command(
            number=13,
            title="Check IP Address",
            command="ip addr show",
            icon="network-wired-symbolic",
            color="purple",
            category="Network",
            description="Display network interface information"
        ),
        Command(
            number=14,
            title="Ping Host",
            command="ping -c 4 ",
            icon="network-workgroup-symbolic",
            color="purple",
            category="Network",
            description="Ping a host (add hostname after command)"
        ),
        Command(
            number=15,
            title="Open Ports",
            command="sudo ss -tulpn",
            icon="network-server-symbolic",
            color="purple",
            category="Network",
            description="Show listening ports and services"
        ),
        Command(
            number=16,
            title="Network Speed Test",
            command="curl -o /dev/null -s -w '%{speed_download}\n' http://speedtest.tele2.net/10MB.zip",
            icon="network-workgroup-symbolic",
            color="purple",
            category="Network",
            description="Simple network speed test"
        ),
        
        # System Services
        Command(
            number=17,
            title="System Status",
            command="systemctl status ",
            icon="preferences-system-symbolic",
            color="orange",
            category="Services",
            description="Check service status (add service name after command)"
        ),
        Command(
            number=18,
            title="System Logs",
            command="journalctl -xe",
            icon="text-editor-symbolic",
            color="orange",
            category="Services",
            description="View recent system logs"
        ),
        Command(
            number=19,
            title="Service Logs",
            command="journalctl -u ",
            icon="text-editor-symbolic",
            color="orange",
            category="Services",
            description="View logs for a service (add service name after command)"
        ),
        Command(
            number=20,
            title="List Failed Services",
            command="systemctl --failed",
            icon="dialog-error-symbolic",
            color="red",
            category="Services",
            description="Show failed systemd services"
        ),
        
        # Git Operations
        Command(
            number=21,
            title="Git Status",
            command="git status",
            icon="folder-git-symbolic",
            color="pink",
            category="Git",
            description="Show the working tree status"
        ),
        Command(
            number=22,
            title="Git Log",
            command="git log --oneline --graph --decorate -20",
            icon="document-new-symbolic",
            color="pink",
            category="Git",
            description="Show recent git commits"
        ),
        Command(
            number=23,
            title="Git Branch List",
            command="git branch -a",
            icon="folder-git-symbolic",
            color="pink",
            category="Git",
            description="List all local and remote branches"
        ),
        Command(
            number=24,
            title="Git Diff",
            command="git diff",
            icon="text-editor-symbolic",
            color="pink",
            category="Git",
            description="Show changes in working directory"
        ),
        
        # Development Tools
        Command(
            number=25,
            title="Python Version",
            command="python --version",
            icon="applications-development-symbolic",
            color="brown",
            category="Development",
            description="Check Python version"
        ),
        Command(
            number=26,
            title="List Python Packages",
            command="pip list",
            icon="applications-development-symbolic",
            color="brown",
            category="Development",
            description="List installed Python packages"
        ),
        Command(
            number=27,
            title="Node Version",
            command="node --version && npm --version",
            icon="applications-development-symbolic",
            color="brown",
            category="Development",
            description="Check Node.js and npm versions"
        ),
        Command(
            number=28,
            title="Environment Variables",
            command="env | sort",
            icon="preferences-system-symbolic",
            color="gray",
            category="System",
            description="List all environment variables"
        ),
        
        # Useful Utilities
        Command(
            number=29,
            title="Clear Terminal",
            command="clear",
            icon="edit-clear-symbolic",
            color="gray",
            category="Utilities",
            description="Clear the terminal screen",
            no_terminal=False
        ),
        Command(
            number=30,
            title="Current Directory",
            command="pwd",
            icon="folder-symbolic",
            color="gray",
            category="Utilities",
            description="Print current working directory"
        ),
        Command(
            number=31,
            title="List Directory Contents",
            command="ls -lah",
            icon="folder-open-symbolic",
            color="gray",
            category="Utilities",
            description="List files with details"
        ),
        Command(
            number=32,
            title="History",
            command="history | tail -20",
            icon="document-open-recent-symbolic",
            color="gray",
            category="Utilities",
            description="Show recent command history"
        ),
    ]


def get_default_command_numbers() -> Set[int]:
    """Get the set of default command numbers."""
    return {cmd.number for cmd in get_default_commands()}


def is_default_command(command: Command) -> bool:
    """
    Check if a command is a default command by comparing with default commands.
    
    Args:
        command: Command to check
        
    Returns:
        True if the command matches a default command (by number and content)
    """
    default_commands = get_default_commands()
    for default_cmd in default_commands:
        if default_cmd.number == command.number:
            # Check if the command content matches the default
            # Compare key properties: title, command, icon, color, category
            return (
                default_cmd.title == command.title and
                default_cmd.command == command.command and
                default_cmd.icon == command.icon and
                default_cmd.color == command.color and
                default_cmd.category == command.category
            )
    return False

