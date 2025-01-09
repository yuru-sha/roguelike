"""
Module for managing quest statistics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import statistics

from roguelike.game.quests.types import QuestType

if TYPE_CHECKING:
    from roguelike.game.quests.quests import Quest

logger = logging.getLogger(__name__)


class QuestTypeStats:
    """Class representing statistics for each quest type."""

    def __init__(self):
        self.total_attempts = 0
        self.successful_completions = 0
        self.failed_attempts = 0
        self.completion_times: List[float] = []  # In seconds
        self.average_level = 0.0
        self.total_experience = 0
        self.total_gold = 0

    def update(
        self,
        completion_time: float,
        player_level: int,
        success: bool,
        experience: int = 0,
        gold: int = 0
    ) -> None:
        """Update statistics.

        Args:
            completion_time: Completion time in seconds
            player_level: Player level
            success: Whether successful
            experience: Experience gained
            gold: Gold earned
        """
        self.total_attempts += 1
        if success:
            self.successful_completions += 1
            self.completion_times.append(completion_time)
        else:
            self.failed_attempts += 1

        # Update average level
        self.average_level = (
            (self.average_level * (self.total_attempts - 1) + player_level)
            / self.total_attempts
        )

        self.total_experience += experience
        self.total_gold += gold

    def get_success_rate(self) -> float:
        """Get success rate.

        Returns:
            Success rate (0.0-1.0)
        """
        if self.total_attempts == 0:
            return 0.0
        return self.successful_completions / self.total_attempts

    def get_average_completion_time(self) -> Optional[float]:
        """Get average completion time.

        Returns:
            Average completion time in seconds, None if no data
        """
        if not self.completion_times:
            return None
        return statistics.mean(self.completion_times)

    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary.

        Returns:
            Converted data
        """
        return {
            "total_attempts": self.total_attempts,
            "successful_completions": self.successful_completions,
            "failed_attempts": self.failed_attempts,
            "completion_times": self.completion_times,
            "average_level": self.average_level,
            "total_experience": self.total_experience,
            "total_gold": self.total_gold
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestTypeStats':
        """Restore statistics from dictionary.

        Args:
            data: Source data

        Returns:
            Restored statistics
        """
        stats = cls()
        stats.total_attempts = data["total_attempts"]
        stats.successful_completions = data["successful_completions"]
        stats.failed_attempts = data["failed_attempts"]
        stats.completion_times = data["completion_times"]
        stats.average_level = data["average_level"]
        stats.total_experience = data["total_experience"]
        stats.total_gold = data["total_gold"]
        return stats


class QuestStats:
    """Class representing statistics for individual quests."""

    def __init__(self):
        self.attempts = 0
        self.completions = 0
        self.failures = 0
        self.fastest_completion: Optional[float] = None
        self.total_time_spent = 0.0
        self.last_attempt: Optional[datetime] = None
        self.completion_history: List[Dict[str, Any]] = []

    def update(
        self,
        time_spent: float,
        success: bool,
        player_level: int,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update statistics.

        Args:
            time_spent: Time spent in seconds
            success: Whether successful
            player_level: Player level
            details: Additional details
        """
        self.attempts += 1
        self.total_time_spent += time_spent
        self.last_attempt = datetime.now()

        if success:
            self.completions += 1
            if self.fastest_completion is None or time_spent < self.fastest_completion:
                self.fastest_completion = time_spent
        else:
            self.failures += 1

        self.completion_history.append({
            "timestamp": self.last_attempt.isoformat(),
            "time_spent": time_spent,
            "success": success,
            "player_level": player_level,
            "details": details or {}
        })

        # Keep only the latest 100 records
        if len(self.completion_history) > 100:
            self.completion_history = self.completion_history[-100:]

    def get_success_rate(self) -> float:
        """Get success rate.

        Returns:
            Success rate (0.0-1.0)
        """
        if self.attempts == 0:
            return 0.0
        return self.completions / self.attempts

    def get_average_completion_time(self) -> Optional[float]:
        """Get average completion time.

        Returns:
            Average completion time in seconds, None if no data
        """
        if self.completions == 0:
            return None
        successful_attempts = [
            entry["time_spent"]
            for entry in self.completion_history
            if entry["success"]
        ]
        if not successful_attempts:
            return None
        return statistics.mean(successful_attempts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary.

        Returns:
            Converted data
        """
        return {
            "attempts": self.attempts,
            "completions": self.completions,
            "failures": self.failures,
            "fastest_completion": self.fastest_completion,
            "total_time_spent": self.total_time_spent,
            "last_attempt": self.last_attempt.isoformat() if self.last_attempt else None,
            "completion_history": self.completion_history
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Restore statistics from dictionary.

        Args:
            data: Source data
        """
        self.attempts = data["attempts"]
        self.completions = data["completions"]
        self.failures = data["failures"]
        self.fastest_completion = data["fastest_completion"]
        self.total_time_spent = data["total_time_spent"]
        if data["last_attempt"]:
            self.last_attempt = datetime.fromisoformat(data["last_attempt"])
        self.completion_history = data["completion_history"]


class QuestStatisticsManager:
    """Class for managing quest statistics."""

    def __init__(self):
        self.type_stats: Dict[str, QuestTypeStats] = {}  # Quest type: Statistics
        self.quest_stats: Dict[str, QuestStats] = {}  # Quest ID: Statistics
        self.total_quests_completed = 0
        self.total_quests_failed = 0
        self.total_experience_gained = 0
        self.total_gold_earned = 0

    def update_quest_stats(
        self,
        quest: 'Quest',
        player_level: int,
        time_spent: timedelta,
        success: bool,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update quest statistics.

        Args:
            quest: Quest to update
            player_level: Player level
            time_spent: Time spent
            success: Whether successful
            details: Additional details
        """
        # Update quest type statistics
        quest_type = quest.type.name
        if quest_type not in self.type_stats:
            self.type_stats[quest_type] = QuestTypeStats()

        self.type_stats[quest_type].update(
            time_spent.total_seconds(),
            player_level,
            success,
            quest.reward.experience if success else 0,
            quest.reward.gold if success else 0
        )

        # Update individual quest statistics
        if quest.quest_id not in self.quest_stats:
            self.quest_stats[quest.quest_id] = QuestStats()

        self.quest_stats[quest.quest_id].update(
            time_spent.total_seconds(),
            success,
            player_level,
            details
        )

        # Keep only the latest 100 records
        if len(self.completion_history) > 100:
            self.completion_history = self.completion_history[-100:]

        # Update overall statistics
        if success:
            self.total_quests_completed += 1
            self.total_experience_gained += quest.reward.experience
            self.total_gold_earned += quest.reward.gold
        else:
            self.total_quests_failed += 1

    def get_quest_type_summary(self, quest_type: str) -> Optional[Dict[str, Any]]:
        """Get statistical summary for quest type.

        Args:
            quest_type: Quest type

        Returns:
            Statistical summary, None if no data
        """
        stats = self.type_stats.get(quest_type)
        if not stats:
            return None

        return {
            "success_rate": stats.get_success_rate(),
            "average_completion_time": stats.get_average_completion_time(),
            "total_attempts": stats.total_attempts,
            "average_level": stats.average_level,
            "total_experience": stats.total_experience,
            "total_gold": stats.total_gold
        }

    def get_quest_summary(self, quest_id: str) -> Optional[Dict[str, Any]]:
        """Get statistical summary for individual quest.

        Args:
            quest_id: Quest ID

        Returns:
            Statistical summary, None if no data
        """
        stats = self.quest_stats.get(quest_id)
        if not stats:
            return None

        return {
            "success_rate": stats.get_success_rate(),
            "average_completion_time": stats.get_average_completion_time(),
            "fastest_completion": stats.fastest_completion,
            "total_attempts": stats.attempts,
            "last_attempt": stats.last_attempt.isoformat() if stats.last_attempt else None
        }

    def get_overall_statistics(self) -> Dict[str, Any]:
        """Get overall statistics.

        Returns:
            Statistical data
        """
        total_attempts = sum(
            stats.total_attempts
            for stats in self.type_stats.values()
        )

        return {
            "total_quests_completed": self.total_quests_completed,
            "total_quests_failed": self.total_quests_failed,
            "total_attempts": total_attempts,
            "overall_success_rate": (
                self.total_quests_completed / total_attempts
                if total_attempts > 0 else 0.0
            ),
            "total_experience_gained": self.total_experience_gained,
            "total_gold_earned": self.total_gold_earned
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary.

        Returns:
            Converted data
        """
        return {
            "type_stats": {
                quest_type: stats.to_dict()
                for quest_type, stats in self.type_stats.items()
            },
            "quest_stats": {
                quest_id: stats.to_dict()
                for quest_id, stats in self.quest_stats.items()
            },
            "total_quests_completed": self.total_quests_completed,
            "total_quests_failed": self.total_quests_failed,
            "total_experience_gained": self.total_experience_gained,
            "total_gold_earned": self.total_gold_earned
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Restore statistics from dictionary.

        Args:
            data: Source data
        """
        self.type_stats = {
            quest_type: QuestTypeStats.from_dict(stats_data)
            for quest_type, stats_data in data["type_stats"].items()
        }
        self.quest_stats = {
            quest_id: QuestStats.from_dict(stats_data)
            for quest_id, stats_data in data["quest_stats"].items()
        }
        self.total_quests_completed = data["total_quests_completed"]
        self.total_quests_failed = data["total_quests_failed"]
        self.total_experience_gained = data["total_experience_gained"]
        self.total_gold_earned = data["total_gold_earned"] 