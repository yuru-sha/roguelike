import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger() -> logging.Logger:
    """ロガーの設定を行う"""
    # ログディレクトリの作成
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 現在の日時を取得してログファイル名を生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"roguelike_{timestamp}.log"
    
    # ロガーの作成
    logger = logging.getLogger("roguelike")
    logger.setLevel(logging.DEBUG)
    
    # ファイルハンドラの設定
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=4,  # 最新5件（現在のファイル + バックアップ4件）
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    
    # コンソールハンドラの設定
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # フォーマッタの設定
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # ハンドラの追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 古いログファイルの削除
    cleanup_old_logs(log_dir, keep=5)
    
    return logger

def cleanup_old_logs(log_dir: Path, keep: int = 5) -> None:
    """古いログファイルを削除する"""
    log_files = sorted(
        [f for f in log_dir.glob("roguelike_*.log")],
        key=os.path.getctime,
        reverse=True
    )
    
    # 指定数以上のログファイルを削除
    for log_file in log_files[keep:]:
        try:
            log_file.unlink()
        except OSError:
            pass

# グローバルなロガーインスタンス
logger = setup_logger() 