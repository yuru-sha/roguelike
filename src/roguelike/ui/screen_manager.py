"""
Screen management system for handling different game screens.
"""

import logging
from typing import Any, Dict, Optional

import tcod

from roguelike.game.states.game_state import GameState, GameStates
from roguelike.ui.screens.save_load_screen import SaveLoadScreen
from roguelike.ui.screens.achievements_screen import AchievementsScreen
from roguelike.ui.message_log import MessageLog
from roguelike.core.constants import Colors, SCREEN_WIDTH, SCREEN_HEIGHT
from roguelike.core.event import EventManager, Event, EventType

logger = logging.getLogger(__name__)

class ScreenManager:
    """Manages different game screens and their transitions."""

    def __init__(self, console: tcod.console.Console, game_state: GameState):
        """Initialize the screen manager.
        
        Args:
            console: The console to render to
            game_state: The current game state
        """
        self.console = console
        self.game_state = game_state
        self.message_log = MessageLog(console)
        self.current_screen: Optional[SaveLoadScreen | AchievementsScreen] = None

        # Subscribe to message log events
        self.event_manager = EventManager.get_instance()
        self.event_manager.subscribe(EventType.MESSAGE_LOG, self._handle_message_log)

        # Message log dimensions
        self.message_log_x = 21
        self.message_log_y = SCREEN_HEIGHT - 5
        self.message_log_width = SCREEN_WIDTH - 21
        self.message_log_height = 5

    def _handle_message_log(self, event: Event) -> None:
        """Handle message log events."""
        message = event.data.get("message")
        color = event.data.get("color")
        if message and color:
            self.message_log.add_message(message, color)
            # Keep only the last N messages
            if len(self.message_log.messages) > 50:  # Adjust this number as needed
                self.message_log.messages.pop(0)

    def switch_to_achievements_screen(self) -> None:
        """Switch to the achievements screen."""
        try:
            self.game_state.state = GameStates.ACHIEVEMENTS
            self.current_screen = AchievementsScreen(self.console)
            logger.debug("Switched to achievements screen")

        except Exception as e:
            logger.error(f"Error switching to achievements screen: {e}")
            raise

    def switch_to_save_screen(self) -> None:
        """Switch to the save game screen."""
        try:
            self.game_state.state = GameStates.SAVE_GAME
            self.current_screen = SaveLoadScreen(self.console, is_save=True)
            self.message_log.add_message("Select a slot to save the game (0-9)", Colors.WHITE)
            logger.debug("Switched to save screen")

        except Exception as e:
            logger.error(f"Error switching to save screen: {e}")
            raise

    def switch_to_load_screen(self) -> None:
        """Switch to the load game screen."""
        try:
            self.game_state.state = GameStates.LOAD_GAME
            self.current_screen = SaveLoadScreen(self.console, is_save=False)
            self.message_log.add_message("Select a slot to load the game (0-9)", Colors.WHITE)
            logger.debug("Switched to load screen")

        except Exception as e:
            logger.error(f"Error switching to load screen: {e}")
            raise

    def return_to_game(self) -> None:
        """Return to the main game screen."""
        try:
            self.game_state.state = GameStates.PLAYERS_TURN
            self.current_screen = None
            logger.debug("Returned to game screen")

        except Exception as e:
            logger.error(f"Error returning to game screen: {e}")
            raise

    def handle_input(self, event: Any) -> Optional[Dict[str, Any]]:
        """Handle input events for the current screen.
        
        Args:
            event: The input event to handle
            
        Returns:
            Action dict if input was handled, None otherwise
        """
        try:
            if self.current_screen:
                return self.current_screen.handle_input(event)
            return None

        except Exception as e:
            logger.error(f"Error handling screen input: {e}")
            raise

    def render(self, world: Any, map_manager: Any, renderer: Any) -> None:
        """Render the current screen.
        
        Args:
            world: The game world
            map_manager: The map manager
            renderer: The game renderer
        """
        try:
            renderer.clear()

            if self.current_screen:
                # Render special screen (save/load/achievements)
                self.current_screen.render()
            else:
                # Render normal game screen
                renderer.render_map(map_manager.tiles, map_manager.fov_map)
                renderer.render_entities(world, map_manager.tiles, map_manager.fov_map)
                self.message_log.render(
                    self.console,
                    self.message_log_x,
                    self.message_log_y,
                    self.message_log_width,
                    self.message_log_height
                )

            logger.debug("Rendered current screen")

        except Exception as e:
            logger.error(f"Error rendering screen: {e}")
            raise

    def add_message(self, message: str, color: tuple = Colors.WHITE) -> None:
        """Add a message to the message log.
        
        Args:
            message: The message text
            color: The message color (RGB tuple)
        """
        # For backward compatibility, convert to event
        self.event_manager.publish(Event(
            EventType.MESSAGE_LOG,
            {"message": message, "color": color}
        ))

    def get_messages(self) -> list:
        """Get all messages in the log."""
        return self.message_log.messages 