"""
Dungeon state management system.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from roguelike.core.constants import Colors, MAP_WIDTH, MAP_HEIGHT
from roguelike.world.map.tiles import Tile, TileType
from roguelike.world.entity.components.base import Position

logger = logging.getLogger(__name__)

class DungeonState:
    """Manages the dungeon's state and attributes."""

    def __init__(self, world: Any, game_state: Any):
        """Initialize the dungeon state manager.
        
        Args:
            world: The game world
            game_state: The current game state
        """
        self.world = world
        self.game_state = game_state

    def get_current_level(self) -> int:
        """Get the current dungeon level.
        
        Returns:
            Current dungeon level number
        """
        return self.game_state.dungeon_level

    def get_tile_at(self, x: int, y: int) -> Optional[Tile]:
        """Get the tile at the specified coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Tile at the specified coordinates, or None if out of bounds
        """
        try:
            if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT):
                return None

            return self.game_state.tiles[y][x]

        except Exception as e:
            logger.error(f"Error getting tile at ({x}, {y}): {str(e)}", exc_info=True)
            raise

    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a position is walkable.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if the position is walkable, False otherwise
        """
        try:
            # Check bounds
            if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT):
                return False

            # Check tile
            tile = self.game_state.tiles[y][x]
            if tile.blocked:
                return False

            # Check for blocking entities
            for ent, (pos,) in self.world.get_components(Position):
                if pos.x == x and pos.y == y:
                    # Check if entity blocks movement
                    # Add more component checks here as needed
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking walkable at ({x}, {y}): {str(e)}", exc_info=True)
            raise

    def is_visible(self, x: int, y: int) -> bool:
        """Check if a position is visible to the player.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if the position is visible, False otherwise
        """
        try:
            if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT):
                return False

            return bool(self.game_state.fov_map[y, x])

        except Exception as e:
            logger.error(f"Error checking visibility at ({x}, {y}): {str(e)}", exc_info=True)
            raise

    def is_explored(self, x: int, y: int) -> bool:
        """Check if a position has been explored.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if the position has been explored, False otherwise
        """
        try:
            if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT):
                return False

            return self.game_state.tiles[y][x].explored

        except Exception as e:
            logger.error(f"Error checking explored at ({x}, {y}): {str(e)}", exc_info=True)
            raise

    def get_entities_at(self, x: int, y: int) -> List[int]:
        """Get all entities at the specified position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            List of entity IDs at the position
        """
        try:
            entities = []
            for ent, (pos,) in self.world.get_components(Position):
                if pos.x == x and pos.y == y:
                    entities.append(ent)
            return entities

        except Exception as e:
            logger.error(f"Error getting entities at ({x}, {y}): {str(e)}", exc_info=True)
            raise

    def find_path(self, start_x: int, start_y: int, end_x: int, end_y: int) -> List[Tuple[int, int]]:
        """Find a path between two points.
        
        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            
        Returns:
            List of (x, y) coordinates forming the path
        """
        try:
            # Create cost map (1 for walkable, 0 for blocked)
            cost = np.ones((MAP_HEIGHT, MAP_WIDTH), dtype=np.int8)
            for y in range(MAP_HEIGHT):
                for x in range(MAP_WIDTH):
                    if not self.is_walkable(x, y):
                        cost[y, x] = 0

            # Use A* pathfinding
            path = []  # TODO: Implement A* pathfinding
            return path

        except Exception as e:
            logger.error(
                f"Error finding path from ({start_x}, {start_y}) to ({end_x}, {end_y}): {str(e)}",
                exc_info=True
            )
            raise

    def get_nearest_walkable(self, x: int, y: int) -> Tuple[int, int]:
        """Find the nearest walkable position to the specified coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Tuple of (x, y) coordinates of the nearest walkable position
        """
        try:
            if self.is_walkable(x, y):
                return (x, y)

            # Search in expanding squares
            for d in range(1, max(MAP_WIDTH, MAP_HEIGHT)):
                for dx in range(-d, d + 1):
                    for dy in range(-d, d + 1):
                        if abs(dx) == d or abs(dy) == d:  # Only check the perimeter
                            new_x = x + dx
                            new_y = y + dy
                            if (0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT
                                and self.is_walkable(new_x, new_y)):
                                return (new_x, new_y)

            # If no walkable position found, return original coordinates
            return (x, y)

        except Exception as e:
            logger.error(f"Error finding nearest walkable to ({x}, {y}): {str(e)}", exc_info=True)
            raise

    def get_stairs_position(self, up: bool = True) -> Optional[Tuple[int, int]]:
        """Get the position of stairs on the current level.
        
        Args:
            up: True for up stairs, False for down stairs
            
        Returns:
            Tuple of (x, y) coordinates of the stairs, or None if not found
        """
        try:
            target_type = TileType.STAIRS_UP if up else TileType.STAIRS_DOWN
            for y in range(MAP_HEIGHT):
                for x in range(MAP_WIDTH):
                    if self.game_state.tiles[y][x].tile_type == target_type:
                        return (x, y)
            return None

        except Exception as e:
            logger.error(f"Error finding stairs: {str(e)}", exc_info=True)
            raise 