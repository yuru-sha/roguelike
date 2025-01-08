from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional
from collections import deque

from roguelike.core.constants import GameStates

@dataclass
class Message:
    """A message to be displayed in the message log."""
    text: str
    color: Tuple[int, int, int]

class GameState:
    """Manages the current state of the game."""
    
    def __init__(self):
        """Initialize the game state."""
        self.state = GameStates.PLAYERS_TURN
        self.dungeon_level = 1
        self.messages: deque = deque(maxlen=100)
        self.wizard_mode = False
        self.wizard_password = "wizard"  # Simple password for demonstration
        
        # Targeting state
        self.targeting_item: Optional[int] = None
        self.targeting_callback = None
        self.targeting_message: Optional[str] = None
    
    def add_message(self, text: str, color: Tuple[int, int, int]) -> None:
        """
        Add a message to the message log.
        
        Args:
            text: The message text
            color: The color of the message
        """
        self.messages.append(Message(text, color))
    
    def enter_targeting_mode(self, item: int, callback: Any, message: Optional[str] = None) -> None:
        """
        Enter targeting mode.
        
        Args:
            item: The item being used
            callback: Function to call when targeting is complete
            message: Optional message to display during targeting
        """
        self.state = GameStates.TARGETING
        self.targeting_item = item
        self.targeting_callback = callback
        self.targeting_message = message
    
    def exit_targeting_mode(self) -> None:
        """Exit targeting mode."""
        self.state = GameStates.PLAYERS_TURN
        self.targeting_item = None
        self.targeting_callback = None
        self.targeting_message = None
    
    def toggle_wizard_mode(self, password: Optional[str] = None) -> bool:
        """
        Toggle wizard mode.
        
        Args:
            password: The password to enable wizard mode
            
        Returns:
            True if wizard mode was toggled successfully
        """
        if not self.wizard_mode and (password == self.wizard_password or password is None):
            self.wizard_mode = True
            return True
        elif self.wizard_mode:
            self.wizard_mode = False
            return True
        return False
    
    def save_game(self) -> Dict[str, Any]:
        """
        Save the current game state.
        
        Returns:
            Dictionary containing the game state
        """
        return {
            'state': self.state,
            'dungeon_level': self.dungeon_level,
            'messages': [(m.text, m.color) for m in self.messages],
            'wizard_mode': self.wizard_mode
        }
    
    @classmethod
    def load_game(cls, data: Dict[str, Any]) -> 'GameState':
        """
        Load a saved game state.
        
        Args:
            data: Dictionary containing the game state
            
        Returns:
            A new GameState instance with the loaded data
        """
        state = cls()
        state.state = data['state']
        state.dungeon_level = data['dungeon_level']
        state.messages = deque(
            [Message(text, color) for text, color in data['messages']],
            maxlen=100
        )
        state.wizard_mode = data['wizard_mode']
        return state 