"""
Input handling system for the game.
"""

import logging
import time
from typing import Any, Dict, Optional

import tcod
from tcod.event import KeySym

from roguelike.game.states.game_state import GameStates

logger = logging.getLogger(__name__)


class InputHandler:
    """Handles input events for the game."""

    def __init__(self):
        """Initialize the input handler."""
        self._last_key_time = 0
        self._key_repeat_delay = 0.1  # seconds

    def handle_input(self, event: Any, game_state: GameStates) -> Optional[Dict[str, Any]]:
        """Handle input events based on the current game state.
        
        Args:
            event: The input event to handle
            game_state: The current game state
            
        Returns:
            Action dict if input was handled, None otherwise
        """
        try:
            if game_state == GameStates.PLAYERS_TURN:
                return self._handle_player_turn_keys(event)
            elif game_state in (GameStates.SAVE_GAME, GameStates.LOAD_GAME, GameStates.ACHIEVEMENTS):
                return self._handle_menu_keys(event)

            return None

        except Exception as e:
            logger.error(f"Error handling input: {e}", exc_info=True)
            return None

    def _handle_player_turn_keys(self, event: Any) -> Optional[Dict[str, Any]]:
        """Handle key events during player's turn.
        
        Args:
            event: The key event to handle
            
        Returns:
            Action dict if key was handled, None otherwise
        """
        try:
            if not isinstance(event, tcod.event.KeyDown):
                return None

            # Get current time
            current_time = time.monotonic()

            # Check if enough time has passed since last key press
            if current_time - self._last_key_time < self._key_repeat_delay:
                return None

            # Update last key time
            self._last_key_time = current_time

            key = event.sym

            # Movement keys
            if key == KeySym.UP:
                return {"action": "move", "dy": -1}
            elif key == KeySym.DOWN:
                return {"action": "move", "dy": 1}
            elif key == KeySym.LEFT:
                return {"action": "move", "dx": -1}
            elif key == KeySym.RIGHT:
                return {"action": "move", "dx": 1}

            # Item interaction
            elif key == KeySym.g:
                return {"action": "pickup"}
            elif key == KeySym.i:
                return {"action": "show_inventory"}
            elif key == KeySym.d:
                return {"action": "drop_inventory"}

            # Stairs
            elif key == KeySym.PERIOD and event.mod & tcod.event.KMOD_SHIFT:
                return {"action": "use_stairs", "direction": "down"}
            elif key == KeySym.COMMA and event.mod & tcod.event.KMOD_SHIFT:
                return {"action": "use_stairs", "direction": "up"}

            # Save/Load
            elif key == KeySym.s and event.mod & tcod.event.KMOD_CTRL:
                return {"action": "save_game"}
            elif key == KeySym.l and event.mod & tcod.event.KMOD_CTRL:
                return {"action": "load_game"}

            # Achievements
            elif key == KeySym.a and event.mod & tcod.event.KMOD_CTRL:
                return {"action": "achievements"}

            # Exit
            elif key == KeySym.ESCAPE:
                return {"action": "exit"}

            return None

        except Exception as e:
            logger.error(f"Error handling player turn keys: {e}", exc_info=True)
            return None

    def _handle_menu_keys(self, event: Any) -> Optional[Dict[str, Any]]:
        """Handle key events in menus.
        
        Args:
            event: The key event to handle
            
        Returns:
            Action dict if key was handled, None otherwise
        """
        try:
            if not isinstance(event, tcod.event.KeyDown):
                return None

            # Get current time
            current_time = time.monotonic()

            # Check if enough time has passed since last key press
            if current_time - self._last_key_time < self._key_repeat_delay:
                return None

            # Update last key time
            self._last_key_time = current_time

            key = event.sym

            if key == KeySym.ESCAPE:
                return {"action": "exit"}
            elif key == KeySym.UP:
                return {"action": "move_cursor", "dy": -1}
            elif key == KeySym.DOWN:
                return {"action": "move_cursor", "dy": 1}
            elif key in (KeySym.RETURN, KeySym.KP_ENTER):
                return {"action": "select"}

            # Number keys for save/load slots
            elif KeySym.N0 <= key <= KeySym.N9:
                slot = key - KeySym.N0
                return {"action": "select_slot", "slot": slot}

            return None

        except Exception as e:
            logger.error(f"Error handling menu keys: {e}", exc_info=True)
            return None
