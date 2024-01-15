import logging
import os
import sys

default_log_level = logging.ERROR


def setup_logger(name: str, log_file: str, level: int = default_log_level):
    """Function to set up a logger.

    Args:
    - name: Name of the logger.
    - log_file: File path to write the log to.
    - level: Logging level, e.g., logging.DEBUG, logging.INFO, etc.

    Returns:
    - A configured logger.
    """

    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create a file handler that logs messages to a file
    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Create a stream handler that logs messages to stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    # Add both handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


app_logger = setup_logger("default_logger", "app.log", default_log_level)
