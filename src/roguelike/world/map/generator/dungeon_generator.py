import random
from typing import List, Optional, Tuple

import numpy as np

from roguelike.core.constants import (MAP_HEIGHT, MAP_WIDTH, MAX_ROOMS,
                                      ROOM_MAX_SIZE, ROOM_MIN_SIZE)
from roguelike.utils.game_logger import GameLogger
from roguelike.world.map.room import (Rect, create_h_tunnel, create_room,
                                      create_v_tunnel)
from roguelike.world.map.tiles import Tile, TileType, initialize_tiles

logger = GameLogger.get_instance()


class DungeonGenerator:
    """Generates dungeon levels."""

    def __init__(self):
        """Initialize the dungeon generator."""
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self.tiles = None
        self.rooms: List[Rect] = []
        self.stairs_down: Optional[Tuple[int, int]] = None
        self.stairs_up: Optional[Tuple[int, int]] = None

    def place_stairs(self, dungeon_level: int) -> None:
        """
        Place stairs in the dungeon.

        Args:
            dungeon_level: Current dungeon level
        """
        if not self.rooms:
            logger.warning("No rooms available for stair placement")
            return

        logger.info(f"Placing stairs on dungeon level {dungeon_level}")

        # Place down stairs in the last room (except on level 26)
        if dungeon_level < 26:
            last_room = self.rooms[-1]
            self.stairs_down = last_room.center
            x, y = self.stairs_down
            self.tiles[y][x] = Tile(TileType.STAIRS_DOWN)
            logger.info(f"Placed down stairs at ({x}, {y}) in the last room")
        else:
            logger.info("Not placing down stairs on level 26")

        # Place up stairs in the first room (except on level 1)
        if dungeon_level > 1:
            first_room = self.rooms[0]
            # Place up stairs near the edge of the first room to avoid player position
            x, y = first_room.center
            offset_x = 2 if x > first_room.x1 + first_room.w // 2 else -2
            self.stairs_up = (x + offset_x, y)
            x, y = self.stairs_up
            self.tiles[y][x] = Tile(TileType.STAIRS_UP)
            logger.info(f"Placed up stairs at ({x}, {y}) in the first room")
        else:
            logger.info("Not placing up stairs on level 1")

    def generate(self, dungeon_level: int) -> Tuple[List[List[Tile]], Tuple[int, int]]:
        """
        Generate a new dungeon level following Rogue's algorithm.

        Args:
            dungeon_level: Current dungeon level

        Returns:
            Tuple of (tiles array, player starting position)
        """
        logger.info(f"Generating dungeon level {dungeon_level}")

        # Initialize tiles
        self.tiles = initialize_tiles(self.width, self.height)
        self.rooms = []

        # Create first room in the center area of the map
        center_x = self.width // 2
        center_y = self.height // 2
        w = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x = center_x - w // 2
        y = center_y - h // 2
        first_room = Rect(x, y, w, h)
        self.create_room(first_room)
        self.rooms.append(first_room)

        # Player starts in the center of the first room
        player_pos = first_room.center

        # Create additional rooms
        for _ in range(MAX_ROOMS - 1):
            # Random width and height
            w = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)

            # Random position
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)

            new_room = Rect(x, y, w, h)

            # Check for intersections with other rooms
            for other_room in self.rooms:
                if new_room.intersects(other_room):
                    break
            else:
                # No intersections, create the room
                self.create_room(new_room)

                # Connect to the nearest room
                nearest_room = min(
                    self.rooms,
                    key=lambda r: abs(r.center[0] - new_room.center[0])
                    + abs(r.center[1] - new_room.center[1]),
                )
                self.connect_rooms(nearest_room, new_room)

                self.rooms.append(new_room)

        # Place stairs
        self.place_stairs(dungeon_level)

        logger.info(
            f"Generated dungeon level {dungeon_level} with {len(self.rooms)} rooms"
        )
        return self.tiles, player_pos

    def create_room(self, room: Rect) -> None:
        """Create a room by setting tiles to floor."""
        for y in range(room.y1 + 1, room.y2):
            for x in range(room.x1 + 1, room.x2):
                self.tiles[y][x] = Tile(TileType.FLOOR)

    def connect_rooms(self, room1: Rect, room2: Rect) -> None:
        """Connect two rooms with L-shaped corridor."""
        x1, y1 = room1.center
        x2, y2 = room2.center

        # Randomly choose whether to go horizontal or vertical first
        if random.random() < 0.5:
            # First horizontal, then vertical
            self.create_h_tunnel(min(x1, x2), max(x1, x2), y1)
            self.create_v_tunnel(min(y1, y2), max(y1, y2), x2)
        else:
            # First vertical, then horizontal
            self.create_v_tunnel(min(y1, y2), max(y1, y2), x1)
            self.create_h_tunnel(min(x1, x2), max(x1, x2), y2)

    def create_h_tunnel(self, x1: int, x2: int, y: int) -> None:
        """Create a horizontal tunnel."""
        for x in range(x1, x2 + 1):
            self.tiles[y][x] = Tile(TileType.FLOOR)

    def create_v_tunnel(self, y1: int, y2: int, x: int) -> None:
        """Create a vertical tunnel."""
        for y in range(y1, y2 + 1):
            self.tiles[y][x] = Tile(TileType.FLOOR)

    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a position is walkable."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return not self.tiles[y][x].blocked
