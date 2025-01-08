from dataclasses import dataclass
from typing import Tuple

import numpy as np
import tcod

from roguelike.core.constants import Colors

@dataclass
class Tile:
    """
    A tile on a map. It may or may not be blocked, and may or may not block sight.
    """
    blocked: bool
    block_sight: bool
    explored: bool = False
    
    def __post_init__(self) -> None:
        """
        If a tile is blocked, it also blocks sight by default.
        """
        if self.blocked and not hasattr(self, 'block_sight'):
            self.block_sight = True

class TileGraphics:
    """
    Defines the graphical representation of tiles.
    """
    WALL_CHAR = '#'
    FLOOR_CHAR = '.'
    
    @staticmethod
    def get_tile_graphics(tile: Tile, visible: bool) -> Tuple[str, Tuple[int, int, int], Tuple[int, int, int]]:
        """
        Returns the character and colors for rendering a tile.
        
        Args:
            tile: The tile to get graphics for
            visible: Whether the tile is currently visible
            
        Returns:
            Tuple of (character, foreground color, background color)
        """
        if not tile.explored:
            return (' ', Colors.BLACK, Colors.BLACK)
        
        if tile.blocked:
            char = TileGraphics.WALL_CHAR
            fg = Colors.WHITE
            bg = Colors.LIGHT_WALL if visible else Colors.DARK_WALL
        else:
            char = TileGraphics.FLOOR_CHAR
            fg = Colors.WHITE
            bg = Colors.LIGHT_GROUND if visible else Colors.DARK_GROUND
            
        return (char, fg, bg)

def initialize_tiles(width: int, height: int) -> np.ndarray:
    """
    Initialize a new tile array with the given dimensions.
    
    Args:
        width: The width of the map
        height: The height of the map
        
    Returns:
        A numpy array of tiles
    """
    # Create a 2D array of blocked tiles (walls)
    tiles = np.full((height, width), fill_value=Tile(blocked=True, block_sight=True), dtype=object)
    return tiles 