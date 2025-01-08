from typing import Dict, Any, Tuple
import esper

from roguelike.world.entity.components.base import (
    Position, Renderable, Fighter, AI, Corpse
)
from roguelike.core.constants import Colors

def create_orc(world: esper.World, x: int, y: int) -> int:
    """
    Create an orc entity.
    
    Args:
        world: The game world
        x: X coordinate
        y: Y coordinate
        
    Returns:
        The entity ID
    """
    orc = world.create_entity()
    
    world.add_component(orc, Position(x=x, y=y))
    world.add_component(orc, Renderable(
        char='o',
        color=Colors.GREEN,
        render_order=1
    ))
    world.add_component(orc, Fighter(
        max_hp=10,
        hp=10,
        defense=0,
        power=3,
        xp=35
    ))
    world.add_component(orc, AI())
    world.add_component(orc, Corpse(name="orc"))
    
    return orc

def create_troll(world: esper.World, x: int, y: int) -> int:
    """
    Create a troll entity.
    
    Args:
        world: The game world
        x: X coordinate
        y: Y coordinate
        
    Returns:
        The entity ID
    """
    troll = world.create_entity()
    
    world.add_component(troll, Position(x=x, y=y))
    world.add_component(troll, Renderable(
        char='T',
        color=Colors.RED,
        render_order=1
    ))
    world.add_component(troll, Fighter(
        max_hp=16,
        hp=16,
        defense=1,
        power=4,
        xp=100
    ))
    world.add_component(troll, AI())
    world.add_component(troll, Corpse(name="troll"))
    
    return troll

def create_dragon(world: esper.World, x: int, y: int) -> int:
    """
    Create a dragon entity.
    
    Args:
        world: The game world
        x: X coordinate
        y: Y coordinate
        
    Returns:
        The entity ID
    """
    dragon = world.create_entity()
    
    world.add_component(dragon, Position(x=x, y=y))
    world.add_component(dragon, Renderable(
        char='D',
        color=Colors.RED,
        render_order=1
    ))
    world.add_component(dragon, Fighter(
        max_hp=30,
        hp=30,
        defense=3,
        power=8,
        xp=200
    ))
    world.add_component(dragon, AI())
    world.add_component(dragon, Corpse(name="dragon"))
    
    return dragon

MONSTER_CHANCES: Dict[str, Dict[str, Any]] = {
    'orc': {
        'chance': 80,
        'min_level': 1,
        'max_level': 5,
        'create_func': create_orc
    },
    'troll': {
        'chance': 20,
        'min_level': 3,
        'max_level': 7,
        'create_func': create_troll
    },
    'dragon': {
        'chance': 5,
        'min_level': 5,
        'max_level': None,  # No maximum level
        'create_func': create_dragon
    }
} 