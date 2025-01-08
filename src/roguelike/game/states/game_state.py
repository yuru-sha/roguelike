from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import esper

from roguelike.core.constants import GameStates
from roguelike.utils.logging import GameLogger

logger = GameLogger.get_instance()

@dataclass
class Message:
    """A message to be displayed in the message log."""
    text: str
    color: tuple[int, int, int]

@dataclass
class GameState:
    """
    Represents the current state of the game.
    """
    state: GameStates = GameStates.PLAYERS_TURN
    dungeon_level: int = 1
    game_messages: List[Message] = field(default_factory=list)
    targeting_item: Optional[int] = None
    wizard_mode: bool = False
    
    def __post_init__(self) -> None:
        """Initialize the game state."""
        logger.info("Initializing game state")
        logger.debug(f"Initial state: {self.state}")
        logger.debug(f"Dungeon level: {self.dungeon_level}")
        logger.debug(f"Wizard mode: {self.wizard_mode}")
    
    def add_message(self, text: str, color: tuple[int, int, int]) -> None:
        """
        Add a message to the game message log.
        
        Args:
            text: The message text
            color: The message color (RGB tuple)
        """
        self.game_messages.append(Message(text=text, color=color))
        logger.debug(f"Added message: {text}")
    
    def enter_targeting_mode(self, item: int) -> None:
        """
        Enter targeting mode for using an item.
        
        Args:
            item: The item entity ID
        """
        self.state = GameStates.TARGETING
        self.targeting_item = item
        logger.debug(f"Entered targeting mode for item {item}")
    
    def exit_targeting_mode(self) -> None:
        """Exit targeting mode."""
        self.state = GameStates.PLAYERS_TURN
        self.targeting_item = None
        logger.debug("Exited targeting mode")
    
    def next_level(self) -> None:
        """Advance to the next dungeon level."""
        self.dungeon_level += 1
        logger.info(f"Advanced to dungeon level {self.dungeon_level}")
    
    def toggle_wizard_mode(self, password: str) -> bool:
        """
        Toggle wizard mode if the correct password is provided.
        
        Args:
            password: The wizard mode password
            
        Returns:
            True if wizard mode was toggled successfully
        """
        from roguelike.core.constants import WIZARD_MODE_PASSWORD
        
        if password == WIZARD_MODE_PASSWORD:
            self.wizard_mode = not self.wizard_mode
            logger.info(f"Wizard mode {'enabled' if self.wizard_mode else 'disabled'}")
            return True
        
        logger.warning("Invalid wizard mode password attempt")
        return False
    
    def save_game(self) -> Dict[str, Any]:
        """
        Create a dictionary representation of the game state for saving.
        
        Returns:
            Dictionary containing the game state
        """
        return {
            'state': self.state.name,
            'dungeon_level': self.dungeon_level,
            'game_messages': [
                {'text': msg.text, 'color': msg.color}
                for msg in self.game_messages[-50:]  # Only save last 50 messages
            ],
            'wizard_mode': self.wizard_mode
        }
    
    @classmethod
    def load_game(cls, data: Dict[str, Any]) -> 'GameState':
        """
        Create a GameState instance from saved data.
        
        Args:
            data: Dictionary containing the game state data
            
        Returns:
            A new GameState instance
        """
        state = cls(
            state=GameStates[data['state']],
            dungeon_level=data['dungeon_level'],
            wizard_mode=data.get('wizard_mode', False)
        )
        
        # Restore messages
        for msg_data in data.get('game_messages', []):
            state.add_message(msg_data['text'], tuple(msg_data['color']))
        
        logger.info("Loaded game state")
        return state 