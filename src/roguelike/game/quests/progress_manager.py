"""
Module for managing quest progress.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from roguelike.game.quests.quests import Quest, QuestChain


class QuestProgress:
    """Class representing quest progress."""

    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.last_update: Optional[datetime] = None
        self.time_spent = timedelta()
        self.objective_progress: Dict[int, float] = {}  # Index: Progress
        self.checkpoints: List[Dict[str, Any]] = []

    def update_time_spent(self) -> None:
        """Update elapsed time."""
        if self.last_update:
            now = datetime.now()
            self.time_spent += now - self.last_update
            self.last_update = now

    def add_checkpoint(self, description: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Add a checkpoint.

        Args:
            description: Checkpoint description
            data: Additional data
        """
        self.checkpoints.append({
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "data": data or {}
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert progress to dictionary.

        Returns:
            Converted data
        """
        return {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "time_spent": self.time_spent.total_seconds(),
            "objective_progress": self.objective_progress,
            "checkpoints": self.checkpoints
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestProgress':
        """Restore progress from dictionary.

        Args:
            data: Source data

        Returns:
            Restored progress
        """
        progress = cls()
        if data["start_time"]:
            progress.start_time = datetime.fromisoformat(data["start_time"])
        if data["last_update"]:
            progress.last_update = datetime.fromisoformat(data["last_update"])
        progress.time_spent = timedelta(seconds=data["time_spent"])
        progress.objective_progress = data["objective_progress"]
        progress.checkpoints = data["checkpoints"]
        return progress


class ChainProgress:
    """Class representing quest chain progress."""

    def __init__(self):
        self.discovered_time: Optional[datetime] = None
        self.completion_time: Optional[datetime] = None
        self.quest_order: List[str] = []  # Quest ID order
        self.current_quest_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert progress to dictionary.

        Returns:
            Converted data
        """
        return {
            "discovered_time": (
                self.discovered_time.isoformat()
                if self.discovered_time else None
            ),
            "completion_time": (
                self.completion_time.isoformat()
                if self.completion_time else None
            ),
            "quest_order": self.quest_order,
            "current_quest_id": self.current_quest_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChainProgress':
        """Restore progress from dictionary.

        Args:
            data: Source data

        Returns:
            Restored progress
        """
        progress = cls()
        if data["discovered_time"]:
            progress.discovered_time = datetime.fromisoformat(data["discovered_time"])
        if data["completion_time"]:
            progress.completion_time = datetime.fromisoformat(data["completion_time"])
        progress.quest_order = data["quest_order"]
        progress.current_quest_id = data["current_quest_id"]
        return progress


class QuestProgressManager:
    """Class for managing quest progress."""

    def __init__(self):
        self.progress: Dict[str, QuestProgress] = {}  # Quest ID: Progress
        self.chain_progress: Dict[str, ChainProgress] = {}  # Chain ID: Progress

    def initialize_quest_progress(self, quest: 'Quest') -> None:
        """Initialize quest progress.

        Args:
            quest: Target quest
        """
        if quest.quest_id not in self.progress:
            progress = QuestProgress()
            progress.start_time = datetime.now()
            progress.last_update = progress.start_time
            self.progress[quest.quest_id] = progress

    def update_quest_progress(self, quest: 'Quest', objective_index: Optional[int] = None) -> None:
        """Update quest progress.

        Args:
            quest: Target quest
            objective_index: Index of objective to update
        """
        if quest.quest_id not in self.progress:
            self.initialize_quest_progress(quest)

        progress = self.progress[quest.quest_id]
        progress.update_time_spent()

        if objective_index is not None:
            objective = quest.objectives[objective_index]
            current, required = objective.get_progress()
            progress.objective_progress[objective_index] = current / required

            # Add checkpoint
            if objective.completed:
                progress.add_checkpoint(
                    f"Completed objective: {objective.description}",
                    {
                        "objective_index": objective_index,
                        "time_spent": progress.time_spent.total_seconds()
                    }
                )

    def update_chain_progress(self, chain: 'QuestChain', completed_quest_id: str) -> None:
        """Update quest chain progress.

        Args:
            chain: Target chain
            completed_quest_id: ID of completed quest
        """
        if chain.chain_id not in self.chain_progress:
            progress = ChainProgress()
            progress.discovered_time = datetime.now()
            self.chain_progress[chain.chain_id] = progress

        progress = self.chain_progress[chain.chain_id]

        # Record completed quest
        if completed_quest_id not in progress.quest_order:
            progress.quest_order.append(completed_quest_id)

        # Set next quest
        next_index = chain.quest_ids.index(completed_quest_id) + 1
        if next_index < len(chain.quest_ids):
            progress.current_quest_id = chain.quest_ids[next_index]
        else:
            progress.current_quest_id = None
            progress.completion_time = datetime.now()

    def get_quest_progress(self, quest_id: str) -> Optional[QuestProgress]:
        """Get quest progress.

        Args:
            quest_id: Quest ID

        Returns:
            Progress (None if not found)
        """
        return self.progress.get(quest_id)

    def get_chain_progress(self, chain_id: str) -> Optional[ChainProgress]:
        """Get quest chain progress.

        Args:
            chain_id: Chain ID

        Returns:
            Progress (None if not found)
        """
        return self.chain_progress.get(chain_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert progress to dictionary.

        Returns:
            Converted data
        """
        return {
            "quests": {
                quest_id: progress.to_dict()
                for quest_id, progress in self.progress.items()
            },
            "chains": {
                chain_id: progress.to_dict()
                for chain_id, progress in self.chain_progress.items()
            }
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Restore progress from dictionary.

        Args:
            data: Source data
        """
        self.progress = {
            quest_id: QuestProgress.from_dict(progress_data)
            for quest_id, progress_data in data["quests"].items()
        }
        self.chain_progress = {
            chain_id: ChainProgress.from_dict(progress_data)
            for chain_id, progress_data in data["chains"].items()
        } 