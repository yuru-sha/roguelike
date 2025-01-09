"""
Module for dynamically adjusting quest difficulty.
"""

from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
import math
import statistics
from datetime import datetime, timedelta

from roguelike.game.quests.types import QuestType

if TYPE_CHECKING:
    from roguelike.game.quests.quests import Quest, QuestObjective


class QuestDifficultyAdjuster:
    """Class that dynamically adjusts quest difficulty."""

    def __init__(self):
        # Base parameters for each quest type
        self.base_parameters = {
            QuestType.KILL_ENEMIES.name: {
                "amount_range": (3, 15),  # (min, max)
                "time_limit_range": (300, 1800),  # in seconds
                "level_scaling": 1.2  # Level scaling coefficient
            },
            QuestType.COLLECT_ITEMS.name: {
                "amount_range": (2, 10),
                "time_limit_range": (600, 3600),
                "level_scaling": 1.1
            },
            QuestType.EXPLORE_LEVELS.name: {
                "amount_range": (1, 5),
                "time_limit_range": (900, 3600),
                "level_scaling": 1.0
            },
            QuestType.SURVIVE_COMBAT.name: {
                "amount_range": (1, 5),
                "time_limit_range": (180, 900),
                "level_scaling": 1.3
            },
            QuestType.FIND_ARTIFACT.name: {
                "amount_range": (1, 3),
                "time_limit_range": (1200, 3600),
                "level_scaling": 1.2
            },
            QuestType.ESCORT_NPC.name: {
                "amount_range": (1, 1),
                "time_limit_range": (600, 1800),
                "level_scaling": 1.4
            },
            QuestType.CLEAR_AREA.name: {
                "amount_range": (10, 30),
                "time_limit_range": (900, 2700),
                "level_scaling": 1.2
            },
            QuestType.TIMED_CHALLENGE.name: {
                "amount_range": (5, 15),
                "time_limit_range": (120, 600),
                "level_scaling": 1.5
            },
            QuestType.CRAFT_ITEMS.name: {
                "amount_range": (1, 5),
                "time_limit_range": (1800, 7200),
                "level_scaling": 1.0
            },
            QuestType.DISCOVER_LOCATIONS.name: {
                "amount_range": (1, 3),
                "time_limit_range": (1800, 7200),
                "level_scaling": 1.0
            },
            QuestType.DEFEAT_BOSS.name: {
                "amount_range": (1, 1),
                "time_limit_range": (600, 1800),
                "level_scaling": 1.5
            },
            QuestType.SOLVE_PUZZLE.name: {
                "amount_range": (1, 3),
                "time_limit_range": (300, 1200),
                "level_scaling": 1.1
            },
            QuestType.TRADE_WITH_NPC.name: {
                "amount_range": (2, 8),
                "time_limit_range": (1800, 7200),
                "level_scaling": 1.0
            },
            QuestType.GATHER_RESOURCES.name: {
                "amount_range": (5, 20),
                "time_limit_range": (900, 3600),
                "level_scaling": 1.1
            },
            QuestType.TRAIN_SKILLS.name: {
                "amount_range": (1, 5),
                "time_limit_range": (1800, 7200),
                "level_scaling": 1.2
            }
        }

        # Player performance data
        self.player_performance: Dict[str, Dict[str, List[float]]] = {}

    def adjust_quest_difficulty(
        self,
        quest: 'Quest',
        player_level: int,
        target_difficulty: float
    ) -> None:
        """Adjust quest difficulty.

        Args:
            quest: Target quest
            player_level: Player level
            target_difficulty: Target difficulty (0.0-5.0)
        """
        quest_type = quest.type.name
        params = self.base_parameters.get(quest_type)
        if not params:
            return

        # Level scaling
        level_factor = math.pow(params["level_scaling"], player_level / 10)

        # Adjustment factor based on target difficulty
        difficulty_factor = target_difficulty / 2.5  # 2.5 is median value

        for objective in quest.objectives:
            self._adjust_objective_requirements(
                objective,
                quest_type,
                level_factor,
                difficulty_factor
            )

        # Adjust time limit
        if quest.time_limit:
            min_time, max_time = params["time_limit_range"]
            base_time = (min_time + max_time) / 2
            adjusted_time = int(base_time * level_factor * difficulty_factor)
            quest.time_limit = min(max_time, max(min_time, adjusted_time))

    def _adjust_objective_requirements(
        self,
        objective: 'QuestObjective',
        quest_type: str,
        level_factor: float,
        difficulty_factor: float
    ) -> None:
        """Adjust objective requirements.

        Args:
            objective: Target objective
            quest_type: Quest type
            level_factor: Level scaling factor
            difficulty_factor: Difficulty adjustment factor
        """
        params = self.base_parameters[quest_type]
        min_amount, max_amount = params["amount_range"]

        for condition in objective.conditions:
            # Calculate base amount
            base_amount = (min_amount + max_amount) / 2
            
            # Adjust based on performance data
            performance_factor = self._calculate_performance_factor(
                quest_type,
                condition.condition_type
            )

            # Calculate final required amount
            adjusted_amount = int(
                base_amount * level_factor * difficulty_factor * performance_factor
            )
            condition.required_amount = min(
                max_amount,
                max(min_amount, adjusted_amount)
            )

    def update_player_performance(
        self,
        quest_type: str,
        condition_type: str,
        completion_time: float,
        success: bool
    ) -> None:
        """Update player performance data.

        Args:
            quest_type: Quest type
            condition_type: Condition type
            completion_time: Completion time in seconds
            success: Whether successful
        """
        if quest_type not in self.player_performance:
            self.player_performance[quest_type] = {
                "completion_times": [],
                "success_rates": []
            }

        performance = self.player_performance[quest_type]
        performance["completion_times"].append(completion_time)
        performance["success_rates"].append(1.0 if success else 0.0)

        # Keep only the latest 100 records
        for key in performance:
            performance[key] = performance[key][-100:]

    def _calculate_performance_factor(
        self,
        quest_type: str,
        condition_type: str
    ) -> float:
        """Calculate adjustment factor based on player performance.

        Args:
            quest_type: Quest type
            condition_type: Condition type

        Returns:
            Adjustment factor (1.0 is baseline)
        """
        if quest_type not in self.player_performance:
            return 1.0

        performance = self.player_performance[quest_type]
        if not performance["success_rates"]:
            return 1.0

        # Adjust based on success rate
        avg_success_rate = statistics.mean(performance["success_rates"])
        if avg_success_rate > 0.8:
            # Increase difficulty if success rate is too high
            return 1.2
        elif avg_success_rate < 0.4:
            # Decrease difficulty if success rate is too low
            return 0.8

        return 1.0

    def analyze_quest_completion_data(
        self,
        quest_type: str
    ) -> Dict[str, Any]:
        """Analyze quest completion data.

        Args:
            quest_type: Quest type

        Returns:
            Dictionary containing analysis results
        """
        if quest_type not in self.player_performance:
            return {}

        performance = self.player_performance[quest_type]
        if not performance["completion_times"]:
            return {}

        return {
            "average_completion_time": statistics.mean(
                performance["completion_times"]
            ),
            "success_rate": statistics.mean(
                performance["success_rates"]
            ),
            "fastest_completion": min(performance["completion_times"]),
            "slowest_completion": max(performance["completion_times"]),
            "completion_time_variance": statistics.variance(
                performance["completion_times"]
            ) if len(performance["completion_times"]) > 1 else 0
        }

    def get_difficulty_adjustment_suggestions(
        self,
        quest: 'Quest',
        player_level: int
    ) -> List[str]:
        """Get difficulty adjustment suggestions.

        Args:
            quest: Target quest
            player_level: Player level

        Returns:
            List of suggestions
        """
        quest_type = quest.type.name
        if quest_type not in self.player_performance:
            return ["Not enough data for suggestions"]

        suggestions = []
        analysis = self.analyze_quest_completion_data(quest_type)

        # Suggestions based on success rate
        success_rate = analysis.get("success_rate", 0.0)
        if success_rate > 0.8:
            suggestions.append(
                "Quest might be too easy. Consider increasing required amounts or adding time limits."
            )
        elif success_rate < 0.4:
            suggestions.append(
                "Quest might be too difficult. Consider reducing required amounts or extending time limits."
            )

        # Suggestions based on completion time
        avg_time = analysis.get("average_completion_time", 0.0)
        if quest.time_limit:
            if avg_time > quest.time_limit * 0.9:
                suggestions.append(
                    "Time limit might be too strict. Consider extending it."
                )
            elif avg_time < quest.time_limit * 0.5:
                suggestions.append(
                    "Time limit might be too lenient. Consider reducing it."
                )

        return suggestions or ["Current difficulty seems appropriate"] 