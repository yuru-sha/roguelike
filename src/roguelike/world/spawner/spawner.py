from typing import List, Dict, Any, Optional
import random

from roguelike.world.map.room import Rect
from roguelike.world.entity.prefabs.monsters import MONSTER_CHANCES, create_orc, create_troll
from roguelike.world.entity.prefabs.items import ITEM_CHANCES
from roguelike.world.entity.components.base import Position, Fighter, AI, Item

def get_random_choice_from_chances(chances_dict: dict, dungeon_level: int) -> Any:
    """
    Get a random choice from a dictionary of chances based on the dungeon level.
    """
    valid_choices = [
        (choice, data)
        for choice, data in chances_dict.items()
        if data.get('min_level', 0) <= dungeon_level and (data.get('max_level') is None or dungeon_level <= data.get('max_level'))
    ]

    if not valid_choices:
        return None

    total_chance = sum(data['chance'] for _, data in valid_choices)
    random_chance = random.randint(0, total_chance)

    current_chance = 0
    for choice, data in valid_choices:
        current_chance += data['chance']
        if random_chance <= current_chance:
            return choice

    return None

def place_monsters(world: Any, room: Rect, dungeon_level: int) -> None:
    """
    Place monsters in a room.
    
    Args:
        world: The ECS world
        room: The room to place monsters in
        dungeon_level: Current dungeon level
    """
    # Get number of monsters
    number_of_monsters = random.randint(0, 3)
    
    for _ in range(number_of_monsters):
        # Choose random position inside the room
        pos = room.get_random_position()
        
        # Choose monster type
        monster_choice = get_random_choice_from_chances(MONSTER_CHANCES, dungeon_level)
        
        if monster_choice:
            # Create the monster using the creation function from MONSTER_CHANCES
            MONSTER_CHANCES[monster_choice]['create_function'](world, pos[0], pos[1])

def place_items(world: Any, room: Rect, dungeon_level: int) -> None:
    """
    Place items in a room.
    
    Args:
        world: The ECS world
        room: The room to place items in
        dungeon_level: Current dungeon level
    """
    # Get number of items
    number_of_items = random.randint(0, 2)
    
    for _ in range(number_of_items):
        # Choose random position inside the room
        pos = room.get_random_position()
        
        # Choose item type
        item_choice = get_random_choice_from_chances(ITEM_CHANCES, dungeon_level)
        
        if item_choice:
            # Create the item using the creation function from ITEM_CHANCES
            ITEM_CHANCES[item_choice]['create_function'](world, pos[0], pos[1])

def populate_dungeon(world: Any, rooms: List[Rect], dungeon_level: int) -> None:
    """
    Populate the dungeon with monsters and items.
    
    Args:
        world: The ECS world
        rooms: List of rooms in the dungeon
        dungeon_level: Current dungeon level
    """
    # Skip the first room (where the player starts)
    for room in rooms[1:]:
        # Place monsters
        place_monsters(world, room, dungeon_level)
        
        # Place items
        place_items(world, room, dungeon_level) 