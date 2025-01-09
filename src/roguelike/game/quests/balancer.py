"""
Module for adjusting quest rewards and difficulty balance.
"""

from typing import Dict, List, Tuple, Any, Optional, TYPE_CHECKING
import math
import statistics
from datetime import datetime, timedelta

from roguelike.game.quests.types import QuestType

if TYPE_CHECKING:
    from roguelike.game.quests.quests import Quest, QuestReward


class QuestBalancer:
    """Class that adjusts quest rewards and difficulty balance."""

    def __init__(self):
        # Base rewards for each quest type
        self.base_rewards = {
            QuestType.KILL_ENEMIES.name: {
                "gold": 50,
                "experience": 100,
                "skill_points": 1
            },
            QuestType.COLLECT_ITEMS.name: {
                "gold": 40,
                "experience": 80,
                "skill_points": 1
            },
            QuestType.EXPLORE_LEVELS.name: {
                "gold": 60,
                "experience": 120,
                "skill_points": 1
            },
            QuestType.SURVIVE_COMBAT.name: {
                "gold": 70,
                "experience": 140,
                "skill_points": 1
            },
            QuestType.FIND_ARTIFACT.name: {
                "gold": 100,
                "experience": 200,
                "skill_points": 2
            },
            QuestType.ESCORT_NPC.name: {
                "gold": 80,
                "experience": 160,
                "skill_points": 1
            },
            QuestType.CLEAR_AREA.name: {
                "gold": 90,
                "experience": 180,
                "skill_points": 2
            },
            QuestType.TIMED_CHALLENGE.name: {
                "gold": 120,
                "experience": 240,
                "skill_points": 2
            },
            QuestType.CRAFT_ITEMS.name: {
                "gold": 60,
                "experience": 120,
                "skill_points": 1
            },
            QuestType.DISCOVER_LOCATIONS.name: {
                "gold": 50,
                "experience": 100,
                "skill_points": 1
            },
            QuestType.DEFEAT_BOSS.name: {
                "gold": 200,
                "experience": 400,
                "skill_points": 3
            },
            QuestType.SOLVE_PUZZLE.name: {
                "gold": 70,
                "experience": 140,
                "skill_points": 1
            },
            QuestType.TRADE_WITH_NPC.name: {
                "gold": 40,
                "experience": 80,
                "skill_points": 1
            },
            QuestType.GATHER_RESOURCES.name: {
                "gold": 30,
                "experience": 60,
                "skill_points": 1
            },
            QuestType.TRAIN_SKILLS.name: {
                "gold": 50,
                "experience": 100,
                "skill_points": 2
            }
        }

        # Difficulty coefficients for each quest type
        self.difficulty_coefficients = {
            QuestType.KILL_ENEMIES.name: 1.0,
            QuestType.COLLECT_ITEMS.name: 0.8,
            QuestType.EXPLORE_LEVELS.name: 0.9,
            QuestType.SURVIVE_COMBAT.name: 1.2,
            QuestType.FIND_ARTIFACT.name: 1.3,
            QuestType.ESCORT_NPC.name: 1.4,
            QuestType.CLEAR_AREA.name: 1.1,
            QuestType.TIMED_CHALLENGE.name: 1.5,
            QuestType.CRAFT_ITEMS.name: 0.7,
            QuestType.DISCOVER_LOCATIONS.name: 0.6,
            QuestType.DEFEAT_BOSS.name: 2.0,
            QuestType.SOLVE_PUZZLE.name: 1.0,
            QuestType.TRADE_WITH_NPC.name: 0.5,
            QuestType.GATHER_RESOURCES.name: 0.4,
            QuestType.TRAIN_SKILLS.name: 0.8
        }

        # Quest metrics for each quest type
        self.quest_metrics: Dict[str, Dict[str, Any]] = {}

    def update_metrics(
        self,
        quest: 'Quest',
        time_spent: float,
        player_level: int,
        completed: bool
    ) -> None:
        """Update quest metrics.

        Args:
            quest: Target quest
            time_spent: Time spent in seconds
            player_level: Player level
            completed: Whether quest was completed
        """
        quest_type = quest.type.name
        if quest_type not in self.quest_metrics:
            self.quest_metrics[quest_type] = {
                "completion_times": [],
                "completion_rates": [],
                "level_diffs": [],
                "objective_counts": []
            }

        metrics = self.quest_metrics[quest_type]
        metrics["completion_times"].append(time_spent)
        metrics["completion_rates"].append(1.0 if completed else 0.0)
        metrics["level_diffs"].append(player_level - quest.level_requirement)
        metrics["objective_counts"].append(len(quest.objectives))

        # Keep only the latest 100 records
        for key in metrics:
            metrics[key] = metrics[key][-100:]

        # Adjust difficulty coefficient
        if len(metrics["completion_rates"]) >= 10:
            avg_completion_rate = statistics.mean(metrics["completion_rates"])
            if avg_completion_rate > 0.8:
                # Increase difficulty if completion rate is too high
                self.difficulty_coefficients[quest_type] *= 1.1
            elif avg_completion_rate < 0.4:
                # Decrease difficulty if completion rate is too low
                self.difficulty_coefficients[quest_type] *= 0.9

    def calculate_quest_difficulty(
        self,
        quest_type: str,
        player_level: int,
        objective_count: int
    ) -> float:
        """Calculate quest difficulty.

        Args:
            quest_type: Quest type
            player_level: Player level
            objective_count: Number of objectives

        Returns:
            Difficulty score (0.0-5.0)
        """
        # Base difficulty
        base_difficulty = self.difficulty_coefficients.get(quest_type, 1.0)

        # Objective count modifier
        objective_modifier = math.log2(objective_count + 1) * 0.5

        # Metrics modifier
        metrics_modifier = 0.0
        if quest_type in self.quest_metrics:
            metrics = self.quest_metrics[quest_type]
            if metrics["completion_rates"]:
                avg_completion_rate = statistics.mean(metrics["completion_rates"])
                metrics_modifier += (1.0 - avg_completion_rate) * 0.5

            if metrics["completion_times"]:
                avg_time = statistics.mean(metrics["completion_times"])
                metrics_modifier += min(1.0, avg_time / 3600) * 0.3

        # Final difficulty calculation
        difficulty = base_difficulty + objective_modifier + metrics_modifier

        # Normalize to 0.0-5.0 range
        return min(5.0, max(0.0, difficulty))

    def get_difficulty_rating(self, difficulty: float) -> str:
        """Convert difficulty score to string representation.

        Args:
            difficulty: Difficulty score

        Returns:
            String representation of difficulty
        """
        if difficulty < 1.0:
            return "Very Easy"
        elif difficulty < 2.0:
            return "Easy"
        elif difficulty < 3.0:
            return "Normal"
        elif difficulty < 4.0:
            return "Hard"
        else:
            return "Very Hard"

    def calculate_rewards(
        self,
        quest_type: str,
        difficulty: float,
        player_level: int
    ) -> 'QuestReward':
        """Calculate quest rewards.

        Args:
            quest_type: Quest type
            difficulty: Difficulty score
            player_level: Player level

        Returns:
            Calculated rewards
        """
        # Get base rewards
        base = self.base_rewards.get(quest_type, {
            "gold": 50,
            "experience": 100,
            "skill_points": 1
        })

        # Difficulty multiplier
        difficulty_multiplier = 1.0 + (difficulty * 0.2)

        # Level multiplier
        level_multiplier = 1.0 + (player_level * 0.1)

        # Calculate final rewards
        from roguelike.game.quests.quests import QuestReward
        return QuestReward(
            gold=int(base["gold"] * difficulty_multiplier * level_multiplier),
            experience=int(base["experience"] * difficulty_multiplier * level_multiplier),
            items=[],
            special_rewards={}
        )

    def calculate_compatibility(
        self,
        quest_type: str,
        player_level: int,
        objective_count: int
    ) -> float:
        """クエストとプレイヤーの相性を計算する。

        Args:
            quest_type: クエストタイプ
            player_level: プレイヤーレベル
            objective_count: 目標の数

        Returns:
            相性スコア（0.0-1.0）
        """
        # 難易度の計算
        difficulty = self.calculate_quest_difficulty(
            quest_type,
            player_level,
            objective_count
        )

        # メトリクスに基づく調整
        metrics_score = 0.5
        if quest_type in self.quest_metrics:
            metrics = self.quest_metrics[quest_type]
            if metrics["completion_rates"]:
                avg_completion_rate = statistics.mean(metrics["completion_rates"])
                metrics_score = avg_completion_rate

        # 最適な難易度からの距離
        optimal_difficulty = 2.5  # Normal難易度の中央値
        difficulty_distance = 1.0 - (abs(difficulty - optimal_difficulty) / 5.0)

        # 最終的な相性スコア
        compatibility = (difficulty_distance * 0.7) + (metrics_score * 0.3)
        return min(1.0, max(0.0, compatibility))

    def get_recommended_quests(
        self,
        available_quests: List['Quest'],
        player_level: int,
        count: int = 3
    ) -> List[Tuple['Quest', str, float]]:
        """Get recommended quests for player.

        Args:
            available_quests: List of available quests
            player_level: Player level
            count: Number of recommendations

        Returns:
            List of tuples containing (quest, recommendation reason, compatibility score)
        """
        rated_quests = []
        for quest in available_quests:
            # Calculate compatibility score
            compatibility = self.calculate_compatibility(
                quest.type.name,
                player_level,
                len(quest.objectives)
            )

            # Determine recommendation reason
            difficulty = self.calculate_quest_difficulty(
                quest.type.name,
                player_level,
                len(quest.objectives)
            )
            rating = self.get_difficulty_rating(difficulty)

            if compatibility > 0.8:
                reason = f"Perfect match! ({rating})"
            elif compatibility > 0.6:
                reason = f"Good challenge ({rating})"
            elif compatibility > 0.4:
                reason = f"Worth trying ({rating})"
            else:
                reason = f"Might be difficult ({rating})"

            rated_quests.append((quest, reason, compatibility))

        # Sort by compatibility score
        rated_quests.sort(key=lambda x: x[2], reverse=True)
        return rated_quests[:count] 