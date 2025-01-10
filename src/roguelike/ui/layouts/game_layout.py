"""
Game screen layout definitions.

This module defines the layout constants for the game screen,
including the positions and dimensions of various UI elements.
"""

from dataclasses import dataclass
from typing import Tuple

from roguelike.core.constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    MAP_WIDTH,
    MAP_HEIGHT,
)

@dataclass(frozen=True)
class Rect:
    """Rectangle area definition."""
    x: int
    y: int
    width: int
    height: int

    @property
    def right(self) -> int:
        """Right edge position."""
        return self.x + self.width

    @property
    def bottom(self) -> int:
        """Bottom edge position."""
        return self.y + self.height

class GameLayout:
    """Layout definitions for the game screen."""

    # Main areas
    MAP_AREA = Rect(0, 0, MAP_WIDTH, MAP_HEIGHT)
    SIDEBAR_AREA = Rect(MAP_WIDTH, 0, SCREEN_WIDTH - MAP_WIDTH, MAP_HEIGHT)
    MESSAGE_AREA = Rect(0, MAP_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT - MAP_HEIGHT)

    # Sidebar elements
    PLAYER_STATUS = Rect(
        MAP_WIDTH + 1,
        1,
        SCREEN_WIDTH - MAP_WIDTH - 2,
        7
    )
    
    MINIMAP = Rect(
        MAP_WIDTH + 1,
        9,
        SCREEN_WIDTH - MAP_WIDTH - 2,
        10
    )
    
    EQUIPMENT = Rect(
        MAP_WIDTH + 1,
        20,
        SCREEN_WIDTH - MAP_WIDTH - 2,
        8
    )
    
    EFFECTS = Rect(
        MAP_WIDTH + 1,
        29,
        SCREEN_WIDTH - MAP_WIDTH - 2,
        6
    )

    # Message log
    MESSAGE_LOG = Rect(
        1,
        MAP_HEIGHT + 1,
        SCREEN_WIDTH - 2,
        SCREEN_HEIGHT - MAP_HEIGHT - 2
    ) 