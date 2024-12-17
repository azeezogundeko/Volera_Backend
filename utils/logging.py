import logging
import colorlog


# Set up the logger
logger = logging.getLogger("custom_logger")
logger.setLevel(logging.DEBUG)  # Set the default log level to DEBUG

# Define a colored formatter
formatter = colorlog.ColoredFormatter(
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

# Create handlers for console output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(console_handler)
