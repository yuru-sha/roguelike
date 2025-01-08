import pytest
import numpy as np

from roguelike.world.map.generator.dungeon_generator import DungeonGenerator
from roguelike.world.map.room import Rect
from roguelike.core.constants import (
    MAP_WIDTH, MAP_HEIGHT, ROOM_MAX_SIZE, ROOM_MIN_SIZE, MAX_ROOMS
)

def test_dungeon_generator_initialization():
    """Test DungeonGenerator initialization."""
    generator = DungeonGenerator()
    assert generator.width == MAP_WIDTH
    assert generator.height == MAP_HEIGHT
    assert len(generator.rooms) == 0
    assert generator.start_position is None

def test_dungeon_generation():
    """Test dungeon generation."""
    generator = DungeonGenerator()
    tiles, start_pos = generator.generate()
    
    # Check tiles array shape
    assert tiles.shape == (MAP_HEIGHT, MAP_WIDTH)
    
    # Check start position is within map bounds
    assert 0 <= start_pos[0] < MAP_WIDTH
    assert 0 <= start_pos[1] < MAP_HEIGHT
    
    # Check that at least one room was created
    assert len(generator.rooms) > 0
    
    # Check that all rooms are within map bounds
    for room in generator.rooms:
        assert 0 <= room.x1 < MAP_WIDTH
        assert 0 <= room.x2 < MAP_WIDTH
        assert 0 <= room.y1 < MAP_HEIGHT
        assert 0 <= room.y2 < MAP_HEIGHT
        
        # Check room size constraints
        assert ROOM_MIN_SIZE <= room.width <= ROOM_MAX_SIZE
        assert ROOM_MIN_SIZE <= room.height <= ROOM_MAX_SIZE

def test_room_intersection():
    """Test room intersection detection."""
    room1 = Rect(0, 0, 5, 5)
    room2 = Rect(3, 3, 8, 8)  # Overlaps with room1
    room3 = Rect(6, 6, 10, 10)  # No overlap with room1
    
    assert room1.intersects(room2)
    assert room2.intersects(room1)
    assert not room1.intersects(room3)
    assert not room3.intersects(room1)

def test_walkable_tiles():
    """Test walkable tile detection."""
    generator = DungeonGenerator()
    tiles, start_pos = generator.generate()
    
    # Start position should be walkable
    assert generator.is_walkable(*start_pos)
    
    # Tiles inside rooms should be walkable
    for room in generator.rooms:
        center_x, center_y = room.center
        assert generator.is_walkable(center_x, center_y)
    
    # Tiles outside map bounds should not be walkable
    assert not generator.is_walkable(-1, -1)
    assert not generator.is_walkable(MAP_WIDTH, MAP_HEIGHT) 