"""
エラー通知システムの実装
"""

import json
import queue
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from roguelike.utils.logging import GameLogger

logger = GameLogger.get_instance()


@dataclass
class Notification:
    """通知メッセージを表すデータクラス"""

    message: str
    level: str  # 'error', 'warning', 'info'
    timestamp: datetime
    source: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """通知をJSON形式に変換する"""
        return {
            "message": self.message,
            "level": self.level,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Notification":
        """JSON形式から通知を復元する"""
        return cls(
            message=data["message"],
            level=data["level"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data["source"],
            details=data.get("details"),
        )


class NotificationManager:
    """通知の管理とハンドリングを行うクラス"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self) -> None:
        """インスタンスの初期化"""
        self.notifications: List[Notification] = []
        self.max_notifications = 100
        self.handlers: Dict[str, List[Callable[[Notification], None]]] = {
            "error": [],
            "warning": [],
            "info": [],
        }
        self.notification_queue = queue.Queue()
        self.notification_thread = threading.Thread(
            target=self._process_notifications, daemon=True
        )
        self.notification_thread.start()

    def add_notification(self, notification: Notification) -> None:
        """
        新しい通知を追加する。
        通知はキューに追加され、別スレッドで処理される。

        Args:
            notification: 追加する通知
        """
        self.notification_queue.put(notification)

    def _process_notifications(self) -> None:
        """通知キューを処理するバックグラウンドスレッド"""
        while True:
            try:
                notification = self.notification_queue.get()

                # 通知をリストに追加
                self.notifications.append(notification)
                if len(self.notifications) > self.max_notifications:
                    self.notifications.pop(0)

                # 通知をファイルに保存
                self._save_notification(notification)

                # ハンドラーを呼び出す
                self._call_handlers(notification)

                # キューの処理完了を通知
                self.notification_queue.task_done()

            except Exception as e:
                logger.error(f"Error processing notification: {e}")

    def _save_notification(self, notification: Notification) -> None:
        """通知をファイルに保存する"""
        try:
            save_dir = Path.home() / ".roguelike" / "notifications"
            save_dir.mkdir(parents=True, exist_ok=True)

            # 日付ごとにファイルを分ける
            date_str = notification.timestamp.strftime("%Y-%m-%d")
            file_path = save_dir / f"notifications_{date_str}.json"

            # 既存の通知を読み込む
            notifications = []
            if file_path.exists():
                with file_path.open("r", encoding="utf-8") as f:
                    notifications = json.load(f)

            # 新しい通知を追加
            notifications.append(notification.to_dict())

            # ファイルに保存
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(notifications, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Failed to save notification: {e}")

    def add_handler(self, level: str, handler: Callable[[Notification], None]) -> None:
        """
        通知ハンドラーを追加する。

        Args:
            level: 通知レベル ('error', 'warning', 'info')
            handler: 通知を処理するコールバック関数
        """
        if level in self.handlers:
            self.handlers[level].append(handler)

    def _call_handlers(self, notification: Notification) -> None:
        """通知に対応するハンドラーを呼び出す"""
        for handler in self.handlers.get(notification.level, []):
            try:
                handler(notification)
            except Exception as e:
                logger.error(f"Error in notification handler: {e}")

    def get_notifications(
        self,
        level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Notification]:
        """
        条件に一致する通知を取得する。

        Args:
            level: フィルタする通知レベル
            start_time: 開始時刻
            end_time: 終了時刻

        Returns:
            条件に一致する通知のリスト
        """
        filtered = self.notifications

        if level:
            filtered = [n for n in filtered if n.level == level]

        if start_time:
            filtered = [n for n in filtered if n.timestamp >= start_time]

        if end_time:
            filtered = [n for n in filtered if n.timestamp <= end_time]

        return filtered

    def clear_notifications(self) -> None:
        """全ての通知をクリアする"""
        self.notifications.clear()

    def get_notification_stats(self) -> Dict[str, Any]:
        """通知の統計情報を取得する"""
        stats = {
            "total": len(self.notifications),
            "by_level": {"error": 0, "warning": 0, "info": 0},
            "by_source": {},
        }

        for notification in self.notifications:
            stats["by_level"][notification.level] += 1

            if notification.source not in stats["by_source"]:
                stats["by_source"][notification.source] = 0
            stats["by_source"][notification.source] += 1

        return stats
