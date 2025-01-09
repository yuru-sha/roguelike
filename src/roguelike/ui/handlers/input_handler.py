"""
Handle keyboard and mouse input.
"""

from typing import Optional, Dict, Any
import logging
import tcod.event
from tcod.event import KeySym

from roguelike.game.states.game_state import GameStates
from roguelike.utils.logging import GameLogger

logger = GameLogger.get_instance()

class InputHandler:
    """Handle keyboard and mouse input."""
    
    def __init__(self):
        """Initialize input handler."""
        self.key_actions = {
            # Movement keys
            KeySym.UP: {'action': 'move', 'dy': -1},
            KeySym.DOWN: {'action': 'move', 'dy': 1},
            KeySym.LEFT: {'action': 'move', 'dx': -1},
            KeySym.RIGHT: {'action': 'move', 'dx': 1},
            # Vi keys
            KeySym.k: {'action': 'move', 'dy': -1},
            KeySym.j: {'action': 'move', 'dy': 1},
            KeySym.h: {'action': 'move', 'dx': -1},
            KeySym.l: {'action': 'move', 'dx': 1},
            # Diagonal movement
            KeySym.y: {'action': 'move', 'dx': -1, 'dy': -1},
            KeySym.u: {'action': 'move', 'dx': 1, 'dy': -1},
            KeySym.b: {'action': 'move', 'dx': -1, 'dy': 1},
            KeySym.n: {'action': 'move', 'dx': 1, 'dy': 1},
            # Other actions
            KeySym.SPACE: {'action': 'wait'},
            KeySym.ESCAPE: {'action': 'exit'},
            KeySym.g: {'action': 'pickup'},
            KeySym.i: {'action': 'show_inventory'},
            KeySym.d: {'action': 'drop_inventory'},
            KeySym.c: {'action': 'show_character'},
            # 階段
            KeySym.PERIOD: {'action': 'use_stairs', 'direction': 'down'},  # > (SHIFT + .)
            KeySym.COMMA: {'action': 'use_stairs', 'direction': 'up'},     # < (SHIFT + ,)
        }
    
    def handle_input(self, event: tcod.event.Event, game_state: GameStates = GameStates.PLAYERS_TURN) -> Optional[Dict[str, Any]]:
        """
        Handle input events based on game state.
        
        Args:
            event: The input event
            game_state: Current game state
            
        Returns:
            Action dictionary or None
            
        Raises:
            Exception: 重要なエラーが発生した場合
        """
        # Log event details
        logger.debug(f"Handling input event: {event}, game_state: {game_state}")
        
        try:
            # KeyUpイベントは無視
            if isinstance(event, tcod.event.KeyUp):
                logger.debug("Ignoring key up event")
                return None
            
            # モディファイアキーのみのイベントは無視
            if isinstance(event, tcod.event.KeyDown):
                # モディファイアキーのチェック
                if event.sym in (
                    KeySym.LSHIFT, KeySym.RSHIFT,
                    KeySym.LCTRL, KeySym.RCTRL,
                    KeySym.LALT, KeySym.RALT,
                    KeySym.LGUI, KeySym.RGUI,
                    KeySym.MODE, KeySym.NUMLOCKCLEAR,
                    KeySym.CAPSLOCK, KeySym.SCROLLLOCK
                ):
                    logger.debug(f"Ignoring modifier key event: {event.sym}")
                    return None
                
                # キーリピートイベントは無視
                if event.repeat:
                    logger.debug("Ignoring key repeat event")
                    return None
                
                # モディファイアの状態をログ
                if event.mod != 0:
                    logger.debug(f"Key pressed with modifiers: {event.mod}")
            
            # Handle different game states
            handlers = {
                GameStates.PLAYERS_TURN: self._handle_player_turn_keys,
                GameStates.PLAYER_DEAD: self._handle_player_dead_keys,
                GameStates.TARGETING: self._handle_targeting_keys,
                GameStates.SHOW_INVENTORY: self._handle_inventory_keys,
                GameStates.DROP_INVENTORY: self._handle_inventory_keys,
                GameStates.LEVEL_UP: self._handle_level_up_keys,
                GameStates.CHARACTER_SCREEN: self._handle_character_screen_keys,
                GameStates.SAVE_GAME: self._handle_save_load_keys,
                GameStates.LOAD_GAME: self._handle_save_load_keys
            }
            
            handler = handlers.get(game_state)
            if not handler:
                logger.warning(f"No handler found for game state: {game_state}")
                return None
            
            # ハンドラを呼び出し、エラーは上位に伝播
            action = handler(event)
            logger.debug(f"Handler {handler.__name__} returned action: {action}")
            return action
            
        except Exception as e:
            logger.error(f"Error handling input event {event}: {str(e)}", exc_info=True)
            logger.error(f"Event details: {vars(event)}")
            logger.error(f"Game state: {game_state}")
            raise  # エラーを上位に伝播
    
    def _handle_player_turn_keys(self, event: tcod.event.Event) -> Optional[Dict[str, Any]]:
        """Handle keys during player's turn."""
        if not isinstance(event, tcod.event.KeyDown):
            return None
            
        # Log key details
        logger.debug(f"Processing key event: sym={event.sym}, scancode={event.scancode}, mod={event.mod}")
        
        # Ctrl + S でセーブ
        if event.sym == KeySym.s and event.mod & tcod.event.Modifier.CTRL:
            logger.debug("Detected Ctrl + S: Save game")
            return {'action': 'save_game'}
            
        # Ctrl + L でロード
        if event.sym == KeySym.l and event.mod & tcod.event.Modifier.CTRL:
            logger.debug("Detected Ctrl + L: Load game")
            return {'action': 'load_game'}
        
        # 階段の処理
        if event.sym == KeySym.PERIOD and event.mod & tcod.event.Modifier.SHIFT:
            logger.debug("Detected > key: Use stairs down")
            return {'action': 'use_stairs', 'direction': 'down'}
        elif event.sym == KeySym.COMMA and event.mod & tcod.event.Modifier.SHIFT:
            logger.debug("Detected < key: Use stairs up")
            return {'action': 'use_stairs', 'direction': 'up'}
        
        # モディファイアキーのみの場合は無視
        if event.sym in (KeySym.LSHIFT, KeySym.RSHIFT, KeySym.LCTRL, KeySym.RCTRL, 
                       KeySym.LALT, KeySym.RALT, KeySym.LGUI, KeySym.RGUI):
            logger.debug(f"Ignoring modifier key: {event.sym}")
            return None
        
        # Check if key exists in actions map
        action = self.key_actions.get(event.sym)
        if action:
            logger.debug(f"Found action for key {event.sym}: {action}")
            return action.copy()  # Return a copy to prevent modification of the original
        else:
            logger.debug(f"No action found for key {event.sym}")
            return None
    
    def _handle_player_dead_keys(self, event: tcod.event.Event) -> Optional[Dict[str, Any]]:
        """Handle keys when player is dead."""
        try:
            if isinstance(event, tcod.event.KeyDown):
                if event.sym == KeySym.ESCAPE:
                    return {'action': 'exit'}
                elif event.sym == KeySym.i:
                    return {'action': 'show_inventory'}
            return None
        except Exception as e:
            logger.error(f"Error handling player dead key: {str(e)}", exc_info=True)
            return None
    
    def _handle_targeting_keys(self, event: tcod.event.Event) -> Optional[Dict[str, Any]]:
        """Handle keys during targeting mode."""
        try:
            if isinstance(event, tcod.event.KeyDown):
                if event.sym == KeySym.ESCAPE:
                    return {'action': 'exit'}
            return None
        except Exception as e:
            logger.error(f"Error handling targeting key: {str(e)}", exc_info=True)
            return None
    
    def _handle_inventory_keys(self, event: tcod.event.Event) -> Optional[Dict[str, Any]]:
        """Handle keys in inventory screen."""
        try:
            if isinstance(event, tcod.event.KeyDown):
                # Calculate inventory index based on key pressed
                if KeySym.a <= event.sym <= KeySym.z:
                    index = event.sym - KeySym.a
                    return {'action': 'inventory_index', 'inventory_index': index}
                
                if event.sym == KeySym.ESCAPE:
                    return {'action': 'exit'}
            return None
        except Exception as e:
            logger.error(f"Error handling inventory key: {str(e)}", exc_info=True)
            return None
    
    def _handle_level_up_keys(self, event: tcod.event.Event) -> Optional[Dict[str, Any]]:
        """Handle keys during level up."""
        try:
            if isinstance(event, tcod.event.KeyDown):
                if event.sym == KeySym.a:
                    return {'action': 'level_up', 'choice': 'hp'}
                elif event.sym == KeySym.b:
                    return {'action': 'level_up', 'choice': 'str'}
                elif event.sym == KeySym.c:
                    return {'action': 'level_up', 'choice': 'def'}
            return None
        except Exception as e:
            logger.error(f"Error handling level up key: {str(e)}", exc_info=True)
            return None
    
    def _handle_character_screen_keys(self, event: tcod.event.Event) -> Optional[Dict[str, Any]]:
        """Handle keys in character screen."""
        try:
            if isinstance(event, tcod.event.KeyDown):
                if event.sym == KeySym.ESCAPE:
                    return {'action': 'exit'}
            return None
        except Exception as e:
            logger.error(f"Error handling character screen key: {str(e)}", exc_info=True)
            return None
    
    def _handle_save_load_keys(self, event: tcod.event.Event) -> Optional[Dict[str, Any]]:
        """Handle keys in save/load screen."""
        try:
            if isinstance(event, tcod.event.KeyDown):
                if event.sym == KeySym.ESCAPE:
                    return {'action': 'exit'}
                elif event.sym == KeySym.UP:
                    return {'action': 'move_cursor', 'dy': -1}
                elif event.sym == KeySym.DOWN:
                    return {'action': 'move_cursor', 'dy': 1}
                elif event.sym == KeySym.RETURN:
                    return {'action': 'select'}
            return None
        except Exception as e:
            logger.error(f"Error handling save/load key: {str(e)}", exc_info=True)
            return None 