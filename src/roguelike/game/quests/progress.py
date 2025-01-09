"""
クエストの進行状況を管理するモジュール。
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, TYPE_CHECKING
import json
from pathlib import Path
import logging

from roguelike.game.quests.types import QuestStatus

if TYPE_CHECKING:
    from roguelike.game.quests.quests import Quest, QuestChain

logger = logging.getLogger(__name__)


@dataclass
class ObjectiveProgress:
    """クエストの目標の進行状況を表すクラス。"""
    
    objective_id: str
    current_amount: int
    required_amount: int
    completed: bool
    completion_time: Optional[datetime] = None
    last_update: datetime = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """進行状況を辞書形式に変換する。"""
        return {
            "objective_id": self.objective_id,
            "current_amount": self.current_amount,
            "required_amount": self.required_amount,
            "completed": self.completed,
            "completion_time": self.completion_time.isoformat() if self.completion_time else None,
            "last_update": self.last_update.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObjectiveProgress':
        """辞書形式から進行状況を復元する。"""
        return cls(
            objective_id=data["objective_id"],
            current_amount=data["current_amount"],
            required_amount=data["required_amount"],
            completed=data["completed"],
            completion_time=datetime.fromisoformat(data["completion_time"]) if data["completion_time"] else None,
            last_update=datetime.fromisoformat(data["last_update"])
        )


@dataclass
class QuestProgress:
    """クエストの進行状況を表すクラス。"""
    
    quest_id: str
    status: QuestStatus
    start_time: Optional[datetime]
    completion_time: Optional[datetime]
    objectives: Dict[str, ObjectiveProgress]
    time_spent: timedelta = timedelta()
    last_update: datetime = datetime.now()
    checkpoints: List[str] = None  # 到達したチェックポイント
    
    def __post_init__(self):
        if self.checkpoints is None:
            self.checkpoints = []
    
    def update_time_spent(self) -> None:
        """経過時間を更新する。"""
        if self.status == QuestStatus.IN_PROGRESS:
            now = datetime.now()
            self.time_spent += now - self.last_update
            self.last_update = now
    
    def add_checkpoint(self, checkpoint: str) -> None:
        """チェックポイントを追加する。"""
        if checkpoint not in self.checkpoints:
            self.checkpoints.append(checkpoint)
            self.last_update = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """進行状況を辞書形式に変換する。"""
        return {
            "quest_id": self.quest_id,
            "status": self.status.name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "completion_time": self.completion_time.isoformat() if self.completion_time else None,
            "objectives": {
                obj_id: obj.to_dict()
                for obj_id, obj in self.objectives.items()
            },
            "time_spent": self.time_spent.total_seconds(),
            "last_update": self.last_update.isoformat(),
            "checkpoints": self.checkpoints
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestProgress':
        """辞書形式から進行状況を復元する。"""
        return cls(
            quest_id=data["quest_id"],
            status=QuestStatus[data["status"]],
            start_time=datetime.fromisoformat(data["start_time"]) if data["start_time"] else None,
            completion_time=datetime.fromisoformat(data["completion_time"]) if data["completion_time"] else None,
            objectives={
                obj_id: ObjectiveProgress.from_dict(obj_data)
                for obj_id, obj_data in data["objectives"].items()
            },
            time_spent=timedelta(seconds=data["time_spent"]),
            last_update=datetime.fromisoformat(data["last_update"]),
            checkpoints=data.get("checkpoints", [])
        )


class QuestProgressManager:
    """クエストの進行状況を管理するクラス。"""
    
    def __init__(self):
        self.progress: Dict[str, QuestProgress] = {}
        self.chain_progress: Dict[str, Set[str]] = {}  # チェーンIDと完了したクエストIDのセット
    
    def initialize_quest_progress(self, quest: 'Quest') -> None:
        """クエストの進行状況を初期化する。

        Args:
            quest: 初期化対象のクエスト
        """
        if quest.quest_id not in self.progress:
            self.progress[quest.quest_id] = QuestProgress(
                quest_id=quest.quest_id,
                status=quest.status,
                start_time=quest.start_time,
                completion_time=quest.completion_time,
                objectives={
                    str(i): ObjectiveProgress(
                        objective_id=str(i),
                        current_amount=obj.get_progress()[0],
                        required_amount=obj.get_progress()[1],
                        completed=obj.completed
                    )
                    for i, obj in enumerate(quest.objectives)
                }
            )
    
    def update_quest_progress(
        self,
        quest: 'Quest',
        objective_index: Optional[int] = None,
        checkpoint: Optional[str] = None
    ) -> None:
        """クエストの進行状況を更新する。

        Args:
            quest: 更新対象のクエスト
            objective_index: 更新する目標のインデックス
            checkpoint: 到達したチェックポイント
        """
        if quest.quest_id not in self.progress:
            self.initialize_quest_progress(quest)
        
        progress = self.progress[quest.quest_id]
        progress.status = quest.status
        progress.update_time_spent()
        
        if objective_index is not None:
            objective = quest.objectives[objective_index]
            obj_progress = progress.objectives[str(objective_index)]
            current, required = objective.get_progress()
            obj_progress.current_amount = current
            obj_progress.required_amount = required
            obj_progress.completed = objective.completed
            if objective.completed and not obj_progress.completion_time:
                obj_progress.completion_time = datetime.now()
        
        if checkpoint:
            progress.add_checkpoint(checkpoint)
    
    def update_chain_progress(self, chain: 'QuestChain', completed_quest_id: str) -> None:
        """クエストチェーンの進行状況を更新する。

        Args:
            chain: 更新対象のチェーン
            completed_quest_id: 完了したクエストのID
        """
        if chain.chain_id not in self.chain_progress:
            self.chain_progress[chain.chain_id] = set()
        
        self.chain_progress[chain.chain_id].add(completed_quest_id)
    
    def get_quest_completion_rate(self, quest_id: str) -> float:
        """クエストの完了率を取得する。

        Args:
            quest_id: クエストID

        Returns:
            完了率（0.0 - 1.0）
        """
        if quest_id not in self.progress:
            return 0.0
        
        progress = self.progress[quest_id]
        if not progress.objectives:
            return 0.0
        
        completed = sum(
            obj.current_amount / obj.required_amount
            for obj in progress.objectives.values()
        )
        return completed / len(progress.objectives)
    
    def get_chain_completion_rate(self, chain_id: str) -> float:
        """クエストチェーンの完了率を取得する。

        Args:
            chain_id: チェーンID

        Returns:
            完了率（0.0 - 1.0）
        """
        if chain_id not in self.chain_progress:
            return 0.0
        
        completed_quests = len(self.chain_progress[chain_id])
        total_quests = len(self.chain_progress[chain_id])  # チェーン内のクエスト総数を取得する必要あり
        return completed_quests / total_quests if total_quests > 0 else 0.0
    
    def save_progress(self, save_dir: Path) -> None:
        """進行状況をファイルに保存する。

        Args:
            save_dir: 保存先ディレクトリ
        """
        try:
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # クエストの進行状況を保存
            progress_file = save_dir / "quest_progress.json"
            progress_data = {
                quest_id: progress.to_dict()
                for quest_id, progress in self.progress.items()
            }
            with progress_file.open("w", encoding="utf-8") as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
            
            # チェーンの進行状況を保存
            chain_file = save_dir / "chain_progress.json"
            chain_data = {
                chain_id: list(completed_quests)
                for chain_id, completed_quests in self.chain_progress.items()
            }
            with chain_file.open("w", encoding="utf-8") as f:
                json.dump(chain_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved quest progress to {save_dir}")
            
        except Exception as e:
            logger.error(f"Error saving quest progress: {str(e)}", exc_info=True)
    
    def load_progress(self, save_dir: Path) -> None:
        """進行状況をファイルから読み込む。

        Args:
            save_dir: 読み込み元ディレクトリ
        """
        try:
            # クエストの進行状況を読み込み
            progress_file = save_dir / "quest_progress.json"
            if progress_file.exists():
                with progress_file.open("r", encoding="utf-8") as f:
                    progress_data = json.load(f)
                self.progress = {
                    quest_id: QuestProgress.from_dict(data)
                    for quest_id, data in progress_data.items()
                }
            
            # チェーンの進行状況を読み込み
            chain_file = save_dir / "chain_progress.json"
            if chain_file.exists():
                with chain_file.open("r", encoding="utf-8") as f:
                    chain_data = json.load(f)
                self.chain_progress = {
                    chain_id: set(completed_quests)
                    for chain_id, completed_quests in chain_data.items()
                }
            
            logger.info(f"Loaded quest progress from {save_dir}")
            
        except Exception as e:
            logger.error(f"Error loading quest progress: {str(e)}", exc_info=True)
    
    def get_quest_statistics(self, quest_id: str) -> Dict[str, Any]:
        """クエストの統計情報を取得する。

        Args:
            quest_id: クエストID

        Returns:
            統計情報の辞書
        """
        if quest_id not in self.progress:
            return {}
        
        progress = self.progress[quest_id]
        return {
            "completion_rate": self.get_quest_completion_rate(quest_id),
            "time_spent": progress.time_spent.total_seconds(),
            "objectives_completed": sum(1 for obj in progress.objectives.values() if obj.completed),
            "total_objectives": len(progress.objectives),
            "checkpoints_reached": len(progress.checkpoints),
            "last_update": progress.last_update.isoformat()
        }
    
    def get_chain_statistics(self, chain_id: str) -> Dict[str, Any]:
        """クエストチェーンの統計情報を取得する。

        Args:
            chain_id: チェーンID

        Returns:
            統計情報の辞書
        """
        if chain_id not in self.chain_progress:
            return {}
        
        completed_quests = self.chain_progress[chain_id]
        total_time = sum(
            self.progress[quest_id].time_spent.total_seconds()
            for quest_id in completed_quests
            if quest_id in self.progress
        )
        
        return {
            "completion_rate": self.get_chain_completion_rate(chain_id),
            "completed_quests": len(completed_quests),
            "total_time_spent": total_time,
            "average_time_per_quest": total_time / len(completed_quests) if completed_quests else 0
        } 