"""
Game logging system.
Provides a singleton logger for the game with file and console output.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional


class GameLogger:
    """A singleton logger for the game."""

    _instance: Optional["GameLogger"] = None

    def __init__(self):
        """Initialize the logger."""
        if GameLogger._instance is not None:
            raise RuntimeError("GameLogger is a singleton. Use get_instance() instead.")

        # Create logs directory if it doesn't exist
        self.logs_dir = Path(__file__).parents[3] / "data" / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Configure logging
        self.logger = logging.getLogger("roguelike")
        self.logger.setLevel(logging.DEBUG)

        # Clear existing handlers
        self.logger.handlers.clear()

        # Rotate existing log files
        self._rotate_logs()

        # File handler for game logs
        game_handler = logging.FileHandler(
            self.logs_dir / "game.log", mode="w", encoding="utf-8"
        )
        game_handler.setLevel(logging.DEBUG)
        game_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        game_handler.setFormatter(game_formatter)
        self.logger.addHandler(game_handler)

        # File handler for error logs
        error_handler = logging.FileHandler(
            self.logs_dir / "error.log", mode="w", encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d\n%(message)s\n%(exc_info)s"
        )
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)

        # Console handler for warnings and above
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter(
            "%(levelname)s [%(filename)s:%(lineno)d]: %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # Log initialization
        self.logger.info("Logging system initialized")

    def _rotate_logs(self) -> None:
        """Rotate existing log files."""
        for log_type in ["game", "error"]:
            for i in range(4, 0, -1):  # Keep 5 backup files
                old_file = self.logs_dir / f"{log_type}.log.{i}"
                new_file = self.logs_dir / f"{log_type}.log.{i+1}"
                if old_file.exists():
                    old_file.rename(new_file)
            current_log = self.logs_dir / f"{log_type}.log"
            if current_log.exists():
                current_log.rename(self.logs_dir / f"{log_type}.log.1")

    @classmethod
    def get_instance(cls) -> logging.Logger:
        """Get the singleton instance of the logger.

        Returns:
            The logger instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance.logger

    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to the logger."""
        return getattr(self.logger, name)


def setup_logging() -> None:
    """Initialize the logging system."""
    GameLogger.get_instance() 