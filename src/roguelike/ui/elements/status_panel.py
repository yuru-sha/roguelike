"""
Status panel UI element.
"""

from typing import Any, Optional, Tuple
import tcod

from roguelike.core.constants import Colors
from roguelike.world.entity.components.base import Fighter
from roguelike.ui.elements.base import UIElement
from roguelike.ui.layouts.game_layout import GameLayout

class StatusPanel(UIElement):
    """Panel showing player status information."""

    def __init__(self, console: tcod.console.Console):
        """Initialize the status panel.
        
        Args:
            console: The console to render to
        """
        super().__init__(console, GameLayout.PLAYER_STATUS)
        self.title = "Status"

    def render(self, world: Any, player_id: int) -> None:
        """Render the status panel.
        
        Args:
            world: The game world
            player_id: The player entity ID
        """
        super().render()
        
        # Draw title
        self.print_centered(0, f"┤ {self.title} ├", Colors.YELLOW)

        try:
            # Get player stats
            fighter = world.component_for_entity(player_id, Fighter)

            # Draw HP bar
            hp_text = f"HP: {fighter.hp}/{fighter.max_hp}"
            self.print(2, 2, hp_text)
            self.draw_bar(
                2, 3,
                self.area.width - 4,
                fighter.hp,
                fighter.max_hp,
                Colors.RED,
                Colors.DARKER_RED
            )

            # Draw XP
            xp_text = f"XP: {fighter.xp}"
            self.print(2, 4, xp_text)

            # Draw combat stats
            stats_text = f"ATK: {fighter.power} DEF: {fighter.defense}"
            self.print(2, 5, stats_text)

        except Exception as e:
            self.print(2, 2, "Error loading stats", Colors.RED)

    def draw_bar(
        self,
        x: int,
        y: int,
        width: int,
        value: int,
        maximum: int,
        bar_color: Tuple[int, int, int],
        back_color: Tuple[int, int, int]
    ) -> None:
        """Draw a bar showing a value and its maximum.
        
        Args:
            x: X coordinate relative to panel
            y: Y coordinate relative to panel
            width: Width of the bar
            value: Current value
            maximum: Maximum value
            bar_color: Color of the filled portion
            back_color: Color of the empty portion
        """
        # Calculate bar width
        bar_width = int(float(value) / maximum * width)

        # Draw background
        for i in range(width):
            self.console.rgb[self.area.y + y, self.area.x + x + i]["ch"] = ord("█")
            self.console.rgb[self.area.y + y, self.area.x + x + i]["fg"] = back_color

        # Draw bar
        for i in range(bar_width):
            self.console.rgb[self.area.y + y, self.area.x + x + i]["ch"] = ord("█")
            self.console.rgb[self.area.y + y, self.area.x + x + i]["fg"] = bar_color 