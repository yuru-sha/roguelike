import random
from typing import List, Tuple, Optional
import numpy as np

from roguelike.core.constants import MAP_WIDTH, MAP_HEIGHT, ROOM_MIN_SIZE, ROOM_MAX_SIZE, MAX_ROOMS
from roguelike.world.map.room import Rect, create_room, create_h_tunnel, create_v_tunnel
from roguelike.world.map.tiles import initialize_tiles, Tile
from roguelike.utils.logging import GameLogger

logger = GameLogger.get_instance()

class DungeonGenerator:
    """Generates dungeon levels."""
    
    def __init__(self):
        """Initialize the dungeon generator."""
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self.tiles = None
        self.rooms: List[Rect] = []
        self.stairs_position: Optional[Tuple[int, int]] = None
    
    def generate(self) -> Tuple[np.ndarray, Tuple[int, int]]:
        """
        Generate a new dungeon level.
        
        Returns:
            Tuple of (tiles array, player starting position)
        """
        logger.info("Generating new dungeon level")
        
        # Initialize tiles
        self.tiles = initialize_tiles(self.width, self.height)
        self.rooms = []
        player_pos = (self.width // 2, self.height // 2)  # Default position
        
        # Create rooms
        for _ in range(MAX_ROOMS):
            # Random width and height
            w = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            
            # Random position
            x = random.randint(0, self.width - w - 1)
            y = random.randint(0, self.height - h - 1)
            
            new_room = Rect(x, y, w, h)
            
            # Check for intersections with other rooms
            for other_room in self.rooms:
                if new_room.intersects(other_room):
                    break
            else:
                # No intersections, create the room
                create_room(self.tiles, new_room)
                
                if not self.rooms:
                    # First room, place player here
                    player_pos = new_room.get_random_position()
                else:
                    # Connect to previous room
                    prev_room = self.rooms[-1]
                    prev_pos = prev_room.get_random_position()
                    new_pos = new_room.get_random_position()
                    
                    # Create tunnels
                    if random.random() < 0.5:
                        create_h_tunnel(self.tiles, prev_pos[0], new_pos[0], prev_pos[1])
                        create_v_tunnel(self.tiles, prev_pos[1], new_pos[1], new_pos[0])
                    else:
                        create_v_tunnel(self.tiles, prev_pos[1], new_pos[1], prev_pos[0])
                        create_h_tunnel(self.tiles, prev_pos[0], new_pos[0], new_pos[1])
                
                self.rooms.append(new_room)
        
        # Place stairs in last room
        if self.rooms:
            self.stairs_position = self.rooms[-1].get_random_position()
        
        logger.info(f"Generated dungeon with {len(self.rooms)} rooms")
        return self.tiles, player_pos
    
    def is_walkable(self, x: int, y: int) -> bool:
        """
        Check if a position is walkable.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if the position is walkable
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return not self.tiles[y][x].blocked
    
    def get_random_room(self) -> Optional[Rect]:
        """
        Get a random room from the dungeon.
        
        Returns:
            A random room, or None if no rooms exist
        """
        if not self.rooms:
            return None
        return random.choice(self.rooms) 