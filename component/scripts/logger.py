import logging
import sys


class CustomLogger:
    def __init__(
        self, name: str, log_file: str = "app.log", level: int = logging.DEBUG
    ):
        """
        Creates a custom logger with a file handler.
        """
        # Create a logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Create handlers (console and file)
        file_handler = logging.FileHandler(log_file)

        # Set log level for handlers
        file_handler.setLevel(level)

        # Create a log format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        # Add handlers to the logger
        self.logger.addHandler(file_handler)

    def message_to_string(self, *messages: str):
        # Transform all the messages into strings
        messages = [str(msg) for msg in messages]

        # Join all the strings in message
        return " ".join(messages)

    def debug(self, *messages: str):
        """Logs a debug message."""
        self.logger.debug(self.message_to_string(*messages))

    def info(self, *messages: str):
        """Logs an info message."""
        self.logger.info(self.message_to_string(*messages))

    def warning(self, *messages: str):
        """Logs a warning message."""
        self.logger.warning(self.message_to_string(*messages))

    def error(self, *messages: str):
        """Logs an error message."""
        self.logger.error(self.message_to_string(*messages))

    def critical(self, *messages: str):
        """Logs a critical message."""
        self.logger.critical(self.message_to_string(*messages))


logger = CustomLogger("se.plan")
