from typing import List, Tuple, Optional
import numpy as np

from roguelike.core.constants import (
    MAP_WIDTH, MAP_HEIGHT, ROOM_MAX_SIZE, ROOM_MIN_SIZE, MAX_ROOMS
)
from roguelike.world.map.room import Rect, create_room, create_h_tunnel, create_v_tunnel
from roguelike.world.map.tiles import initialize_tiles, Tile
from roguelike.utils.logging import GameLogger

logger = GameLogger.get_instance()

class DungeonGenerator:
    """
    Generates a dungeon level using a room-and-corridor approach.
    """
    
    def __init__(self, width: int = MAP_WIDTH, height: int = MAP_HEIGHT):
        """
        Initialize the dungeon generator.
        
        Args:
            width: Width of the dungeon
            height: Height of the dungeon
        """
        self.width = width
        self.height = height
        self.tiles = initialize_tiles(width, height)
        self.rooms: List[Rect] = []
        self.start_position: Optional[Tuple[int, int]] = None
        
    def generate(self) -> Tuple[np.ndarray, Tuple[int, int]]:
        """
        Generate a new dungeon level.
        
        Returns:
            Tuple of (tiles array, player starting position)
        """
        logger.info("Generating new dungeon level...")
        
        self.rooms = []
        self.tiles = initialize_tiles(self.width, self.height)
        
        for r in range(MAX_ROOMS):
            # Random width and height
            w = np.random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            h = np.random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            
            # Random position without going out of the boundaries of the map
            x = np.random.randint(0, self.width - w - 1)
            y = np.random.randint(0, self.height - h - 1)
            
            new_room = Rect(x, y, x + w, y + h)
            
            # Check if the room intersects with existing rooms
            for other_room in self.rooms:
                if new_room.intersects(other_room):
                    break
            else:  # No intersection found
                # Create the room
                create_room(self.tiles, new_room)
                
                if not self.rooms:  # First room
                    # Player starts in the first room
                    self.start_position = new_room.center
                else:
                    # Connect to the previous room
                    prev_x, prev_y = self.rooms[-1].center
                    curr_x, curr_y = new_room.center
                    
                    # Randomly choose horizontal-then-vertical or vertical-then-horizontal
                    if np.random.random() < 0.5:
                        create_h_tunnel(self.tiles, prev_x, curr_x, prev_y)
                        create_v_tunnel(self.tiles, prev_y, curr_y, curr_x)
                    else:
                        create_v_tunnel(self.tiles, prev_y, curr_y, prev_x)
                        create_h_tunnel(self.tiles, prev_x, curr_x, curr_y)
                
                self.rooms.append(new_room)
        
        if not self.start_position:
            raise RuntimeError("Failed to generate dungeon: no rooms created")
        
        logger.info(f"Generated dungeon with {len(self.rooms)} rooms")
        return self.tiles, self.start_position
    
    def get_random_room(self) -> Rect:
        """
        Returns a random room from the dungeon.
        
        Returns:
            A random room
        
        Raises:
            RuntimeError: If no rooms exist
        """
        if not self.rooms:
            raise RuntimeError("No rooms exist in the dungeon")
        return np.random.choice(self.rooms)
    
    def is_walkable(self, x: int, y: int) -> bool:
        """
        Check if a position is walkable.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if the position is walkable
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return not self.tiles[y][x].blocked
        return False 