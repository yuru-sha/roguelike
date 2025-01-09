import random
from typing import Tuple

import numpy as np

from roguelike.world.entity.components.base import Position


class Rect:
    """A rectangular room."""

    def __init__(self, x: int, y: int, w: int, h: int):
        """
        Initialize the room.

        Args:
            x: X coordinate of top-left corner
            y: Y coordinate of top-left corner
            w: Room width
            h: Room height
        """
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    @property
    def x1(self) -> int:
        """Left edge."""
        return self.x

    @property
    def y1(self) -> int:
        """Top edge."""
        return self.y

    @property
    def x2(self) -> int:
        """Right edge."""
        return self.x + self.w

    @property
    def y2(self) -> int:
        """Bottom edge."""
        return self.y + self.h

    @property
    def center(self) -> Tuple[int, int]:
        """Center coordinates."""
        return (self.x + self.w // 2, self.y + self.h // 2)

    def intersects(self, other: "Rect") -> bool:
        """
        Check if this room intersects with another room.

        Args:
            other: The other room to check

        Returns:
            True if the rooms intersect
        """
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )

    def get_random_position(self) -> Tuple[int, int]:
        """
        Get a random position inside the room.

        Returns:
            A tuple of (x, y) coordinates
        """
        x = random.randint(self.x1 + 1, self.x2 - 1)
        y = random.randint(self.y1 + 1, self.y2 - 1)
        return (x, y)


def create_room(tiles: np.ndarray, room: Rect) -> None:
    """
    Create a room by setting tiles to unblocked.

    Args:
        tiles: The tile array to modify
        room: The room to create
    """
    for y in range(room.y + 1, room.y + room.height - 1):
        for x in range(room.x + 1, room.x + room.width - 1):
            tiles[y][x].blocked = False
            tiles[y][x].block_sight = False


def create_h_tunnel(tiles: np.ndarray, x1: int, x2: int, y: int) -> None:
    """
    Create a horizontal tunnel.

    Args:
        tiles: The tile array to modify
        x1: Starting x coordinate
        x2: Ending x coordinate
        y: Y coordinate
    """
    for x in range(min(x1, x2), max(x1, x2) + 1):
        tiles[y][x].blocked = False
        tiles[y][x].block_sight = False


def create_v_tunnel(tiles: np.ndarray, y1: int, y2: int, x: int) -> None:
    """
    Create a vertical tunnel.

    Args:
        tiles: The tile array to modify
        y1: Starting y coordinate
        y2: Ending y coordinate
        x: X coordinate
    """
    for y in range(min(y1, y2), max(y1, y2) + 1):
        tiles[y][x].blocked = False
        tiles[y][x].block_sight = False
