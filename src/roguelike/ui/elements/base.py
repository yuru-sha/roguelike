"""
Base classes for UI elements.
"""

from typing import Any, Optional, Tuple
import tcod

from roguelike.ui.layouts.game_layout import Rect
from roguelike.core.constants import Colors

class UIElement:
    """Base class for all UI elements."""

    def __init__(self, console: tcod.console.Console, area: Rect):
        """Initialize the UI element.
        
        Args:
            console: The console to render to
            area: The area this element occupies
        """
        self.console = console
        self.area = area

    def render(self) -> None:
        """Render the UI element."""
        self.clear()
        self.draw_border()

    def clear(self) -> None:
        """Clear the element's area."""
        for y in range(self.area.y, self.area.bottom):
            for x in range(self.area.x, self.area.right):
                self.console.rgb[y, x] = Colors.BLACK

    def draw_border(self) -> None:
        """Draw a border around the element."""
        # Corners
        self.console.rgb[self.area.y, self.area.x]["ch"] = ord("┌")
        self.console.rgb[self.area.y, self.area.right - 1]["ch"] = ord("┐")
        self.console.rgb[self.area.bottom - 1, self.area.x]["ch"] = ord("└")
        self.console.rgb[self.area.bottom - 1, self.area.right - 1]["ch"] = ord("┘")

        # Horizontal lines
        for x in range(self.area.x + 1, self.area.right - 1):
            self.console.rgb[self.area.y, x]["ch"] = ord("─")
            self.console.rgb[self.area.bottom - 1, x]["ch"] = ord("─")

        # Vertical lines
        for y in range(self.area.y + 1, self.area.bottom - 1):
            self.console.rgb[y, self.area.x]["ch"] = ord("│")
            self.console.rgb[y, self.area.right - 1]["ch"] = ord("│")

    def print(self, x: int, y: int, text: str, fg: Tuple[int, int, int] = Colors.WHITE) -> None:
        """Print text at the given position relative to the element's area.
        
        Args:
            x: X coordinate relative to element's area
            y: Y coordinate relative to element's area
            text: Text to print
            fg: Text color
        """
        abs_x = self.area.x + x
        abs_y = self.area.y + y
        if 0 <= x < self.area.width and 0 <= y < self.area.height:
            self.console.print(x=abs_x, y=abs_y, string=text, fg=fg)

    def print_centered(self, y: int, text: str, fg: Tuple[int, int, int] = Colors.WHITE) -> None:
        """Print centered text at the given vertical position.
        
        Args:
            y: Y coordinate relative to element's area
            text: Text to print
            fg: Text color
        """
        x = (self.area.width - len(text)) // 2
        self.print(x, y, text, fg) 