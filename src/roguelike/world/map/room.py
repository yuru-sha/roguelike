from dataclasses import dataclass
from typing import Tuple, Optional

import numpy as np

from roguelike.world.map.tiles import Tile

@dataclass
class Rect:
    """
    A rectangle on the map, used to characterize a room.
    """
    x1: int
    y1: int
    x2: int
    y2: int
    
    @property
    def center(self) -> Tuple[int, int]:
        """Returns the center coordinates of the room."""
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return center_x, center_y
    
    @property
    def width(self) -> int:
        """Returns the width of the room."""
        return self.x2 - self.x1
    
    @property
    def height(self) -> int:
        """Returns the height of the room."""
        return self.y2 - self.y1
    
    def intersects(self, other: 'Rect') -> bool:
        """Returns True if this rectangle intersects with another one."""
        return (
            self.x1 <= other.x2 and
            self.x2 >= other.x1 and
            self.y1 <= other.y2 and
            self.y2 >= other.y1
        )

def create_room(tiles: np.ndarray, room: Rect) -> None:
    """
    Create a room in the tiles array by setting tiles to unblocked.
    
    Args:
        tiles: The tile array to modify
        room: The room to create
    """
    # Set the tiles within the room area to unblocked
    tiles[room.y1+1:room.y2, room.x1+1:room.x2] = Tile(blocked=False, block_sight=False)

def create_h_tunnel(tiles: np.ndarray, x1: int, x2: int, y: int) -> None:
    """
    Create a horizontal tunnel between x1 and x2 at y.
    
    Args:
        tiles: The tile array to modify
        x1: Starting x coordinate
        x2: Ending x coordinate
        y: The y coordinate of the tunnel
    """
    for x in range(min(x1, x2), max(x1, x2) + 1):
        tiles[y][x] = Tile(blocked=False, block_sight=False)

def create_v_tunnel(tiles: np.ndarray, y1: int, y2: int, x: int) -> None:
    """
    Create a vertical tunnel between y1 and y2 at x.
    
    Args:
        tiles: The tile array to modify
        y1: Starting y coordinate
        y2: Ending y coordinate
        x: The x coordinate of the tunnel
    """
    for y in range(min(y1, y2), max(y1, y2) + 1):
        tiles[y][x] = Tile(blocked=False, block_sight=False)

def place_entities(room: Rect, dungeon_level: int) -> Tuple[int, int]:
    """
    Returns a random position within a room.
    
    Args:
        room: The room to place entities in
        dungeon_level: Current dungeon level (affects entity placement)
        
    Returns:
        Tuple of (x, y) coordinates
    """
    # Return a random position inside the room
    x = np.random.randint(room.x1 + 1, room.x2)
    y = np.random.randint(room.y1 + 1, room.y2)
    return x, y 