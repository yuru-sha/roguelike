from typing import Tuple, List
from enum import Enum, auto

class TileType(Enum):
    WALL = auto()
    FLOOR = auto()
    STAIRS_DOWN = auto()
    STAIRS_UP = auto()

class Tile:
    """A tile on a map."""

    def __init__(self, tile_type: TileType):
        self.tile_type = tile_type
        self.explored = False
        self.blocked = tile_type == TileType.WALL
        self.block_sight = tile_type == TileType.WALL

    @property
    def char(self) -> str:
        if self.tile_type == TileType.WALL:
            return '#'
        elif self.tile_type == TileType.STAIRS_DOWN:
            return '>'
        elif self.tile_type == TileType.STAIRS_UP:
            return '<'
        return '.'

    @property
    def color(self) -> Tuple[int, int, int]:
        if self.tile_type == TileType.WALL:
            return (130, 110, 50)
        return (200, 180, 50)

    @property
    def dark_color(self) -> Tuple[int, int, int]:
        if self.tile_type == TileType.WALL:
            return (0, 0, 100)
        return (50, 50, 150)

def initialize_tiles(width: int, height: int) -> List[List[Tile]]:
    """
    Initialize a 2D array of tiles.
    
    Args:
        width: Map width
        height: Map height
        
    Returns:
        A 2D array of tiles
    """
    return [[Tile(TileType.WALL) for x in range(width)] for y in range(height)] 