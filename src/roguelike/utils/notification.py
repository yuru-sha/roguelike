"""
Error notification system implementation
"""

import json
import queue
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from roguelike.utils.game_logger import GameLogger

logger = GameLogger.get_instance()


@dataclass
class Notification:
    """Data class representing a notification message"""

    message: str
    level: str  # 'error', 'warning', 'info'
    timestamp: datetime
    source: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to JSON format"""
        return {
            "message": self.message,
            "level": self.level,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Notification":
        """Restore notification from JSON format"""
        return cls(
            message=data["message"],
            level=data["level"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data["source"],
            details=data.get("details"),
        )


class NotificationManager:
    """Class for managing and handling notifications"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self) -> None:
        """Initialize the instance"""
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
        Add a new notification.
        The notification is added to a queue and processed in a separate thread.

        Args:
            notification: The notification to add
        """
        self.notification_queue.put(notification)

    def _process_notifications(self) -> None:
        """Background thread for processing the notification queue"""
        while True:
            try:
                notification = self.notification_queue.get()

                # Add notification to list
                self.notifications.append(notification)
                if len(self.notifications) > self.max_notifications:
                    self.notifications.pop(0)

                # Save notification to file
                self._save_notification(notification)

                # Call handlers
                self._call_handlers(notification)

                # Mark queue task as done
                self.notification_queue.task_done()

            except Exception as e:
                logger.error(f"Error processing notification: {e}")

    def _save_notification(self, notification: Notification) -> None:
        """Save notification to file"""
        try:
            save_dir = Path.home() / ".roguelike" / "notifications"
            save_dir.mkdir(parents=True, exist_ok=True)

            # Separate files by date
            date_str = notification.timestamp.strftime("%Y-%m-%d")
            file_path = save_dir / f"notifications_{date_str}.json"

            # Load existing notifications
            notifications = []
            if file_path.exists():
                with file_path.open("r", encoding="utf-8") as f:
                    notifications = json.load(f)

            # Add new notification
            notifications.append(notification.to_dict())

            # Save to file
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(notifications, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Failed to save notification: {e}")

    def add_handler(self, level: str, handler: Callable[[Notification], None]) -> None:
        """
        Add a notification handler.

        Args:
            level: Notification level ('error', 'warning', 'info')
            handler: Callback function to handle the notification
        """
        if level in self.handlers:
            self.handlers[level].append(handler)

    def _call_handlers(self, notification: Notification) -> None:
        """Call handlers for the notification"""
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
        Get notifications matching the conditions.

        Args:
            level: Filter by notification level
            start_time: Start time
            end_time: End time

        Returns:
            List of notifications matching the conditions
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
        """Clear all notifications"""
        self.notifications.clear()

    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
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
