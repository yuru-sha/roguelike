"""
Save/Load screen implementation.
"""

import logging
from typing import Any, Optional

import tcod

from roguelike.core.constants import SCREEN_WIDTH, SCREEN_HEIGHT, Colors
from roguelike.game.states.game_state import GameStates

logger = logging.getLogger(__name__)

class SaveLoadScreen:
    """Handles the save/load screen interface."""

    def __init__(self, console: Any, is_save: bool = True):
        """Initialize the save/load screen.
        
        Args:
            console: The console to render to
            is_save: True for save screen, False for load screen
        """
        self.console = console
        self.is_save = is_save
        self.selected_slot = 0
        self.title = "Save Game" if is_save else "Load Game"

    def render(self) -> None:
        """Render the save/load screen."""
        try:
            # Clear the screen
            self.console.clear()

            # Draw title
            title_x = SCREEN_WIDTH // 2 - len(self.title) // 2
            self.console.print(x=title_x, y=5, string=self.title, fg=Colors.WHITE)

            # Draw slot options
            for i in range(10):
                text = f"Slot {i}"
                if i == self.selected_slot:
                    color = Colors.YELLOW
                    text = f"> {text} <"
                else:
                    color = Colors.WHITE

                x = SCREEN_WIDTH // 2 - len(text) // 2
                y = 8 + i
                self.console.print(x=x, y=y, string=text, fg=color)

            # Draw instructions
            instructions = "[↑/↓] Select slot   [Enter] Confirm   [Esc] Cancel"
            x = SCREEN_WIDTH // 2 - len(instructions) // 2
            self.console.print(x=x, y=SCREEN_HEIGHT - 3, string=instructions, fg=Colors.LIGHT_GRAY)

        except Exception as e:
            logger.error(f"Error rendering save/load screen: {e}")
            raise

    def handle_input(self, event: Any) -> Optional[dict]:
        """Handle input events.
        
        Args:
            event: The input event to handle
            
        Returns:
            Action dict if input was handled, None otherwise
        """
        try:
            if isinstance(event, tcod.event.KeyDown):
                if event.sym == tcod.event.K_ESCAPE:
                    return {"action": "exit"}
                elif event.sym == tcod.event.K_UP:
                    return {"action": "move_cursor", "dy": -1}
                elif event.sym == tcod.event.K_DOWN:
                    return {"action": "move_cursor", "dy": 1}
                elif event.sym == tcod.event.K_RETURN:
                    return {"action": "select"}

            return None

        except Exception as e:
            logger.error(f"Error handling input: {e}")
            raise

    def move_cursor(self, dy: int) -> None:
        """Move the cursor up or down.
        
        Args:
            dy: Amount to move (-1 for up, 1 for down)
        """
        try:
            if dy < 0:
                self.selected_slot = max(0, self.selected_slot - 1)
            elif dy > 0:
                self.selected_slot = min(9, self.selected_slot + 1)
            logger.debug(f"Moved cursor to slot {self.selected_slot}")

        except Exception as e:
            logger.error(f"Error moving cursor: {e}")
            raise
