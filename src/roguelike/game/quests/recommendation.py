"""
Implementation of quest recommendation system.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
import math
import random

from roguelike.game.quests.types import QuestType
from roguelike.game.quests.statistics import QuestStatisticsManager
from roguelike.game.quests.balancer import QuestBalancer

if TYPE_CHECKING:
    from roguelike.game.quests.quests import Quest


@dataclass
class QuestScore:
    """Class representing quest scores."""

    quest_id: str
    base_score: float
    level_factor: float
    style_factor: float
    completion_factor: float
    difficulty_factor: float
    final_score: float


class QuestRecommender:
    """Quest recommendation system."""

    def __init__(self):
        """Initialize quest recommendation system."""
        self.stats_manager = QuestStatisticsManager()
        self.quest_balancer = QuestBalancer()
        self.style_weights = {
            "combat": 0.0,
            "exploration": 0.0,
            "collection": 0.0,
            "story": 0.0,
            "challenge": 0.0
        }
        self.last_recommendations: List[str] = []

    def update_style_weights(self, quest_history: List['Quest']) -> None:
        """Update playstyle weights.

        Args:
            quest_history: History of completed quests
        """
        total_quests = len(quest_history)
        if total_quests == 0:
            return

        # Count completed quests by type
        type_counts = {
            "combat": 0,
            "exploration": 0,
            "collection": 0,
            "story": 0,
            "challenge": 0
        }

        for quest in quest_history:
            if quest.type in [QuestType.KILL_ENEMIES, QuestType.COMBAT_MASTER]:
                type_counts["combat"] += 1
            elif quest.type in [QuestType.EXPLORE_LEVELS, QuestType.DISCOVER_LOCATIONS]:
                type_counts["exploration"] += 1
            elif quest.type in [QuestType.COLLECT_ITEMS, QuestType.TREASURE_HUNTER]:
                type_counts["collection"] += 1
            elif quest.type in [QuestType.ESCORT_NPC, QuestType.SOLVE_PUZZLE]:
                type_counts["story"] += 1
            elif quest.type in [QuestType.TIME_ATTACK, QuestType.NO_DAMAGE]:
                type_counts["challenge"] += 1

        # Update weights
        for style in self.style_weights:
            count = type_counts[style]
            self.style_weights[style] = count / total_quests

    def calculate_quest_score(
        self,
        quest: 'Quest',
        player_level: int,
        player_stats: Dict[str, Any]
    ) -> QuestScore:
        """Calculate quest score.

        Args:
            quest: Quest to evaluate
            player_level: Player level
            player_stats: Player statistics

        Returns:
            Quest score
        """
        # Base score based on quest reward and difficulty
        base_score = quest.reward.points * 0.5

        # Level factor based on player level and quest level requirement
        level_diff = abs(player_level - quest.level_requirement)
        level_factor = 1.0 / (1.0 + level_diff * 0.2)

        # Playstyle factor
        style_factor = self._calculate_style_factor(quest)

        # Completion factor based on completion history of similar quests
        completion_factor = self._calculate_completion_factor(
            quest.type,
            player_stats
        )

        # Difficulty factor based on player ability and quest difficulty
        difficulty_factor = self._calculate_difficulty_factor(
            quest,
            player_stats
        )

        # Final score calculation
        final_score = (
            base_score *
            level_factor *
            style_factor *
            completion_factor *
            difficulty_factor
        )

        return QuestScore(
            quest_id=quest.quest_id,
            base_score=base_score,
            level_factor=level_factor,
            style_factor=style_factor,
            completion_factor=completion_factor,
            difficulty_factor=difficulty_factor,
            final_score=final_score
        )

    def _calculate_style_factor(self, quest: 'Quest') -> float:
        """Calculate playstyle factor.

        Args:
            quest: Quest to evaluate

        Returns:
            Playstyle factor (0.0-2.0)
        """
        quest_style = self._get_quest_style(quest.type)
        if not quest_style:
            return 1.0

        style_weight = self.style_weights[quest_style]
        return 1.0 + style_weight

    def _calculate_completion_factor(
        self,
        quest_type: QuestType,
        player_stats: Dict[str, Any]
    ) -> float:
        """Calculate completion factor.

        Args:
            quest_type: Quest type
            player_stats: Player statistics

        Returns:
            Completion factor (0.5-1.5)
        """
        type_stats = player_stats.get("quest_type_stats", {}).get(quest_type.name, {})
        success_rate = type_stats.get("success_rate", 0.0)

        if success_rate > 0.8:
            # If high success rate, recommend harder quests
            return 0.5
        elif success_rate < 0.3:
            # If low success rate, recommend similar quests
            return 1.5
        else:
            # If medium success rate, balance the difficulty
            return 1.0

    def _calculate_difficulty_factor(
        self,
        quest: 'Quest',
        player_stats: Dict[str, Any]
    ) -> float:
        """Calculate difficulty factor.

        Args:
            quest: Quest to evaluate
            player_stats: Player statistics

        Returns:
            Difficulty factor (0.5-1.5)
        """
        quest_difficulty = self.quest_balancer.calculate_quest_difficulty(
            quest.type.name,
            player_stats.get("level", 1),
            len(quest.objectives)
        )

        # Recommend appropriate difficulty based on player skill
        player_skill = player_stats.get("average_completion_rate", 0.5)
        target_difficulty = 3.0 - (player_skill * 2.0)  # 0.5-2.5 range

        diff = abs(quest_difficulty - target_difficulty)
        return 1.5 - (diff * 0.2)  # Higher difference results in lower score

    def _get_quest_style(self, quest_type: QuestType) -> Optional[str]:
        """Get quest style from quest type.

        Args:
            quest_type: Quest type

        Returns:
            Quest style
        """
        style_mapping = {
            QuestType.KILL_ENEMIES: "combat",
            QuestType.COMBAT_MASTER: "combat",
            QuestType.EXPLORE_LEVELS: "exploration",
            QuestType.DISCOVER_LOCATIONS: "exploration",
            QuestType.COLLECT_ITEMS: "collection",
            QuestType.TREASURE_HUNTER: "collection",
            QuestType.ESCORT_NPC: "story",
            QuestType.SOLVE_PUZZLE: "story",
            QuestType.TIME_ATTACK: "challenge",
            QuestType.NO_DAMAGE: "challenge"
        }
        return style_mapping.get(quest_type)

    def get_quest_recommendations(
        self,
        available_quests: List['Quest'],
        player_level: int,
        count: int = 3,
        exclude_recent: bool = True
    ) -> List[Tuple['Quest', QuestScore]]:
        """Get quest recommendations.

        Args:
            available_quests: Available quests
            player_level: Player level
            count: Number of recommendations
            exclude_recent: Whether to exclude recently recommended quests

        Returns:
            List of recommended quests and scores
        """
        if not available_quests:
            return []

        # Get player statistics
        player_stats = self.stats_manager.get_overall_statistics()

        # Calculate scores for each quest
        quest_scores: List[Tuple['Quest', QuestScore]] = []
        for quest in available_quests:
            if exclude_recent and quest.quest_id in self.last_recommendations:
                continue

            score = self.calculate_quest_score(
                quest,
                player_level,
                player_stats
            )
            quest_scores.append((quest, score))

        # Sort by score
        quest_scores.sort(key=lambda x: x[1].final_score, reverse=True)

        # Update recommended list
        self.last_recommendations = [
            quest.quest_id for quest, _ in quest_scores[:count]
        ]

        return quest_scores[:count]

    def get_quest_chain_recommendations(
        self,
        available_chains: List[Tuple[str, List['Quest']]],
        player_level: int,
        count: int = 2
    ) -> List[Tuple[str, List['Quest'], float]]:
        """Get quest chain recommendations.

        Args:
            available_chains: Available quest chains
            player_level: Player level
            count: Number of recommendations

        Returns:
            List of recommended chains and scores
        """
        if not available_chains:
            return []

        # Get player statistics
        player_stats = self.stats_manager.get_overall_statistics()

        # Calculate scores for each chain
        chain_scores: List[Tuple[str, List['Quest'], float]] = []
        for chain_id, quests in available_chains:
            # Calculate scores for each quest in the chain
            quest_scores = [
                self.calculate_quest_score(
                    quest,
                    player_level,
                    player_stats
                ).final_score
                for quest in quests
            ]

            # Calculate chain score
            chain_score = (
                sum(quest_scores) / len(quest_scores) *
                (1.0 + (len(quests) * 0.1))  # Bonus for longer chains
            )

            chain_scores.append((chain_id, quests, chain_score))

        # Sort by score
        chain_scores.sort(key=lambda x: x[2], reverse=True)
        return chain_scores[:count]

    def get_daily_recommendations(
        self,
        available_quests: List['Quest'],
        player_level: int,
        count: int = 3
    ) -> List[Tuple['Quest', str]]:
        """Get daily quest recommendations.

        Args:
            available_quests: Available quests
            player_level: Player level
            count: Number of recommendations

        Returns:
            List of recommended quests and reasons
        """
        recommendations = self.get_quest_recommendations(
            available_quests,
            player_level,
            count * 2  # Select more candidates
        )

        # Randomly select and add reasons
        selected = random.sample(recommendations, min(count, len(recommendations)))
        result = []

        for quest, score in selected:
            reason = self._get_recommendation_reason(quest, score)
            result.append((quest, reason))

        return result

    def _get_recommendation_reason(
        self,
        quest: 'Quest',
        score: QuestScore
    ) -> str:
        """Generate quest recommendation reason.

        Args:
            quest: Recommended quest
            score: Quest score

        Returns:
            Recommendation reason
        """
        reasons = []

        if score.level_factor > 0.8:
            reasons.append("Suitable for your level")
        if score.style_factor > 1.5:
            reasons.append("Matches your playstyle")
        if score.completion_factor > 1.2:
            reasons.append("You have succeeded at this before")
        if score.difficulty_factor > 1.2:
            reasons.append("Appropriate challenge")

        if not reasons:
            reasons.append("A balanced challenge")

        return ", ".join(reasons) 

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