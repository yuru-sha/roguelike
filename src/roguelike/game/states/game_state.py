"""
Game state management.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

from roguelike.world.entity.components.serializable import \
    SerializableComponent


class GameStates(Enum):
    """Game state enumeration."""

    PLAYERS_TURN = auto()
    ENEMY_TURN = auto()
    PLAYER_DEAD = auto()
    SHOW_INVENTORY = auto()
    DROP_INVENTORY = auto()
    TARGETING = auto()
    LEVEL_UP = auto()
    CHARACTER_SCREEN = auto()
    SAVE_GAME = auto()
    LOAD_GAME = auto()
    ACHIEVEMENTS = auto()


@dataclass
class Message:
    """Game message with color."""

    text: str
    color: Tuple[int, int, int]


T = TypeVar("T", bound="GameState")


@dataclass
class GameState(SerializableComponent):
    """
    Represents the current state of the game.
    """

    dungeon_level: int = 1
    player_has_amulet: bool = False
    game_messages: List[Message] = None
    previous_player_positions: Dict[int, Tuple[int, int]] = None
    game_won: bool = False
    state: GameStates = GameStates.PLAYERS_TURN
    targeting_item: Optional[int] = None
    wizard_mode: bool = False
    auto_save_interval: int = 50  # Number of turns between auto-saves
    dungeon: Any = None  # Current dungeon map

    def __post_init__(self):
        if self.game_messages is None:
            self.game_messages = []
        if self.previous_player_positions is None:
            self.previous_player_positions = {}

    def add_message(
        self, text: str, color: Tuple[int, int, int] = (255, 255, 255)
    ) -> None:
        """Add a message to the message log."""
        self.game_messages.append(Message(text, color))

    def clear_messages(self) -> None:
        """Clear all messages."""
        self.game_messages.clear()

    def save_player_position(self, level: int, position: Tuple[int, int]) -> None:
        """Save player's position for a specific dungeon level."""
        self.previous_player_positions[level] = position

    def get_player_position(self, level: int) -> Optional[Tuple[int, int]]:
        """Get player's previous position for a specific dungeon level."""
        return self.previous_player_positions.get(level)

    def check_victory_condition(self) -> bool:
        """
        Check if the player has won the game.
        Victory is achieved by obtaining the Amulet of Yendor and returning to level 1.
        """
        if self.player_has_amulet and self.dungeon_level == 1:
            self.game_won = True
            self.add_message(
                "You have escaped the dungeon with the Amulet of Yendor! You win!",
                (255, 255, 0),
            )
            return True
        return False

    def enter_targeting_mode(self, item: int) -> None:
        """
        Enter targeting mode.

        Args:
            item: The item entity being used
        """
        self.state = GameStates.TARGETING
        self.targeting_item = item

    def exit_targeting_mode(self) -> None:
        """Exit targeting mode."""
        self.state = GameStates.PLAYERS_TURN
        self.targeting_item = None

    def next_level(self) -> None:
        """Advance to the next dungeon level."""
        self.dungeon_level += 1
        self.add_message(
            f"You descend deeper into the dungeon... (Level {self.dungeon_level})"
        )

    def toggle_wizard_mode(self, password: str) -> bool:
        """
        Toggle wizard mode with password.

        Args:
            password: The wizard mode password

        Returns:
            True if wizard mode was toggled
        """
        from roguelike.core.constants import WIZARD_MODE_PASSWORD

        if password != WIZARD_MODE_PASSWORD:
            return False

        self.wizard_mode = not self.wizard_mode
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert game state to dictionary."""
        return {
            "dungeon_level": self.dungeon_level,
            "player_has_amulet": self.player_has_amulet,
            "game_messages": [
                {"text": msg.text, "color": msg.color} for msg in self.game_messages
            ],
            "previous_player_positions": {
                str(k): v for k, v in self.previous_player_positions.items()
            },
            "game_won": self.game_won,
            "state": self.state.name,
            "targeting_item": self.targeting_item,
            "wizard_mode": self.wizard_mode,
            "auto_save_interval": self.auto_save_interval,
        }

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create game state from dictionary."""
        messages = [
            Message(text=msg["text"], color=tuple(msg["color"]))
            for msg in data["game_messages"]
        ]

        previous_positions = {
            int(k): tuple(v) for k, v in data["previous_player_positions"].items()
        }

        return cls(
            dungeon_level=data["dungeon_level"],
            player_has_amulet=data["player_has_amulet"],
            game_messages=messages,
            previous_player_positions=previous_positions,
            game_won=data["game_won"],
            state=GameStates[data["state"]],
            targeting_item=data["targeting_item"],
            wizard_mode=data["wizard_mode"],
            auto_save_interval=data.get("auto_save_interval", 50),  # Default to 50 if not present
        )

    def change_level(self, new_level: int) -> None:
        """
        Change to a specific dungeon level.

        Args:
            new_level: The dungeon level to change to
        """
        old_level = self.dungeon_level
        self.dungeon_level = new_level
        if new_level > old_level:
            self.add_message(
                f"You descend deeper into the dungeon... (Level {self.dungeon_level})"
            )
        else:
            self.add_message(
                f"You ascend to an earlier level... (Level {self.dungeon_level})"
            )
