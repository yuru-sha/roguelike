"""
Quest system type definitions.
"""

from enum import Enum, auto
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass
from datetime import datetime


class QuestType(Enum):
    """Types of quests available in the game."""
    KILL_ENEMIES = auto()      # Slay specific number/type of enemies
    COLLECT_ITEMS = auto()     # Gather specific items
    EXPLORE_LEVELS = auto()    # Reach specific dungeon level
    SURVIVE_COMBAT = auto()    # Survive in combat
    FIND_ARTIFACT = auto()     # Find specific artifact
    ESCORT_NPC = auto()        # Escort NPC
    CLEAR_AREA = auto()        # Clear all enemies in area
    TIMED_CHALLENGE = auto()   # Time-limited challenge
    CRAFT_ITEMS = auto()       # Craft items
    DISCOVER_LOCATIONS = auto()  # Discover specific locations
    DEFEAT_BOSS = auto()       # Defeat boss
    SOLVE_PUZZLE = auto()      # Solve puzzle
    TRADE_WITH_NPC = auto()    # Trade with NPC
    GATHER_RESOURCES = auto()  # Gather resources
    TRAIN_SKILLS = auto()      # Train skills


class QuestStatus(Enum):
    """Quest status enumeration."""
    NOT_STARTED = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass
class QuestCondition:
    """Represents a condition that must be met for quest progress."""
    condition_type: str  # "kill", "collect", "reach_level", "survive", "find", "escort", "clear", "time", etc.
    target_id: Optional[str] = None  # Target ID (enemy, item, location, etc.)
    target_type: Optional[str] = None  # Target type ("enemy_type", "item_category", etc.)
    required_amount: int = 1  # Required amount
    current_amount: int = 0  # Current progress
    extra_data: Optional[Dict[str, Any]] = None  # Additional parameters 