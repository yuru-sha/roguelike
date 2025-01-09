"""
Quest generation system implementation.
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from roguelike.game.quests import (
    Quest,
    QuestType,
    QuestObjective,
    QuestCondition,
    QuestReward
)


@dataclass
class QuestTemplate:
    """Template for generating quests."""
    template_id: str
    quest_type: QuestType
    name_patterns: List[str]  # e.g. "Slay {target_name}"
    description_patterns: List[str]  # e.g. "{target_name} is terrorizing {location_name}. Restore peace by defeating it."
    objective_patterns: List[str]  # e.g. "Slay {target_name}"
    condition_type: str
    target_types: List[str]  # Types of enemies or items to target
    base_required_amount: Tuple[int, int]  # (min, max)
    base_rewards: Dict[str, Tuple[int, int]]  # Base reward ranges (gold, exp, etc.)
    level_range: Tuple[int, int]  # Recommended level range
    time_limit_range: Optional[Tuple[int, int]] = None  # Time limit range (minutes)
    chain_probability: float = 0.0  # Probability of this quest being part of a chain


class QuestDifficultyManager:
    """Manages quest difficulty scaling."""

    def __init__(self):
        self.difficulty_multipliers = {
            "trivial": 0.5,
            "easy": 0.75,
            "normal": 1.0,
            "hard": 1.5,
            "epic": 2.0,
            "legendary": 3.0
        }

    def calculate_difficulty(
        self,
        player_level: int,
        quest_level: int
    ) -> str:
        """Calculate quest difficulty based on level difference.
        
        Args:
            player_level: Current player level
            quest_level: Quest recommended level
            
        Returns:
            Difficulty rating as string
        """
        level_diff = player_level - quest_level
        
        if level_diff >= 5:
            return "trivial"
        elif level_diff >= 3:
            return "easy"
        elif level_diff >= -2:
            return "normal"
        elif level_diff >= -4:
            return "hard"
        elif level_diff >= -6:
            return "epic"
        else:
            return "legendary"

    def adjust_rewards(
        self,
        base_rewards: Dict[str, int],
        difficulty: str
    ) -> Dict[str, int]:
        """Adjust rewards based on difficulty.
        
        Args:
            base_rewards: Base reward values
            difficulty: Difficulty rating
            
        Returns:
            Adjusted reward values
        """
        multiplier = self.difficulty_multipliers.get(difficulty, 1.0)
        return {
            key: int(value * multiplier)
            for key, value in base_rewards.items()
        }

    def adjust_requirements(
        self,
        base_amount: int,
        difficulty: str
    ) -> int:
        """Adjust required amounts based on difficulty.
        
        Args:
            base_amount: Base required amount
            difficulty: Difficulty rating
            
        Returns:
            Adjusted required amount
        """
        multiplier = self.difficulty_multipliers.get(difficulty, 1.0)
        return max(1, int(base_amount * multiplier))


class QuestGenerator:
    """Generates quests from templates."""

    def __init__(self):
        self.templates: Dict[str, QuestTemplate] = {}
        self.difficulty_manager = QuestDifficultyManager()
        self._initialize_templates()

    def _initialize_templates(self) -> None:
        """Initialize quest templates."""
        # 敵討伐クエスト
        self.templates["kill_enemies"] = QuestTemplate(
            template_id="kill_enemies",
            quest_type=QuestType.KILL_ENEMIES,
            name_patterns=[
                "Hunt {target_name}",
                "Exterminate {target_name}",
                "Threat of {target_name}"
            ],
            description_patterns=[
                "{target_name} have appeared in {location_name}, threatening the villagers. Eliminate them to restore peace.",
                "A pack of {target_name} has emerged in {location_name}. Deal with them before more damage is done.", 
                "{location_name} is occupied by {target_name}. Clear them out."
            ],
            objective_patterns=[
                "Slay {target_name}",
                "Hunt down {target_name}", 
                "Eliminate {target_name}"
            ],
            condition_type="kill",
            target_types=["goblin", "orc", "undead", "beast", "demon"],
            base_required_amount=(3, 10),
            base_rewards={
                "gold": (50, 200),
                "experience": (100, 400)
            },
            level_range=(1, 20)
        )

        # アイテム収集クエスト
        self.templates["collect_items"] = QuestTemplate(
            template_id="collect_items",
            quest_type=QuestType.COLLECT_ITEMS,
            name_patterns=[
                "Gather {target_name}",
                "Search for {target_name}",
                "Lost {target_name}"
            ],
            description_patterns=[
                "Find {target_name} in {location_name}. It may hold vital clues.",
                "An alchemist requires {target_name}. You should find them in {location_name}.",
                "{target_name} lies somewhere in {location_name}. Retrieve it."
            ],
            objective_patterns=[
                "Gather {target_name}",
                "Find {target_name}",
                "Retrieve {target_name}"
            ],
            condition_type="collect",
            target_types=["herb", "mineral", "artifact", "treasure", "reagent"],
            base_required_amount=(1, 5),
            base_rewards={
                "gold": (100, 300),
                "experience": (150, 450)
            },
            level_range=(1, 15)
        )

        # ボス討伐クエスト
        self.templates["defeat_boss"] = QuestTemplate(
            template_id="defeat_boss",
            quest_type=QuestType.DEFEAT_BOSS,
            name_patterns=[
                "Final Battle with {target_name}",
                "Hunt {target_name}",
                "Challenge {target_name}"
            ],
            description_patterns=[
                "A mighty {target_name} has appeared in {location_name}. You are our only hope.",
                "{target_name} has become the tyrant of {location_name}. End their reign.",
                "The {target_name} lurking in {location_name} threatens the world."
            ],
            objective_patterns=[
                "Slay {target_name}",
                "Hunt down {target_name}",
                "Defeat {target_name}"
            ],
            condition_type="kill",
            target_types=["dragon", "demon_lord", "ancient_being", "corrupted_hero"],
            base_required_amount=(1, 1),
            base_rewards={
                "gold": (1000, 5000),
                "experience": (2000, 10000),
                "skill_points": (1, 3)
            },
            level_range=(10, 50),
            chain_probability=0.8
        )

    def generate_quest(
        self,
        template_id: str,
        player_level: int,
        location_data: Optional[Dict[str, str]] = None
    ) -> Quest:
        """Generate a quest from a template.
        
        Args:
            template_id: ID of the template to use
            player_level: Current player level
            location_data: Optional location-specific data
            
        Returns:
            Generated quest
        """
        template = self.templates[template_id]
        
        # 基本パラメータの決定
        quest_level = random.randint(*template.level_range)
        difficulty = self.difficulty_manager.calculate_difficulty(player_level, quest_level)
        
        # ターゲットの選択
        target_type = random.choice(template.target_types)
        target_data = self._get_target_data(target_type, difficulty)
        
        # 必要数の決定
        base_amount = random.randint(*template.base_required_amount)
        required_amount = self.difficulty_manager.adjust_requirements(base_amount, difficulty)
        
        # 報酬の決定
        base_rewards = {
            key: random.randint(*value)
            for key, value in template.base_rewards.items()
        }
        rewards = self.difficulty_manager.adjust_rewards(base_rewards, difficulty)
        
        # テキストの生成
        format_data = {
            "target_name": target_data["name"],
            "location_name": location_data["name"] if location_data else "Unknown Location",
            "amount": required_amount
        }
        
        name = random.choice(template.name_patterns).format(**format_data)
        description = random.choice(template.description_patterns).format(**format_data)
        objective_text = random.choice(template.objective_patterns).format(**format_data)
        
        # クエストの生成
        quest_id = f"{template_id}_{random.randint(1000, 9999)}"
        
        return Quest(
            quest_id=quest_id,
            type=template.quest_type,
            name=name,
            description=description,
            objectives=[
                QuestObjective(
                    description=objective_text,
                    conditions=[
                        QuestCondition(
                            condition_type=template.condition_type,
                            target_type=target_type,
                            target_id=target_data.get("id"),
                            required_amount=required_amount
                        )
                    ]
                )
            ],
            reward=QuestReward(
                gold=rewards.get("gold", 0),
                experience=rewards.get("experience", 0),
                skill_points=rewards.get("skill_points", 0),
                items=target_data.get("reward_items", [])
            ),
            level_requirement=quest_level,
            time_limit=random.randint(*template.time_limit_range) if template.time_limit_range else None
        )

    def _get_target_data(
        self,
        target_type: str,
        difficulty: str
    ) -> Dict[str, str]:
        """Get target-specific data based on type and difficulty.
        
        Args:
            target_type: Type of target
            difficulty: Difficulty rating
            
        Returns:
            Target data including name, ID, and possible rewards
        """
        return {
            "id": f"{target_type}_{difficulty}",
            "name": f"{difficulty.title()} {target_type.replace('_', ' ').title()}",
            "reward_items": []  # Should be populated from game data
        }

    def generate_quest_chain(
        self,
        base_template_id: str,
        player_level: int,
        chain_length: int = 3
    ) -> List[Quest]:
        """Generate a chain of related quests.
        
        Args:
            base_template_id: ID of the template to base the chain on
            player_level: Current player level
            chain_length: Number of quests in the chain
            
        Returns:
            List of generated quests
        """
        quests = []
        base_template = self.templates[base_template_id]
        
        # Chain base settings
        chain_target_type = random.choice(base_template.target_types)
        chain_location = {"name": "Chain-specific Location"}  # Should be fetched from game data
        
        for i in range(chain_length):
            # Gradually increase difficulty for each quest
            level_increase = i * 2
            adjusted_player_level = player_level - level_increase
            
            quest = self.generate_quest(
                base_template_id,
                adjusted_player_level,
                chain_location
            )
            
            # Adjust quest for chain context
            if i > 0:
                quest.prerequisites = [quests[-1].quest_id]
            
            quests.append(quest)
        
        return quests 