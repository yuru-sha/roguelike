"""
Handle keyboard and mouse input.
"""

from typing import Optional
import tcod.event

from roguelike.game.actions import Action, MovementAction, WaitAction, QuitAction

class InputHandler:
    """Handle keyboard and mouse input."""
    
    def handle_input(self, event: tcod.event.Event) -> Optional[Action]:
        """Handle input events and return an action if valid."""
        
        if isinstance(event, tcod.event.Quit):
            return QuitAction()
            
        if isinstance(event, tcod.event.KeyDown):
            # Movement keys
            if event.sym == tcod.event.K_UP:
                return MovementAction(0, -1)
            elif event.sym == tcod.event.K_DOWN:
                return MovementAction(0, 1)
            elif event.sym == tcod.event.K_LEFT:
                return MovementAction(-1, 0)
            elif event.sym == tcod.event.K_RIGHT:
                return MovementAction(1, 0)
                
            # Wait
            elif event.sym == tcod.event.K_PERIOD:
                return WaitAction()
                
            # Quit
            elif event.sym == tcod.event.K_ESCAPE:
                return QuitAction()
                
        return None 