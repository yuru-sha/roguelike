"""
Handle keyboard and mouse input.
"""

from typing import Optional, Dict, Any
import tcod.event

from roguelike.game.states.game_state import GameStates

class InputHandler:
    """Handle keyboard and mouse input."""
    
    def __init__(self):
        """Initialize input handler."""
        self.key_actions = {
            # Movement keys
            tcod.event.K_UP: {'action': 'move', 'dy': -1},
            tcod.event.K_DOWN: {'action': 'move', 'dy': 1},
            tcod.event.K_LEFT: {'action': 'move', 'dx': -1},
            tcod.event.K_RIGHT: {'action': 'move', 'dx': 1},
            # Vi keys
            tcod.event.K_k: {'action': 'move', 'dy': -1},
            tcod.event.K_j: {'action': 'move', 'dy': 1},
            tcod.event.K_h: {'action': 'move', 'dx': -1},
            tcod.event.K_l: {'action': 'move', 'dx': 1},
            # Diagonal movement
            tcod.event.K_y: {'action': 'move', 'dx': -1, 'dy': -1},
            tcod.event.K_u: {'action': 'move', 'dx': 1, 'dy': -1},
            tcod.event.K_b: {'action': 'move', 'dx': -1, 'dy': 1},
            tcod.event.K_n: {'action': 'move', 'dx': 1, 'dy': 1},
            # Other actions
            tcod.event.K_PERIOD: {'action': 'wait'},
            tcod.event.K_ESCAPE: {'action': 'exit'},
            tcod.event.K_g: {'action': 'pickup'},
            tcod.event.K_i: {'action': 'show_inventory'},
            tcod.event.K_d: {'action': 'drop_inventory'},
            tcod.event.K_c: {'action': 'show_character'},
            tcod.event.K_GREATER: {'action': 'use_stairs', 'direction': 'down'},
            tcod.event.K_LESS: {'action': 'use_stairs', 'direction': 'up'},
            # Save/Load
            tcod.event.K_F5: {'action': 'save_game'},
            tcod.event.K_F9: {'action': 'load_game'}
        }
    
    def handle_input(self, event: tcod.event.Event, game_state: GameStates = GameStates.PLAYERS_TURN) -> Optional[Dict[str, Any]]:
        """
        Handle input events based on game state.
        
        Args:
            event: The input event
            game_state: Current game state
            
        Returns:
            Action dictionary or None
        """
        # Ignore key repeat events
        if isinstance(event, tcod.event.KeyDown) and event.repeat:
            return None
            
        if game_state == GameStates.PLAYERS_TURN:
            return self._handle_player_turn_keys(event)
        elif game_state == GameStates.PLAYER_DEAD:
            return self._handle_player_dead_keys(event)
        elif game_state == GameStates.TARGETING:
            return self._handle_targeting_keys(event)
        elif game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
            return self._handle_inventory_keys(event)
        elif game_state == GameStates.LEVEL_UP:
            return self._handle_level_up_keys(event)
        elif game_state == GameStates.CHARACTER_SCREEN:
            return self._handle_character_screen_keys(event)
        elif game_state in (GameStates.SAVE_GAME, GameStates.LOAD_GAME):
            return self._handle_save_load_keys(event)
            
        return None
    
    def _handle_player_turn_keys(self, event: tcod.event.Event) -> Optional[Dict[str, Any]]:
        """Handle keys during player's turn."""
        if isinstance(event, tcod.event.KeyDown):
            return self.key_actions.get(event.sym)
        return None
    
    def _handle_player_dead_keys(self, event: tcod.event.Event) -> Optional[Dict[str, Any]]:
        """Handle keys when player is dead."""
        if isinstance(event, tcod.event.KeyDown):
            if event.sym == tcod.event.K_ESCAPE:
                return {'action': 'exit'}
            elif event.sym == tcod.event.K_i:
                return {'action': 'show_inventory'}
        return None
    
    def _handle_targeting_keys(self, event: tcod.event.Event) -> Optional[Dict[str, Any]]:
        """Handle keys during targeting mode."""
        if isinstance(event, tcod.event.KeyDown):
            if event.sym == tcod.event.K_ESCAPE:
                return {'action': 'exit'}
        return None
    
    def _handle_inventory_keys(self, event: tcod.event.Event) -> Optional[Dict[str, Any]]:
        """Handle keys in inventory screen."""
        if isinstance(event, tcod.event.KeyDown):
            index = event.sym - tcod.event.K_a
            if 0 <= index <= 26:
                return {'action': 'inventory_index', 'inventory_index': index}
            
            if event.sym == tcod.event.K_ESCAPE:
                return {'action': 'exit'}
        return None
    
    def _handle_level_up_keys(self, event: tcod.event.Event) -> Optional[Dict[str, Any]]:
        """Handle keys during level up."""
        if isinstance(event, tcod.event.KeyDown):
            if event.sym == tcod.event.K_a:
                return {'action': 'level_up', 'choice': 'hp'}
            elif event.sym == tcod.event.K_b:
                return {'action': 'level_up', 'choice': 'str'}
            elif event.sym == tcod.event.K_c:
                return {'action': 'level_up', 'choice': 'def'}
        return None
    
    def _handle_character_screen_keys(self, event: tcod.event.Event) -> Optional[Dict[str, Any]]:
        """Handle keys in character screen."""
        if isinstance(event, tcod.event.KeyDown):
            if event.sym == tcod.event.K_ESCAPE:
                return {'action': 'exit'}
        return None
    
    def _handle_save_load_keys(self, event: tcod.event.Event) -> Optional[Dict[str, Any]]:
        """Handle keys in save/load screen."""
        if isinstance(event, tcod.event.KeyDown):
            if event.sym == tcod.event.K_ESCAPE:
                return {'action': 'exit'}
            elif event.sym == tcod.event.K_UP:
                return {'action': 'move_cursor', 'dy': -1}
            elif event.sym == tcod.event.K_DOWN:
                return {'action': 'move_cursor', 'dy': 1}
            elif event.sym == tcod.event.K_RETURN:
                return {'action': 'select'}
        return None 