from dataclasses import dataclass, field
import numpy as np

@dataclass
class Tile:
    """A tile in the game map."""
    blocked: bool = True
    block_sight: bool = True
    explored: bool = False
    
    def __post_init__(self):
        """Set block_sight to match blocked by default."""
        if self.block_sight is None:
            self.block_sight = self.blocked

def initialize_tiles(width: int, height: int) -> np.ndarray:
    """
    Initialize a 2D array of tiles.
    
    Args:
        width: Map width
        height: Map height
        
    Returns:
        A 2D array of tiles
    """
    tiles = np.empty((height, width), dtype=object)
    for y in range(height):
        for x in range(width):
            tiles[y][x] = Tile()
    return tiles 