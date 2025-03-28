from abc import ABC, abstractmethod

import logging

NOTSET = logging.NOTSET
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

class ILogger(ABC):
    """
    Abstract base class for logging in the system.

    The `ILogger` interface defines the structure for logging messages within the
    system. It provides methods for logging messages at different severity levels,
    including debug, info, warning, error, and critical.
    """

    @abstractmethod
    def debug(self, msg: str) -> None:
        """
        Log a debug message.

        Args:
            msg (str): The debug message to log.
        """
        pass

    @abstractmethod
    def info(self, msg: str) -> None:
        """
        Log an informational message.

        Args:
            msg (str): The informational message to log.
        """
        pass

    @abstractmethod
    def warning(self, msg: str) -> None:
        """
        Log a warning message.

        Args:
            msg (str): The warning message to log.
        """
        pass

    @abstractmethod
    def error(self, msg: str) -> None:
        """
        Log an error message.

        Args:
            msg (str): The error message to log.
        """
        pass

    @abstractmethod
    def critical(self, msg: str) -> None:
        """
        Log a critical message.

        Args:
            msg (str): The critical message to log.
        """
        pass

    @abstractmethod
    def setLevel(self, level: int) -> None:
        """
        Set the logging level.

        Args:
            level (str): The logging level to set (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR').
        """
        pass