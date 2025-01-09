"""
Quest save manager.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, TYPE_CHECKING
import gzip
import base64

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from roguelike.game.quests.quests import (
        Quest, QuestChain, QuestObjective,
        QuestReward, QuestChainReward
    )
    from roguelike.game.quests.progress import QuestLog, QuestLogEntry
    from roguelike.game.quests.types import QuestStatus, QuestCondition

class QuestSaveManager:
    """Class for managing quest progress save/load."""

    def __init__(self, save_dir: Path):
        self.save_dir = save_dir
        self.backup_count = 3  # Number of backups to keep

    def save_quest_data(
        self,
        quests: Dict[str, 'Quest'],
        quest_chains: Dict[str, 'QuestChain'],
        quest_log: 'QuestLog',
        progress_data: Dict[str, Any],
        statistics_data: Dict[str, Any],
        difficulty_data: Dict[str, Any]
    ) -> None:
        """Save quest data.

        Args:
            quests: Quest dictionary
            quest_chains: Quest chain dictionary
            quest_log: Quest log
            progress_data: Progress data
            statistics_data: Statistics data
            difficulty_data: Difficulty data
        """
        try:
            # Create save directory
            self.save_dir.mkdir(parents=True, exist_ok=True)

            # Backup existing save data
            self._backup_existing_saves()

            # Save quest data
            quest_file = self.save_dir / "quests.json.gz"
            quest_data = {
                "quests": {
                    quest_id: self._serialize_quest(quest)
                    for quest_id, quest in quests.items()
                },
                "chains": {
                    chain_id: self._serialize_quest_chain(chain)
                    for chain_id, chain in quest_chains.items()
                },
                "log": self._serialize_quest_log(quest_log),
                "progress": progress_data,
                "statistics": statistics_data,
                "difficulty": difficulty_data,
                "save_timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }

            # Compress and save data
            compressed_data = gzip.compress(
                json.dumps(quest_data, indent=2).encode('utf-8')
            )
            quest_file.write_bytes(compressed_data)

            # Calculate and save checksum
            checksum = self._calculate_checksum(compressed_data)
            checksum_file = self.save_dir / "quests.checksum"
            checksum_file.write_text(checksum)

            logger.info(f"Quest data saved successfully to {quest_file}")

        except Exception as e:
            logger.error(f"Error saving quest data: {str(e)}", exc_info=True)
            raise

    def load_quest_data(self) -> Dict[str, Any]:
        """クエストデータを読み込む。

        Returns:
            読み込まれたクエストデータ
        """
        try:
            quest_file = self.save_dir / "quests.json.gz"
            if not quest_file.exists():
                logger.warning("No quest save data found")
                return {}

            # チェックサムの検証
            checksum_file = self.save_dir / "quests.checksum"
            if checksum_file.exists():
                saved_checksum = checksum_file.read_text().strip()
                compressed_data = quest_file.read_bytes()
                current_checksum = self._calculate_checksum(compressed_data)
                if saved_checksum != current_checksum:
                    logger.error("Checksum verification failed")
                    return self._load_backup()

            # データの読み込みと解凍
            compressed_data = quest_file.read_bytes()
            quest_data = json.loads(gzip.decompress(compressed_data).decode('utf-8'))

            # バージョンの確認
            if quest_data.get("version") != "1.0.0":
                logger.warning("Save data version mismatch")
                return self._load_backup()

            # データの復元
            return {
                "quests": {
                    quest_id: self._deserialize_quest(data)
                    for quest_id, data in quest_data["quests"].items()
                },
                "chains": {
                    chain_id: self._deserialize_quest_chain(data)
                    for chain_id, data in quest_data["chains"].items()
                },
                "log": self._deserialize_quest_log(quest_data["log"]),
                "progress": quest_data["progress"],
                "statistics": quest_data["statistics"],
                "difficulty": quest_data["difficulty"]
            }

        except Exception as e:
            logger.error(f"Error loading quest data: {str(e)}", exc_info=True)
            return self._load_backup()

    def _backup_existing_saves(self) -> None:
        """Backup existing save data."""
        quest_file = self.save_dir / "quests.json.gz"
        if not quest_file.exists():
            return

        # 古いバックアップの削除
        for i in range(self.backup_count, 0, -1):
            old_backup = self.save_dir / f"quests.json.gz.bak{i}"
            if old_backup.exists():
                if i == self.backup_count:
                    old_backup.unlink()
                else:
                    old_backup.rename(self.save_dir / f"quests.json.gz.bak{i+1}")

        # 現在のセーブデータをバックアップ
        quest_file.rename(self.save_dir / "quests.json.gz.bak1")

    def _load_backup(self) -> Dict[str, Any]:
        """最新のバックアップを読み込む。

        Returns:
            バックアップから読み込まれたデータ
        """
        for i in range(1, self.backup_count + 1):
            backup_file = self.save_dir / f"quests.json.gz.bak{i}"
            if backup_file.exists():
                try:
                    compressed_data = backup_file.read_bytes()
                    quest_data = json.loads(
                        gzip.decompress(compressed_data).decode('utf-8')
                    )
                    logger.info(f"Successfully loaded backup {i}")
                    return quest_data
                except Exception as e:
                    logger.error(
                        f"Error loading backup {i}: {str(e)}",
                        exc_info=True
                    )

        logger.error("No valid backups found")
        return {}

    def _calculate_checksum(self, data: bytes) -> str:
        """Calculate data checksum.

        Args:
            data: Data to calculate checksum for

        Returns:
            Checksum string
        """
        return base64.b64encode(data).decode('utf-8')

    def _serialize_quest(self, quest: 'Quest') -> Dict[str, Any]:
        """Serialize quest.

        Args:
            quest: Quest to serialize

        Returns:
            Serialized data
        """
        return {
            "quest_id": quest.quest_id,
            "type": quest.type.name,
            "name": quest.name,
            "description": quest.description,
            "objectives": [
                self._serialize_objective(obj)
                for obj in quest.objectives
            ],
            "reward": self._serialize_reward(quest.reward),
            "level_requirement": quest.level_requirement,
            "time_limit": quest.time_limit,
            "prerequisites": quest.prerequisites,
            "hidden": quest.hidden,
            "fail_conditions": quest.fail_conditions,
            "status": quest.status.name,
            "start_time": quest.start_time.isoformat() if quest.start_time else None,
            "completion_time": quest.completion_time.isoformat() if quest.completion_time else None,
            "fail_reason": quest.fail_reason
        }

    def _deserialize_quest(self, data: Dict[str, Any]) -> 'Quest':
        """Deserialize quest.

        Args:
            data: Data to deserialize

        Returns:
            Deserialized quest
        """
        objectives = [
            self._deserialize_objective(obj_data)
            for obj_data in data["objectives"]
        ]

        reward = self._deserialize_reward(data["reward"])

        quest = Quest(
            quest_id=data["quest_id"],
            type=QuestType[data["type"]],
            name=data["name"],
            description=data["description"],
            objectives=objectives,
            reward=reward,
            level_requirement=data["level_requirement"],
            time_limit=data["time_limit"],
            prerequisites=data["prerequisites"],
            hidden=data["hidden"],
            fail_conditions=data["fail_conditions"]
        )

        quest.status = QuestStatus[data["status"]]
        if data["start_time"]:
            quest.start_time = datetime.fromisoformat(data["start_time"])
        if data["completion_time"]:
            quest.completion_time = datetime.fromisoformat(data["completion_time"])
        quest.fail_reason = data["fail_reason"]

        return quest

    def _serialize_objective(self, objective: 'QuestObjective') -> Dict[str, Any]:
        """Serialize quest objective.

        Args:
            objective: Objective to serialize

        Returns:
            Serialized data
        """
        return {
            "description": objective.description,
            "current": objective.get_progress()[0],
            "required": objective.get_progress()[1],
            "completed": objective.completed
        }

    def _deserialize_objective(self, data: Dict[str, Any]) -> 'QuestObjective':
        """Deserialize quest objective.

        Args:
            data: Data to deserialize

        Returns:
            Deserialized objective
        """
        from roguelike.game.quests.quests import QuestObjective
        return QuestObjective(
            description=data["description"],
            current=data["current"],
            required=data["required"],
            completed=data["completed"]
        )

    def _serialize_condition(self, condition: 'QuestCondition') -> Dict[str, Any]:
        """Serialize quest condition.

        Args:
            condition: Condition to serialize

        Returns:
            Serialized data
        """
        return {
            "condition_type": condition.condition_type,
            "target_id": condition.target_id,
            "target_type": condition.target_type,
            "required_amount": condition.required_amount,
            "current_amount": condition.current_amount,
            "extra_data": condition.extra_data
        }

    def _deserialize_condition(self, data: Dict[str, Any]) -> 'QuestCondition':
        """Deserialize quest condition.

        Args:
            data: Data to deserialize

        Returns:
            Deserialized condition
        """
        from roguelike.game.quests.types import QuestCondition
        return QuestCondition(
            condition_type=data["condition_type"],
            target_id=data.get("target_id"),
            target_type=data.get("target_type"),
            required_amount=data["required_amount"],
            current_amount=data["current_amount"],
            extra_data=data.get("extra_data")
        )

    def _serialize_reward(self, reward: 'QuestReward') -> Dict[str, Any]:
        """Serialize quest reward.

        Args:
            reward: Reward to serialize

        Returns:
            Serialized data
        """
        return {
            "experience": reward.experience,
            "gold": reward.gold,
            "items": reward.items,
            "special_rewards": reward.special_rewards
        }

    def _deserialize_reward(self, data: Dict[str, Any]) -> 'QuestReward':
        """Deserialize quest reward.

        Args:
            data: Data to deserialize

        Returns:
            Deserialized reward
        """
        from roguelike.game.quests.quests import QuestReward
        return QuestReward(
            experience=data["experience"],
            gold=data["gold"],
            items=data["items"],
            special_rewards=data["special_rewards"]
        )

    def _serialize_quest_chain(self, chain: 'QuestChain') -> Dict[str, Any]:
        """Serialize quest chain.

        Args:
            chain: Chain to serialize

        Returns:
            Serialized data
        """
        return {
            "chain_id": chain.chain_id,
            "name": chain.name,
            "description": chain.description,
            "quest_ids": chain.quest_ids,
            "reward": self._serialize_reward(chain.reward) if chain.reward else None,
            "prerequisites": chain.prerequisites,
            "hidden": chain.hidden
        }

    def _deserialize_quest_chain(self, data: Dict[str, Any]) -> 'QuestChain':
        """Deserialize quest chain.

        Args:
            data: Data to deserialize

        Returns:
            Deserialized chain
        """
        from roguelike.game.quests.quests import QuestChain
        return QuestChain(
            chain_id=data["chain_id"],
            name=data["name"],
            description=data["description"],
            quest_ids=data["quest_ids"],
            reward=self._deserialize_reward(data["reward"]) if data["reward"] else None,
            prerequisites=data["prerequisites"],
            hidden=data["hidden"]
        )

    def _serialize_quest_log(self, log: 'QuestLog') -> Dict[str, Any]:
        """Serialize quest log.

        Args:
            log: Log to serialize

        Returns:
            Serialized data
        """
        return {
            "entries": [
                self._serialize_log_entry(entry)
                for entry in log.entries
            ],
            "active_quests": list(log.active_quests),
            "completed_quests": list(log.completed_quests),
            "failed_quests": list(log.failed_quests)
        }

    def _deserialize_quest_log(self, data: Dict[str, Any]) -> 'QuestLog':
        """Deserialize quest log.

        Args:
            data: Data to deserialize

        Returns:
            Deserialized log
        """
        from roguelike.game.quests.progress import QuestLog
        log = QuestLog()
        log.entries = [
            self._deserialize_log_entry(entry_data)
            for entry_data in data["entries"]
        ]
        log.active_quests = set(data["active_quests"])
        log.completed_quests = set(data["completed_quests"])
        log.failed_quests = set(data["failed_quests"])
        return log

    def _serialize_log_entry(self, entry: 'QuestLogEntry') -> Dict[str, Any]:
        """Serialize quest log entry.

        Args:
            entry: Entry to serialize

        Returns:
            Serialized data
        """
        return {
            "quest_id": entry.quest_id,
            "timestamp": entry.timestamp.isoformat(),
            "message": entry.message,
            "status": entry.status.name
        }

    def _deserialize_log_entry(self, data: Dict[str, Any]) -> 'QuestLogEntry':
        """Deserialize quest log entry.

        Args:
            data: Data to deserialize

        Returns:
            Deserialized entry
        """
        from roguelike.game.quests.progress import QuestLogEntry
        return QuestLogEntry(
            quest_id=data["quest_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message=data["message"],
            status=QuestStatus[data["status"]]
        ) 
