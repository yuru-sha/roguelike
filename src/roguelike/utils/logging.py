import logging
import sys
from pathlib import Path
from typing import Optional

class GameLogger:
    _instance: Optional["GameLogger"] = None
    
    def __init__(self) -> None:
        if GameLogger._instance is not None:
            raise RuntimeError("GameLogger is a singleton!")
        
        self.logger = logging.getLogger("roguelike")
        self.logger.setLevel(logging.DEBUG)
        
        # ログファイルの設定
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # ファイルハンドラの設定
        file_handler = logging.FileHandler(
            log_dir / "game.log",
            encoding="utf-8",
            mode="w"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        
        # コンソールハンドラの設定（エラーのみ）
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.ERROR)
        console_formatter = logging.Formatter(
            "%(levelname)s: %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    @classmethod
    def get_instance(cls) -> "GameLogger":
        if cls._instance is None:
            cls._instance = GameLogger()
        return cls._instance
    
    def debug(self, message: str) -> None:
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        self.logger.critical(message)
    
    def exception(self, message: str) -> None:
        self.logger.exception(message) 