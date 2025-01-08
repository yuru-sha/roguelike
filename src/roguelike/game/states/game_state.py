"""
Game state management.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, Type, TypeVar
from enum import Enum, auto

from roguelike.world.entity.components.serializable import SerializableComponent

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

@dataclass
class Message:
    """Game message with color."""
    text: str
    color: Tuple[int, int, int]

T = TypeVar('T', bound='GameState')

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
    
    def __post_init__(self):
        if self.game_messages is None:
            self.game_messages = []
        if self.previous_player_positions is None:
            self.previous_player_positions = {}
    
    def add_message(self, text: str, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
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
                (255, 255, 0)
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
        self.add_message(f"You descend deeper into the dungeon... (Level {self.dungeon_level})")
    
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
        """Override to handle Message objects and GameStates enum."""
        data = super().to_dict()
        
        # Convert Message objects to dictionaries
        messages = []
        for msg in self.game_messages:
            messages.append({
                'text': msg.text,
                'color': msg.color
            })
        data['data']['game_messages'] = messages
        
        # Convert GameStates enum to string
        data['data']['state'] = self.state.name
        
        return data
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Override to handle Message objects and GameStates enum."""
        # Convert message dictionaries back to Message objects
        messages = []
        for msg_data in data['data']['game_messages']:
            messages.append(Message(
                text=msg_data['text'],
                color=tuple(msg_data['color'])
            ))
        data['data']['game_messages'] = messages
        
        # Convert state string back to enum
        data['data']['state'] = GameStates[data['data']['state']]
        
        return super().from_dict(data) 