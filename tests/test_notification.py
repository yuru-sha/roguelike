"""
通知システムのテストケース
"""

import json
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import pytest

from roguelike.utils.notification import Notification, NotificationManager


@pytest.fixture
def notification_manager():
    """テスト用の通知マネージャーを作成する"""
    manager = NotificationManager()
    manager.clear_notifications()
    return manager


def test_notification_creation():
    """通知の作成テスト"""
    notification = Notification(
        message="Test notification",
        level="info",
        timestamp=datetime.now(),
        source="test",
        details={"key": "value"},
    )

    assert notification.message == "Test notification"
    assert notification.level == "info"
    assert notification.source == "test"
    assert notification.details == {"key": "value"}


def test_notification_serialization():
    """通知のシリアライズ/デシリアライズテスト"""
    original = Notification(
        message="Test notification",
        level="info",
        timestamp=datetime.now(),
        source="test",
        details={"key": "value"},
    )

    # シリアライズ
    data = original.to_dict()
    assert isinstance(data, dict)
    assert data["message"] == original.message
    assert data["level"] == original.level

    # デシリアライズ
    restored = Notification.from_dict(data)
    assert restored.message == original.message
    assert restored.level == original.level
    assert restored.source == original.source
    assert restored.details == original.details


def test_notification_manager_singleton(notification_manager):
    """NotificationManagerのシングルトンパターンテスト"""
    manager1 = NotificationManager()
    manager2 = NotificationManager()
    assert manager1 is manager2


def test_add_notification(notification_manager):
    """通知の追加テスト"""
    notification = Notification(
        message="Test notification",
        level="info",
        timestamp=datetime.now(),
        source="test",
    )

    notification_manager.add_notification(notification)
    time.sleep(0.1)  # 非同期処理の完了を待つ

    notifications = notification_manager.get_notifications()
    assert len(notifications) == 1
    assert notifications[0].message == notification.message


def test_notification_limit(notification_manager):
    """通知の最大数制限テスト"""
    # 最大数+1の通知を追加
    for i in range(notification_manager.max_notifications + 1):
        notification = Notification(
            message=f"Test notification {i}",
            level="info",
            timestamp=datetime.now(),
            source="test",
        )
        notification_manager.add_notification(notification)

    time.sleep(0.1)  # 非同期処理の完了を待つ

    notifications = notification_manager.get_notifications()
    assert len(notifications) == notification_manager.max_notifications
    # 最古の通知が削除されていることを確認
    assert notifications[0].message != "Test notification 0"


def test_notification_handlers(notification_manager):
    """通知ハンドラーのテスト"""
    received_notifications: List[Notification] = []

    def test_handler(notification: Notification):
        received_notifications.append(notification)

    # ハンドラーを登録
    notification_manager.add_handler("info", test_handler)

    # 通知を送信
    notification = Notification(
        message="Test notification",
        level="info",
        timestamp=datetime.now(),
        source="test",
    )
    notification_manager.add_notification(notification)

    time.sleep(0.1)  # 非同期処理の完了を待つ

    assert len(received_notifications) == 1
    assert received_notifications[0].message == notification.message


def test_notification_filtering(notification_manager):
    """通知のフィルタリングテスト"""
    # 異なるレベルの通知を追加
    levels = ["info", "warning", "error"]
    for level in levels:
        notification = Notification(
            message=f"Test {level}",
            level=level,
            timestamp=datetime.now(),
            source="test",
        )
        notification_manager.add_notification(notification)

    time.sleep(0.1)  # 非同期処理の完了を待つ

    # レベルでフィルタリング
    info_notifications = notification_manager.get_notifications(level="info")
    assert len(info_notifications) == 1
    assert info_notifications[0].level == "info"

    # 時間範囲でフィルタリング
    start_time = datetime.now() - timedelta(minutes=1)
    end_time = datetime.now() + timedelta(minutes=1)
    time_filtered = notification_manager.get_notifications(
        start_time=start_time, end_time=end_time
    )
    assert len(time_filtered) == 3


def test_notification_persistence(notification_manager, tmp_path):
    """通知の永続化テスト"""
    # 通知を追加
    notification = Notification(
        message="Test notification",
        level="info",
        timestamp=datetime.now(),
        source="test",
    )
    notification_manager.add_notification(notification)

    time.sleep(0.1)  # 非同期処理の完了を待つ

    # 保存されたファイルを確認
    save_dir = Path.home() / ".roguelike" / "notifications"
    date_str = notification.timestamp.strftime("%Y-%m-%d")
    file_path = save_dir / f"notifications_{date_str}.json"

    assert file_path.exists()
    with file_path.open("r", encoding="utf-8") as f:
        saved_data = json.load(f)
    assert len(saved_data) > 0
    assert saved_data[0]["message"] == notification.message


def test_notification_stats(notification_manager):
    """通知の統計情報テスト"""
    # 異なるレベルと送信元の通知を追加
    notifications = [
        ("Test info", "info", "source1"),
        ("Test warning", "warning", "source1"),
        ("Test error", "error", "source2"),
    ]

    for message, level, source in notifications:
        notification = Notification(
            message=message, level=level, timestamp=datetime.now(), source=source
        )
        notification_manager.add_notification(notification)

    time.sleep(0.1)  # 非同期処理の完了を待つ

    stats = notification_manager.get_notification_stats()
    assert stats["total"] == 3
    assert stats["by_level"]["info"] == 1
    assert stats["by_level"]["warning"] == 1
    assert stats["by_level"]["error"] == 1
    assert stats["by_source"]["source1"] == 2
    assert stats["by_source"]["source2"] == 1


def test_notification_cleanup(notification_manager):
    """古い通知のクリーンアップテスト"""
    # 古い通知を追加
    old_time = datetime.now() - timedelta(days=31)
    notification = Notification(
        message="Old notification", level="info", timestamp=old_time, source="test"
    )
    notification_manager.add_notification(notification)

    # 新しい通知を追加
    new_notification = Notification(
        message="New notification",
        level="info",
        timestamp=datetime.now(),
        source="test",
    )
    notification_manager.add_notification(new_notification)

    time.sleep(0.1)  # 非同期処理の完了を待つ

    # クリーンアップを実行
    deleted = notification_manager.cleanup_old_notifications(max_age_days=30)
    assert len(deleted) == 1
    assert deleted[0].message == "Old notification"

    # 残っている通知を確認
    remaining = notification_manager.get_notifications()
    assert len(remaining) == 1
    assert remaining[0].message == "New notification"


def test_notification_batch_processing(notification_manager):
    """通知の一括処理テスト"""
    # 複数の通知を作成
    notifications = []
    for i in range(5):
        notification = Notification(
            message=f"Batch notification {i}",
            level="info",
            timestamp=datetime.now(),
            source="test",
        )
        notifications.append(notification)

    # 一括追加
    notification_manager.add_notifications(notifications)
    time.sleep(0.1)  # 非同期処理の完了を待つ

    # 追加された通知を確認
    added = notification_manager.get_notifications()
    assert len(added) == 5
    assert all(n.message.startswith("Batch notification") for n in added)


def test_notification_error_handling(notification_manager):
    """通知のエラーハンドリングテスト"""
    # 無効なレベルの通知
    with pytest.raises(ValueError):
        Notification(
            message="Invalid level",
            level="invalid_level",
            timestamp=datetime.now(),
            source="test",
        )

    # 無効なタイムスタンプ
    with pytest.raises(TypeError):
        Notification(
            message="Invalid timestamp",
            level="info",
            timestamp="invalid_time",
            source="test",
        )

    # 空のメッセージ
    with pytest.raises(ValueError):
        Notification(message="", level="info", timestamp=datetime.now(), source="test")


def test_notification_priority_handling(notification_manager):
    """通知の優先度処理テスト"""
    # 異なる優先度の通知を追加
    priorities = ["low", "medium", "high", "critical"]
    for priority in priorities:
        notification = Notification(
            message=f"Priority {priority}",
            level="info",
            timestamp=datetime.now(),
            source="test",
            details={"priority": priority},
        )
        notification_manager.add_notification(notification)

    time.sleep(0.1)  # 非同期処理の完了を待つ

    # 優先度でフィルタリング
    high_priority = notification_manager.get_notifications(
        filter_fn=lambda n: n.details.get("priority") in ["high", "critical"]
    )
    assert len(high_priority) == 2
    assert all(n.details["priority"] in ["high", "critical"] for n in high_priority)


def test_notification_aggregation(notification_manager):
    """通知の集計テスト"""
    # 同じソースから複数の通知を追加
    for i in range(5):
        notification = Notification(
            message=f"Similar notification",
            level="info",
            timestamp=datetime.now(),
            source="repeated_source",
            details={"event_type": "test_event"},
        )
        notification_manager.add_notification(notification)

    time.sleep(0.1)  # 非同期処理の完了を待つ

    # 集計結果を確認
    aggregated = notification_manager.get_aggregated_notifications(
        group_by=["source", "details.event_type"], time_window=timedelta(minutes=5)
    )

    assert len(aggregated) == 1
    assert aggregated[0]["count"] == 5
    assert aggregated[0]["source"] == "repeated_source"
    assert aggregated[0]["details"]["event_type"] == "test_event"
