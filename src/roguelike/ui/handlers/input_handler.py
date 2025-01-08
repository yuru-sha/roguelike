"""
Handle keyboard and mouse input.
"""

from typing import Optional, Dict, Any
import tcod.event

from roguelike.game.states.game_state import GameStates

class InputHandler:
    """Handles keyboard input."""
    
    def handle_input(self, event: tcod.event.Event) -> Optional[Dict[str, Any]]:
        """
        Handle keyboard input.
        
        Args:
            event: The input event
            
        Returns:
            Action dictionary or None if input was not handled
        """
        # Movement keys
        if isinstance(event, tcod.event.KeyDown):
            # Arrow keys
            if event.sym == tcod.event.KeySym.UP:
                return {'action': 'move', 'dx': 0, 'dy': -1}
            elif event.sym == tcod.event.KeySym.DOWN:
                return {'action': 'move', 'dx': 0, 'dy': 1}
            elif event.sym == tcod.event.KeySym.LEFT:
                return {'action': 'move', 'dx': -1, 'dy': 0}
            elif event.sym == tcod.event.KeySym.RIGHT:
                return {'action': 'move', 'dx': 1, 'dy': 0}
            
            # Stairs
            elif event.sym == tcod.event.KeySym.PERIOD and event.mod & tcod.event.Modifier.SHIFT:
                # > key (SHIFT + .)
                return {'action': 'use_stairs', 'direction': 'down'}
            elif event.sym == tcod.event.KeySym.COMMA and event.mod & tcod.event.Modifier.SHIFT:
                # < key (SHIFT + ,)
                return {'action': 'use_stairs', 'direction': 'up'}
            
            # Wait
            elif event.sym == tcod.event.KeySym.PERIOD:
                return {'action': 'wait'}
            
            # Exit
            elif event.sym == tcod.event.KeySym.ESCAPE:
                return {'action': 'exit'}
        
        return None 