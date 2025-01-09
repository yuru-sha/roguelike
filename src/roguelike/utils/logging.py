import logging
import sys
from pathlib import Path
from typing import Optional, Any
from logging.handlers import RotatingFileHandler

class GameLogger:
    """A singleton logger for the game."""
    
    _instance: Optional['GameLogger'] = None
    
    def __init__(self):
        """Initialize the logger."""
        if GameLogger._instance is not None:
            raise RuntimeError("GameLogger is a singleton. Use get_instance() instead.")
        
        # Create logs directory if it doesn't exist
        logs_dir = Path(__file__).parents[3] / "logs"  # プロジェクトルートの logs/ ディレクトリ
        logs_dir.mkdir(exist_ok=True)
        
        # Configure logging
        self.logger = logging.getLogger("roguelike")
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Rotate existing log files
        self._rotate_logs(logs_dir)
        
        # File handler for game logs
        game_handler = logging.FileHandler(
            logs_dir / "game.log",
            mode="w",  # 新規作成モード
            encoding="utf-8"
        )
        game_handler.setLevel(logging.DEBUG)
        game_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        game_handler.setFormatter(game_formatter)
        self.logger.addHandler(game_handler)
        
        # File handler for error logs
        error_handler = logging.FileHandler(
            logs_dir / "error.log",
            mode="w",  # 新規作成モード
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
        
        # 起動時のメッセージを記録
        self.logger.info("Logging system initialized")
    
    def _rotate_logs(self, logs_dir: Path) -> None:
        """
        Rotate existing log files.
        
        Args:
            logs_dir: Directory containing log files
        """
        # Rotate game logs
        for i in range(4, 0, -1):  # Keep 5 backup files
            old_file = logs_dir / f"game.log.{i}"
            new_file = logs_dir / f"game.log.{i+1}"
            if old_file.exists():
                old_file.rename(new_file)
        game_log = logs_dir / "game.log"
        if game_log.exists():
            game_log.rename(logs_dir / "game.log.1")
        
        # Rotate error logs
        for i in range(4, 0, -1):  # Keep 5 backup files
            old_file = logs_dir / f"error.log.{i}"
            new_file = logs_dir / f"error.log.{i+1}"
            if old_file.exists():
                old_file.rename(new_file)
        error_log = logs_dir / "error.log"
        if error_log.exists():
            error_log.rename(logs_dir / "error.log.1")
    
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