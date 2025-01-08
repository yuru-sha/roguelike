import logging
import sys
from pathlib import Path
from typing import Optional, Any

class GameLogger:
    """A singleton logger for the game."""
    
    _instance: Optional['GameLogger'] = None
    
    def __init__(self):
        """Initialize the logger."""
        if GameLogger._instance is not None:
            raise RuntimeError("GameLogger is a singleton. Use get_instance() instead.")
        
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Configure logging
        self.logger = logging.getLogger("roguelike")
        self.logger.setLevel(logging.DEBUG)
        
        # File handler for all logs
        file_handler = logging.FileHandler(
            logs_dir / "game.log",
            mode="w",
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler for errors and above
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.ERROR)
        console_formatter = logging.Formatter(
            "%(levelname)s: %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    @classmethod
    def get_instance(cls) -> logging.Logger:
        """
        Get the singleton instance of the logger.
        
        Returns:
            The logger instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance.logger
    
    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to the logger."""
        return getattr(self.logger, name) 