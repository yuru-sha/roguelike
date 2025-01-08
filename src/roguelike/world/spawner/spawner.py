from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import esper

from roguelike.world.map.room import Rect
from roguelike.core.constants import MAX_MONSTERS_PER_ROOM, MAX_ITEMS_PER_ROOM
from roguelike.world.entity.prefabs.monsters import MONSTER_CHANCES
from roguelike.world.entity.prefabs.items import ITEM_CHANCES
from roguelike.utils.logging import GameLogger

logger = GameLogger.get_instance()

def get_random_choice_from_chances(chances: Dict[str, Dict[str, Any]], dungeon_level: int) -> Optional[str]:
    """
    Choose a random item from the chances dictionary based on dungeon level.
    
    Args:
        chances: Dictionary of chances
        dungeon_level: Current dungeon level
        
    Returns:
        The chosen item key or None if no valid choices
    """
    # Filter choices based on dungeon level
    valid_choices = {
        k: v for k, v in chances.items()
        if (v['min_level'] <= dungeon_level and
            (v['max_level'] is None or dungeon_level <= v['max_level']))
    }
    
    if not valid_choices:
        return None
    
    # Calculate total chance
    total_chance = sum(item['chance'] for item in valid_choices.values())
    
    if total_chance == 0:
        return None
    
    # Roll the dice
    roll = np.random.randint(0, total_chance)
    
    # Find the chosen item
    running_total = 0
    for key, value in valid_choices.items():
        running_total += value['chance']
        if roll < running_total:
            return key
    
    return None

def place_monsters(world: esper.World, room: Rect, dungeon_level: int) -> None:
    """
    Place monsters in a room.
    
    Args:
        world: The game world
        room: The room to place monsters in
        dungeon_level: Current dungeon level
    """
    number_of_monsters = np.random.randint(0, MAX_MONSTERS_PER_ROOM + 1)
    
    for _ in range(number_of_monsters):
        x = np.random.randint(room.x1 + 1, room.x2)
        y = np.random.randint(room.y1 + 1, room.y2)
        
        monster_choice = get_random_choice_from_chances(MONSTER_CHANCES, dungeon_level)
        
        if monster_choice:
            create_func = MONSTER_CHANCES[monster_choice]['create_func']
            create_func(world, x, y)
            logger.debug(f"Spawned {monster_choice} at ({x}, {y})")

def place_items(world: esper.World, room: Rect, dungeon_level: int) -> None:
    """
    Place items in a room.
    
    Args:
        world: The game world
        room: The room to place items in
        dungeon_level: Current dungeon level
    """
    number_of_items = np.random.randint(0, MAX_ITEMS_PER_ROOM + 1)
    
    for _ in range(number_of_items):
        x = np.random.randint(room.x1 + 1, room.x2)
        y = np.random.randint(room.y1 + 1, room.y2)
        
        item_choice = get_random_choice_from_chances(ITEM_CHANCES, dungeon_level)
        
        if item_choice:
            create_func = ITEM_CHANCES[item_choice]['create_func']
            create_func(world, x, y)
            logger.debug(f"Spawned {item_choice} at ({x}, {y})")

def populate_dungeon(world: esper.World, rooms: List[Rect], dungeon_level: int) -> None:
    """
    Populate a dungeon with monsters and items.
    
    Args:
        world: The game world
        rooms: List of rooms to populate
        dungeon_level: Current dungeon level
    """
    # Skip the first room as it's the player's starting room
    for room in rooms[1:]:
        place_monsters(world, room, dungeon_level)
        place_items(world, room, dungeon_level) 