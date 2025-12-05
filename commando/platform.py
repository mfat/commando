"""
Platform detection for OS and distribution.
"""

import platform
import os
from pathlib import Path
from typing import Optional, Tuple
from enum import Enum

from commando.logger import get_logger

logger = get_logger(__name__)


class Distribution(Enum):
    """Linux distribution types."""
    FEDORA = "fedora"
    RHEL = "rhel"
    CENTOS = "centos"
    DEBIAN = "debian"
    UBUNTU = "ubuntu"
    ARCH = "arch"
    OPENSUSE = "opensuse"
    SUSE = "suse"
    UNKNOWN = "unknown"


def detect_distribution() -> Distribution:
    """
    Detect the Linux distribution.
    
    Returns:
        Distribution enum value
    """
    try:
        # Try /etc/os-release first (most reliable)
        os_release = Path("/etc/os-release")
        if os_release.exists():
            with open(os_release, "r") as f:
                content = f.read()
            
            # Parse ID and ID_LIKE
            id_val = None
            id_like = None
            
            for line in content.splitlines():
                if line.startswith("ID="):
                    id_val = line.split("=", 1)[1].strip().strip('"').lower()
                elif line.startswith("ID_LIKE="):
                    id_like = line.split("=", 1)[1].strip().strip('"').lower()
            
            # Check distribution
            if id_val:
                if id_val in ["fedora", "rhel", "centos"]:
                    if id_val == "fedora":
                        return Distribution.FEDORA
                    elif id_val == "rhel":
                        return Distribution.RHEL
                    elif id_val == "centos":
                        return Distribution.CENTOS
                elif id_val in ["debian", "ubuntu"]:
                    if id_val == "ubuntu":
                        return Distribution.UBUNTU
                    return Distribution.DEBIAN
                elif id_val in ["arch", "archlinux"]:
                    return Distribution.ARCH
                elif id_val in ["opensuse", "opensuse-leap", "opensuse-tumbleweed"]:
                    return Distribution.OPENSUSE
                elif id_val == "sles":
                    return Distribution.SUSE
            
            # Check ID_LIKE for distributions derived from others
            if id_like:
                if "fedora" in id_like or "rhel" in id_like:
                    return Distribution.FEDORA
                elif "debian" in id_like:
                    if id_val == "ubuntu":
                        return Distribution.UBUNTU
                    return Distribution.DEBIAN
                elif "arch" in id_like:
                    return Distribution.ARCH
                elif "suse" in id_like:
                    return Distribution.OPENSUSE
        
        # Fallback: Check for distribution-specific files
        if Path("/etc/fedora-release").exists():
            return Distribution.FEDORA
        elif Path("/etc/redhat-release").exists():
            return Distribution.RHEL
        elif Path("/etc/debian_version").exists():
            return Distribution.DEBIAN
        elif Path("/etc/arch-release").exists():
            return Distribution.ARCH
        elif Path("/etc/SuSE-release").exists():
            return Distribution.OPENSUSE
        
    except Exception as e:
        logger.warning(f"Failed to detect distribution: {e}")
    
    return Distribution.UNKNOWN


def detect_os() -> str:
    """
    Detect the operating system.
    
    Returns:
        OS name (e.g., 'Linux', 'Windows', 'Darwin')
    """
    return platform.system()


def get_package_manager(distribution: Optional[Distribution] = None) -> Optional[str]:
    """
    Get the package manager command for a distribution.
    
    Args:
        distribution: Distribution to check. If None, auto-detects.
        
    Returns:
        Package manager name (e.g., 'dnf', 'apt', 'pacman', 'zypper') or None
    """
    if distribution is None:
        distribution = detect_distribution()
    
    if distribution in [Distribution.FEDORA, Distribution.RHEL, Distribution.CENTOS]:
        # Check if dnf exists (preferred), fall back to yum
        import shutil
        if shutil.which("dnf"):
            return "dnf"
        elif shutil.which("yum"):
            return "yum"
    elif distribution in [Distribution.DEBIAN, Distribution.UBUNTU]:
        return "apt"
    elif distribution == Distribution.ARCH:
        return "pacman"
    elif distribution in [Distribution.OPENSUSE, Distribution.SUSE]:
        return "zypper"
    
    return None


def get_platform_info() -> Tuple[str, Distribution, Optional[str]]:
    """
    Get complete platform information.
    
    Returns:
        Tuple of (OS name, Distribution, package_manager)
    """
    os_name = detect_os()
    distribution = detect_distribution()
    package_manager = get_package_manager(distribution)
    
    return (os_name, distribution, package_manager)







