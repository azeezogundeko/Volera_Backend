import importlib.util
import subprocess
import sys
import logging

logger = logging.getLogger(__name__)

def ensure_playwright_installed():
    # Check if the playwright package is installed
    if importlib.util.find_spec("playwright") is None:
        logger.info("Playwright not found. Installing Playwright package...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        except subprocess.CalledProcessError as e:
            logger.error("Failed to install Playwright package: %s", e)
            sys.exit(1)
    
    # Install the Playwright browsers
    try:
        logger.info("Installing Playwright browsers...")
        subprocess.check_call(["playwright", "install"])
    except subprocess.CalledProcessError as e:
        logger.error("Failed to install Playwright browsers: %s", e)
        sys.exit(1)

# if __name__ == "__main__":
#     ensure_playwright_installed()
    # Continue with starting your FastAPI app...
