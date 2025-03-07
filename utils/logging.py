import logging
import colorlog
import os
from logging.handlers import RotatingFileHandler
import stat

# Ensure logs directory exists with proper permissions
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Set proper permissions for the logs directory
try:
    os.chmod(LOG_DIR, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
except Exception as e:
    print(f"Warning: Could not set log directory permissions: {e}")

# Set up the logger
logger = logging.getLogger("custom_logger")
logger.setLevel(logging.DEBUG)  # Set the default log level to DEBUG

# Define a colored formatter for console
console_formatter = colorlog.ColoredFormatter(
    "%(asctime)s - %(log_color)s%(levelname)s%(reset)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
)

# Define a standard formatter for file logging
file_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(console_formatter)

def create_file_handler(filename, level=logging.INFO, max_bytes=10*1024*1024, backup_count=5):
    """Create a file handler with proper permissions"""
    log_file_path = os.path.join(LOG_DIR, filename)
    
    # Create the file if it doesn't exist and set permissions
    if not os.path.exists(log_file_path):
        with open(log_file_path, 'a'):
            pass
        try:
            os.chmod(log_file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)  # 0666
        except Exception as e:
            print(f"Warning: Could not set log file permissions for {filename}: {e}")
    
    handler = RotatingFileHandler(
        log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    handler.setLevel(level)
    handler.setFormatter(file_formatter)
    return handler

# Create handlers using the new function
file_handler = create_file_handler('application.log', logging.INFO)
error_file_handler = create_file_handler('error.log', logging.ERROR, backup_count=3)

# Add handlers to the logger
# logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.addHandler(error_file_handler)

# Prevent log messages from propagating to parent loggers
logger.propagate = False