"""
Implementation of the achievement system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import json
import logging

from roguelike.core.constants import AchievementType
from roguelike.core.event import Event, EventType, EventManager
from roguelike.game.quests.statistics import QuestStatisticsManager

logger = logging.getLogger(__name__)


class AchievementType(Enum):
    """Available achievement types."""
    
    # Basic Achievements
    FIRST_KILL = auto()          # Slay your first enemy
    KILL_STREAK = auto()         # Achieve a killing streak
    DUNGEON_DIVER = auto()       # Reach a specific dungeon level
    TREASURE_HUNTER = auto()     # Collect specific items
    SURVIVOR = auto()            # Recover to a specific HP
    WARRIOR = auto()             # Reach a specific level
    EQUIPMENT_MASTER = auto()    # Fill all equipment slots
    SPEED_RUNNER = auto()        # Clear within a specific time
    PACIFIST = auto()           # Progress without slaying enemies
    PERFECTIONIST = auto()      # Unlock all achievements

    # Statistics-based Achievements
    COMBAT_MASTER = auto()       # Based on combat statistics
    QUEST_MASTER = auto()        # Based on quest completion rate
    TIME_MASTER = auto()         # Based on playtime
    EFFICIENCY_MASTER = auto()   # Based on efficiency
    EXPLORATION_MASTER = auto()  # Based on exploration completion rate

    # Playstyle Achievements
    BERSERKER = auto()          # Aggressive playstyle
    TACTICIAN = auto()          # Tactical playstyle
    COLLECTOR = auto()          # Collector playstyle
    SPEEDSTER = auto()          # Speed-focused playstyle
    SURVIVOR_STYLE = auto()     # Survival-focused playstyle

    # Challenge Achievements
    NO_DAMAGE = auto()          # Clear without taking damage
    SOLO_CHALLENGE = auto()     # Clear solo
    TIME_ATTACK = auto()        # Clear with time limit
    HARD_MODE = auto()          # Clear on hard settings
    SPECIAL_CONDITION = auto()  # Clear under special conditions


@dataclass
class Achievement:
    """Class representing an achievement."""

    type: AchievementType
    name: str
    description: str
    points: int
    hidden: bool = False
    unlocked: bool = False
    unlock_date: Optional[datetime] = None
    progress: float = 0.0
    required_progress: float = 100.0
    unlock_conditions: Dict[str, Any] = field(default_factory=dict)
    rewards: Dict[str, Any] = field(default_factory=dict)
    related_achievements: Set[AchievementType] = field(default_factory=set)

    def unlock(self) -> None:
        """Unlock the achievement."""
        if not self.unlocked:
            self.unlocked = True
            self.unlock_date = datetime.now()
            self.progress = self.required_progress
            logger.info(f"Achievement unlocked: {self.name}")

    def update_progress(self, amount: float) -> bool:
        """Update achievement progress.

        Args:
            amount: Progress amount

        Returns:
            Whether the achievement was unlocked
        """
        if self.unlocked:
            return False

        self.progress = min(self.progress + amount, self.required_progress)
        unlocked = self.progress >= self.required_progress
        if unlocked:
            self.unlock()
        return unlocked

    def to_dict(self) -> Dict[str, Any]:
        """Convert achievement to dictionary.

        Returns:
            Converted data
        """
        return {
            "type": self.type.name,
            "name": self.name,
            "description": self.description,
            "points": self.points,
            "hidden": self.hidden,
            "unlocked": self.unlocked,
            "unlock_date": self.unlock_date.isoformat() if self.unlock_date else None,
            "progress": self.progress,
            "required_progress": self.required_progress,
            "unlock_conditions": self.unlock_conditions,
            "rewards": self.rewards,
            "related_achievements": [a.name for a in self.related_achievements]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Achievement':
        """Restore achievement from dictionary.

        Args:
            data: Source data

        Returns:
            Restored achievement
        """
        achievement = cls(
            type=AchievementType[data["type"]],
            name=data["name"],
            description=data["description"],
            points=data["points"],
            hidden=data["hidden"],
            unlocked=data["unlocked"],
            progress=data["progress"],
            required_progress=data["required_progress"],
            unlock_conditions=data["unlock_conditions"],
            rewards=data["rewards"]
        )
        if data["unlock_date"]:
            achievement.unlock_date = datetime.fromisoformat(data["unlock_date"])
        achievement.related_achievements = {
            AchievementType[name] for name in data["related_achievements"]
        }
        return achievement


class AchievementManager:
    """Class for managing achievements."""
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AchievementManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.achievements: Dict[AchievementType, Achievement] = {}
            self.stats_manager = QuestStatisticsManager()
            self.event_manager = EventManager.get_instance()
            self._initialize_achievements()
            self._register_event_handlers()
            self._initialized = True

    def _initialize_achievements(self) -> None:
        """Initialize available achievements."""
        # Basic Achievements
        self.achievements[AchievementType.FIRST_KILL] = Achievement(
            type=AchievementType.FIRST_KILL,
            name="First Blood",
            description="Thou hast slain thy first foe",
            points=10
        )

        self.achievements[AchievementType.KILL_STREAK] = Achievement(
            type=AchievementType.KILL_STREAK,
            name="Killing Spree",
            description="Slay 10 enemies in succession",
            points=20,
            required_progress=10
        )

        self.achievements[AchievementType.DUNGEON_DIVER] = Achievement(
            type=AchievementType.DUNGEON_DIVER,
            name="Deep Diver",
            description="Descend to level 10 of the dungeon",
            points=30,
            required_progress=10
        )

        # Statistics-based Achievements
        self.achievements[AchievementType.COMBAT_MASTER] = Achievement(
            type=AchievementType.COMBAT_MASTER,
            name="Combat Master",
            description="Achieve a victory rate of 80% in combat",
            points=50,
            required_progress=80,
            unlock_conditions={"min_battles": 50}
        )

        self.achievements[AchievementType.QUEST_MASTER] = Achievement(
            type=AchievementType.QUEST_MASTER,
            name="Quest Master",
            description="Complete 90% of all quests",
            points=100,
            required_progress=90,
            unlock_conditions={"min_quests": 20}
        )

        self.achievements[AchievementType.TIME_MASTER] = Achievement(
            type=AchievementType.TIME_MASTER,
            name="Time Master",
            description="Survive for 100 hours in the dungeon",
            points=50,
            required_progress=100
        )

        # Playstyle Achievements
        self.achievements[AchievementType.BERSERKER] = Achievement(
            type=AchievementType.BERSERKER,
            name="Berserker",
            description="Achieve a critical hit rate of 30%",
            points=30,
            required_progress=30,
            unlock_conditions={"min_attacks": 100}
        )

        self.achievements[AchievementType.TACTICIAN] = Achievement(
            type=AchievementType.TACTICIAN,
            name="Tactician",
            description="Achieve an evasion rate of 40%",
            points=40,
            required_progress=40,
            unlock_conditions={"min_battles": 50}
        )

        # Challenge Achievements
        self.achievements[AchievementType.NO_DAMAGE] = Achievement(
            type=AchievementType.NO_DAMAGE,
            name="Untouchable",
            description="Clear a level without taking damage",
            points=100,
            hidden=True
        )

        self.achievements[AchievementType.TIME_ATTACK] = Achievement(
            type=AchievementType.TIME_ATTACK,
            name="Speed Demon",
            description="Clear the dungeon in 30 minutes",
            points=150,
            hidden=True
        )

    def _register_event_handlers(self) -> None:
        """Register event handlers."""
        self.event_manager.subscribe(EventType.COMBAT_KILL, self._handle_kill)
        self.event_manager.subscribe(EventType.COMBAT_DAMAGE, self._handle_damage_taken)
        self.event_manager.subscribe(EventType.ITEM_PICKED_UP, self._handle_item_pickup)
        self.event_manager.subscribe(EventType.ITEM_USED, self._handle_item_used)
        self.event_manager.subscribe(EventType.EQUIPMENT_CHANGED, self._handle_equipment_change)
        self.event_manager.subscribe(EventType.COMBAT_LEVEL_UP, self._handle_level_up)
        self.event_manager.subscribe(EventType.LEVEL_CHANGED, self._handle_level_change)

    def _handle_kill(self, event: Event) -> None:
        """Handle event when an enemy is slain."""
        # First Kill achievement
        if not self.achievements[AchievementType.FIRST_KILL].unlocked:
            self.achievements[AchievementType.FIRST_KILL].unlock()

        # Kill Streak achievement
        self.achievements[AchievementType.KILL_STREAK].update_progress(1)

        # Combat Master achievement update
        stats = self.stats_manager.get_overall_statistics()
        if stats["total_battles"] >= self.achievements[AchievementType.COMBAT_MASTER].unlock_conditions["min_battles"]:
            win_rate = stats["wins"] / stats["total_battles"] * 100
            self.achievements[AchievementType.COMBAT_MASTER].progress = win_rate
            if win_rate >= self.achievements[AchievementType.COMBAT_MASTER].required_progress:
                self.achievements[AchievementType.COMBAT_MASTER].unlock()

    def _handle_damage_taken(self, event: Event) -> None:
        """Handle event when damage is taken."""
        # No Damage achievement check
        if event.data.get("damage", 0) > 0:
            self.achievements[AchievementType.NO_DAMAGE].progress = 0

        # Tactician achievement update
        stats = self.stats_manager.get_overall_statistics()
        if stats["total_attacks"] >= self.achievements[AchievementType.TACTICIAN].unlock_conditions["min_battles"]:
            dodge_rate = stats["dodges"] / stats["total_attacks"] * 100
            self.achievements[AchievementType.TACTICIAN].progress = dodge_rate

    def _handle_item_pickup(self, event: Event) -> None:
        """Handle event when an item is picked up."""
        # Treasure Hunter achievement update
        stats = self.stats_manager.get_overall_statistics()
        unique_items = stats.get("unique_items_collected", 0)
        self.achievements[AchievementType.TREASURE_HUNTER].progress = unique_items

    def _handle_item_used(self, event: Event) -> None:
        """Handle event when an item is used."""
        # Survivor achievement update
        if event.data.get("heal_amount", 0) > 0:
            current_hp = event.data.get("current_hp", 0)
            max_hp = event.data.get("max_hp", 0)
            if max_hp > 0:
                hp_percentage = (current_hp / max_hp) * 100
                if hp_percentage >= 100:
                    self.achievements[AchievementType.SURVIVOR].unlock()

    def _handle_equipment_change(self, event: Event) -> None:
        """Handle event when equipment is changed."""
        # Equipment Master achievement update
        if event.data.get("action") == "equip":
            stats = self.stats_manager.get_overall_statistics()
            equipped_slots = stats.get("equipped_slots", 0)
            total_slots = stats.get("total_equipment_slots", 0)
            if total_slots > 0 and equipped_slots == total_slots:
                self.achievements[AchievementType.EQUIPMENT_MASTER].unlock()

    def _handle_level_up(self, event: Event) -> None:
        """Handle event when a level is gained."""
        # Warrior achievement update
        new_level = event.data.get("new_level", 1)
        if new_level >= 10:
            self.achievements[AchievementType.WARRIOR].unlock()

    def _handle_level_change(self, event: Event) -> None:
        """Handle event when a level is changed."""
        # Dungeon Diver achievement update
        new_level = event.data.get("new_level", 1)
        self.achievements[AchievementType.DUNGEON_DIVER].progress = new_level

        # Time Attack achievement check
        if new_level >= 10:
            stats = self.stats_manager.get_overall_statistics()
            if stats["play_time"].total_seconds() <= 1800:  # 30 minutes
                self.achievements[AchievementType.TIME_ATTACK].unlock()

    def reset_progress(self) -> None:
        """Reset progress for all achievements."""
        for achievement in self.achievements.values():
            achievement.unlocked = False
            achievement.unlock_date = None
            achievement.progress = 0.0

    def unlock_achievement(self, achievement_type: AchievementType) -> None:
        """Unlock a specific achievement.

        Args:
            achievement_type: Type of the achievement to unlock
        """
        if achievement_type in self.achievements:
            achievement = self.achievements[achievement_type]
            if not achievement.unlocked:
                achievement.unlock()

                # Perfectionist achievement check
                all_unlocked = all(
                    a.unlocked for a in self.achievements.values()
                    if a.type != AchievementType.PERFECTIONIST
                )
                if all_unlocked:
                    self.achievements[AchievementType.PERFECTIONIST].unlock()

    def save_achievements(self, save_dir: Path) -> None:
        """Save achievements to file.

        Args:
            save_dir: Directory to save to
        """
        try:
            save_dir.mkdir(parents=True, exist_ok=True)
            save_file = save_dir / "achievements.json"

            # Create backup
            if save_file.exists():
                backup_file = save_dir / f"achievements_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                save_file.rename(backup_file)

            # Save new data
            with save_file.open("w", encoding="utf-8") as f:
                json.dump(
                    {
                        "achievements": {
                            achievement_type.name: achievement.to_dict()
                            for achievement_type, achievement in self.achievements.items()
                        }
                    },
                    f,
                    indent=2,
                    ensure_ascii=False
                )

            logger.info(f"Achievements saved to {save_file}")

        except Exception as e:
            logger.error(f"Error saving achievements: {e}", exc_info=True)
            raise

    def load_achievements(self, save_dir: Path) -> None:
        """Load achievements from file.

        Args:
            save_dir: Directory to load from
        """
        try:
            save_file = save_dir / "achievements.json"
            if not save_file.exists():
                logger.info("No achievement save file found")
                return

            with save_file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            for achievement_name, achievement_data in data["achievements"].items():
                achievement_type = AchievementType[achievement_name]
                if achievement_type in self.achievements:
                    loaded_achievement = Achievement.from_dict(achievement_data)
                    self.achievements[achievement_type] = loaded_achievement

            logger.info(f"Achievements loaded from {save_file}")

        except Exception as e:
            logger.error(f"Error loading achievements: {e}", exc_info=True)
            raise

    def get_unlocked_achievements(self) -> List[Achievement]:
        """Get list of unlocked achievements.

        Returns:
            List of unlocked achievements
        """
        return [
            achievement for achievement in self.achievements.values()
            if achievement.unlocked
        ]

    def get_achievement_points(self) -> int:
        """Get total achievement points.

        Returns:
            Total achievement points
        """
        return sum(
            achievement.points
            for achievement in self.achievements.values()
            if achievement.unlocked
        )

    @classmethod
    def get_instance(cls) -> 'AchievementManager':
        """Get singleton instance.

        Returns:
            AchievementManager instance
        """
        return cls() 