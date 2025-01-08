from typing import Optional, Dict, Any, Callable
import tcod
from tcod.event import Event, KeyDown, MouseButtonDown

from roguelike.core.constants import GameStates
from roguelike.utils.logging import GameLogger

logger = GameLogger.get_instance()

class InputHandler:
    """
    Handles keyboard and mouse input for the game.
    """
    
    def __init__(self):
        """Initialize the input handler."""
        self.key_actions: Dict[int, str] = {
            # Movement
            tcod.event.K_UP: 'move_north',
            tcod.event.K_DOWN: 'move_south',
            tcod.event.K_LEFT: 'move_west',
            tcod.event.K_RIGHT: 'move_east',
            tcod.event.K_k: 'move_north',
            tcod.event.K_j: 'move_south',
            tcod.event.K_h: 'move_west',
            tcod.event.K_l: 'move_east',
            tcod.event.K_y: 'move_northwest',
            tcod.event.K_u: 'move_northeast',
            tcod.event.K_b: 'move_southwest',
            tcod.event.K_n: 'move_southeast',
            
            # Actions
            tcod.event.K_g: 'pickup',
            tcod.event.K_i: 'show_inventory',
            tcod.event.K_d: 'drop_inventory',
            tcod.event.K_c: 'show_character_screen',
            tcod.event.K_GREATER: 'take_stairs',
            tcod.event.K_ESCAPE: 'exit',
            tcod.event.K_RETURN: 'enter',
            
            # Wizard mode
            tcod.event.K_w: 'wizard_mode'
        }
    
    def handle_input(self, event: Event, game_state: GameStates) -> Optional[Dict[str, Any]]:
        """
        Handle input events based on the current game state.
        
        Args:
            event: The input event
            game_state: The current game state
            
        Returns:
            A dictionary containing the action and its parameters, or None
        """
        if isinstance(event, KeyDown):
            return self._handle_key(event, game_state)
        elif isinstance(event, MouseButtonDown):
            return self._handle_mouse(event, game_state)
        
        return None
    
    def _handle_key(self, event: KeyDown, game_state: GameStates) -> Optional[Dict[str, Any]]:
        """
        Handle keyboard input.
        
        Args:
            event: The keyboard event
            game_state: The current game state
            
        Returns:
            A dictionary containing the action and its parameters, or None
        """
        key = event.sym
        
        if game_state == GameStates.PLAYERS_TURN:
            return self._handle_player_turn_keys(key)
        elif game_state == GameStates.PLAYER_DEAD:
            return self._handle_player_dead_keys(key)
        elif game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
            return self._handle_inventory_keys(key)
        elif game_state == GameStates.TARGETING:
            return self._handle_targeting_keys(key)
        elif game_state == GameStates.LEVEL_UP:
            return self._handle_level_up_keys(key)
        elif game_state == GameStates.CHARACTER_SCREEN:
            return self._handle_character_screen_keys(key)
            
        return None
    
    def _handle_player_turn_keys(self, key: int) -> Optional[Dict[str, Any]]:
        """Handle keys during the player's turn."""
        action = self.key_actions.get(key)
        
        if action:
            logger.debug(f"Player action: {action}")
            return {'action': action}
            
        return None
    
    def _handle_player_dead_keys(self, key: int) -> Optional[Dict[str, Any]]:
        """Handle keys when the player is dead."""
        if key == tcod.event.K_i:
            return {'action': 'show_inventory'}
        elif key == tcod.event.K_ESCAPE:
            return {'action': 'exit'}
            
        return None
    
    def _handle_inventory_keys(self, key: int) -> Optional[Dict[str, Any]]:
        """Handle keys in inventory screens."""
        index = key - tcod.event.K_a
        
        if 0 <= index <= 26:
            return {'action': 'inventory_index', 'inventory_index': index}
            
        if key == tcod.event.K_ESCAPE:
            return {'action': 'exit'}
            
        return None
    
    def _handle_targeting_keys(self, key: int) -> Optional[Dict[str, Any]]:
        """Handle keys during targeting mode."""
        if key == tcod.event.K_ESCAPE:
            return {'action': 'exit'}
            
        return None
    
    def _handle_level_up_keys(self, key: int) -> Optional[Dict[str, Any]]:
        """Handle keys during level up screen."""
        if key == tcod.event.K_a:
            return {'action': 'level_up', 'choice': 'hp'}
        elif key == tcod.event.K_b:
            return {'action': 'level_up', 'choice': 'str'}
        elif key == tcod.event.K_c:
            return {'action': 'level_up', 'choice': 'def'}
            
        return None
    
    def _handle_character_screen_keys(self, key: int) -> Optional[Dict[str, Any]]:
        """Handle keys in character screen."""
        if key == tcod.event.K_ESCAPE:
            return {'action': 'exit'}
            
        return None
    
    def _handle_mouse(self, event: MouseButtonDown, game_state: GameStates) -> Optional[Dict[str, Any]]:
        """
        Handle mouse input.
        
        Args:
            event: The mouse event
            game_state: The current game state
            
        Returns:
            A dictionary containing the action and its parameters, or None
        """
        if game_state == GameStates.TARGETING:
            if event.button == tcod.event.BUTTON_LEFT:
                return {
                    'action': 'left_click',
                    'position': (event.tile.x, event.tile.y)
                }
            elif event.button == tcod.event.BUTTON_RIGHT:
                return {'action': 'right_click'}
                
        return None 