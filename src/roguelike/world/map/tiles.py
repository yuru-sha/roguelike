from enum import Enum, auto
from typing import Any, Dict, List, Tuple, Type, TypeVar

from roguelike.world.entity.components.serializable import \
    SerializableComponent


class TileType(Enum):
    WALL = auto()
    FLOOR = auto()
    STAIRS_DOWN = auto()
    STAIRS_UP = auto()


T = TypeVar("T", bound="Tile")


class Tile(SerializableComponent):
    """A tile on a map."""

    def __init__(self, tile_type: TileType):
        self.tile_type = tile_type
        self.explored = False
        self.blocked = tile_type == TileType.WALL
        self.block_sight = tile_type == TileType.WALL

    @property
    def char(self) -> str:
        if self.tile_type == TileType.WALL:
            return "#"
        elif self.tile_type == TileType.STAIRS_DOWN:
            return ">"
        elif self.tile_type == TileType.STAIRS_UP:
            return "<"
        return "."

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert tile to dictionary."""
        return {
            "tile_type": self.tile_type.name,
            "explored": self.explored,
            "blocked": self.blocked,
            "block_sight": self.block_sight,
        }

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create tile from dictionary."""
        # Handle Tile object
        if isinstance(data, Tile):
            return cls(data.tile_type)

        # Handle dictionary formats
        if not isinstance(data, dict):
            raise ValueError(f"Invalid data format for Tile: {data}")

        component_data = data.get("data", data)
        if not isinstance(component_data, dict):
            raise ValueError(f"Invalid component data format: {component_data}")

        # Convert tile_type string to TileType enum
        tile_type_str = component_data["tile_type"]
        tile_type = (
            TileType[tile_type_str] if isinstance(tile_type_str, str) else tile_type_str
        )

        tile = cls(tile_type)
        tile.explored = component_data["explored"]
        tile.blocked = component_data["blocked"]
        tile.block_sight = component_data["block_sight"]
        return tile


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
