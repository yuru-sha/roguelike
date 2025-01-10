"""
Main game screen implementation.
"""

from typing import Any, Optional
import tcod

from roguelike.ui.elements.status_panel import StatusPanel
from roguelike.ui.elements.equipment_panel import EquipmentPanel
from roguelike.ui.elements.effects_panel import EffectsPanel
from roguelike.ui.message_log import MessageLog
from roguelike.ui.layouts.game_layout import GameLayout

class GameScreen:
    """Main game screen."""

    def __init__(self, console: tcod.console.Console):
        """Initialize the game screen.
        
        Args:
            console: The console to render to
        """
        self.console = console
        
        # Initialize UI elements
        self.status_panel = StatusPanel(console)
        self.equipment_panel = EquipmentPanel(console)
        self.effects_panel = EffectsPanel(console)
        self.message_log = MessageLog(console)

    def render(self, world: Any, map_manager: Any, renderer: Any, player_id: int) -> None:
        """Render the game screen.
        
        Args:
            world: The game world
            map_manager: The map manager
            renderer: The game renderer
            player_id: The player entity ID
        """
        # Clear the screen
        renderer.clear()

        # Render the map and entities
        renderer.render_map(map_manager.tiles, map_manager.fov_map)
        renderer.render_entities(world, map_manager.tiles, map_manager.fov_map)

        # Render UI elements
        self.status_panel.render(world, player_id)
        self.equipment_panel.render(world, player_id)
        self.effects_panel.render(world, player_id)
        
        # Render message log
        self.message_log.render(
            self.console,
            GameLayout.MESSAGE_LOG.x,
            GameLayout.MESSAGE_LOG.y,
            GameLayout.MESSAGE_LOG.width,
            GameLayout.MESSAGE_LOG.height
        )

    def add_message(self, text: str, color: tuple) -> None:
        """Add a message to the message log.
        
        Args:
            text: The message text
            color: The message color
        """
        self.message_log.add_message(text, color) 