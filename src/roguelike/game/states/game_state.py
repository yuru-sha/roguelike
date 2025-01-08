from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum, auto

class GameStates(Enum):
    """Game state enumeration."""
    PLAYERS_TURN = auto()
    ENEMY_TURN = auto()
    PLAYER_DEAD = auto()
    SHOW_INVENTORY = auto()
    DROP_INVENTORY = auto()
    LEVEL_UP = auto()

@dataclass
class GameState:
    """
    Represents the current state of the game.
    """
    dungeon_level: int = 1
    player_has_amulet: bool = False
    game_messages: List[Tuple[str, Tuple[int, int, int]]] = None
    previous_player_positions: Dict[int, Tuple[int, int]] = None
    game_won: bool = False
    state: GameStates = GameStates.PLAYERS_TURN
    
    def __post_init__(self):
        if self.game_messages is None:
            self.game_messages = []
        if self.previous_player_positions is None:
            self.previous_player_positions = {}
    
    def add_message(self, text: str, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        """Add a message to the message log."""
        self.game_messages.append((text, color))
    
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
                (255, 255, 0)
            )
            return True
        return False 