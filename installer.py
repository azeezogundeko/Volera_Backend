import importlib.util
import subprocess
import sys
from utils.logging import logger

def install_package(package_name: str, install_command: list = None):
    """
    Install a package using pip if it is not already installed.
    If an install_command is provided, run that command after the package installation.
    """
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing {package_name}: {e}")
        sys.exit(1)
    
    # If an additional install command is provided (e.g., for installing browser binaries), run it.
    if install_command:
        try:
            subprocess.check_call(install_command)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running post-install command for {package_name}: {e}")
            sys.exit(1)

def ensure_playwright_installed():
    if importlib.util.find_spec("playwright") is None:
        logger.info("Playwright not found. Installing Playwright...")
        # Install the playwright package
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        # Install Playwright browsers
        subprocess.check_call(["playwright", "install"])
    else:
        try:
            subprocess.check_call(["playwright", "install"])
        except Exception as e:
            logger.error("Failed to install Playwright browsers:", e)