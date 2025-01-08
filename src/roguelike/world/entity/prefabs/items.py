from typing import Dict, Any, Optional, Callable
import esper

from roguelike.world.entity.components.base import (
    Position, Renderable, Item
)
from roguelike.core.constants import Colors

def create_healing_potion(world: esper.World, x: int, y: int) -> int:
    """
    Create a healing potion entity.
    
    Args:
        world: The game world
        x: X coordinate
        y: Y coordinate
        
    Returns:
        The entity ID
    """
    potion = world.create_entity()
    
    world.add_component(potion, Position(x=x, y=y))
    world.add_component(potion, Renderable(
        char='!',
        color=Colors.BLUE,
        render_order=0
    ))
    world.add_component(potion, Item(
        use_function=lambda user: user.get_component(Fighter).heal(4),
        targeting=False,
        consumable=True
    ))
    
    return potion

def create_lightning_scroll(world: esper.World, x: int, y: int) -> int:
    """
    Create a lightning scroll entity.
    
    Args:
        world: The game world
        x: X coordinate
        y: Y coordinate
        
    Returns:
        The entity ID
    """
    scroll = world.create_entity()
    
    world.add_component(scroll, Position(x=x, y=y))
    world.add_component(scroll, Renderable(
        char='?',
        color=Colors.YELLOW,
        render_order=0
    ))
    world.add_component(scroll, Item(
        use_function=None,  # Will be set by game logic
        targeting=True,
        targeting_message="Left-click an enemy to strike it with lightning",
        consumable=True
    ))
    
    return scroll

def create_fireball_scroll(world: esper.World, x: int, y: int) -> int:
    """
    Create a fireball scroll entity.
    
    Args:
        world: The game world
        x: X coordinate
        y: Y coordinate
        
    Returns:
        The entity ID
    """
    scroll = world.create_entity()
    
    world.add_component(scroll, Position(x=x, y=y))
    world.add_component(scroll, Renderable(
        char='?',
        color=Colors.RED,
        render_order=0
    ))
    world.add_component(scroll, Item(
        use_function=None,  # Will be set by game logic
        targeting=True,
        targeting_message="Left-click a target tile for the fireball",
        consumable=True
    ))
    
    return scroll

def create_confusion_scroll(world: esper.World, x: int, y: int) -> int:
    """
    Create a confusion scroll entity.
    
    Args:
        world: The game world
        x: X coordinate
        y: Y coordinate
        
    Returns:
        The entity ID
    """
    scroll = world.create_entity()
    
    world.add_component(scroll, Position(x=x, y=y))
    world.add_component(scroll, Renderable(
        char='?',
        color=Colors.GREEN,
        render_order=0
    ))
    world.add_component(scroll, Item(
        use_function=None,  # Will be set by game logic
        targeting=True,
        targeting_message="Left-click an enemy to confuse it",
        consumable=True
    ))
    
    return scroll

ITEM_CHANCES: Dict[str, Dict[str, Any]] = {
    'healing_potion': {
        'chance': 70,
        'min_level': 1,
        'max_level': None,
        'create_func': create_healing_potion
    },
    'lightning_scroll': {
        'chance': 10,
        'min_level': 4,
        'max_level': None,
        'create_func': create_lightning_scroll
    },
    'fireball_scroll': {
        'chance': 10,
        'min_level': 6,
        'max_level': None,
        'create_func': create_fireball_scroll
    },
    'confusion_scroll': {
        'chance': 10,
        'min_level': 2,
        'max_level': None,
        'create_func': create_confusion_scroll
    }
} 