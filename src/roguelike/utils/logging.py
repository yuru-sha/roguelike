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
        
        # File handler for game logs
        game_handler = logging.FileHandler(
            logs_dir / "game.log",
            mode="w",  # Overwrite mode
            encoding="utf-8"
        )
        game_handler.setLevel(logging.INFO)
        game_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        game_handler.setFormatter(game_formatter)
        self.logger.addHandler(game_handler)
        
        # File handler for error logs
        error_handler = logging.FileHandler(
            logs_dir / "error.log",
            mode="w",  # Overwrite mode
            encoding="utf-8"
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