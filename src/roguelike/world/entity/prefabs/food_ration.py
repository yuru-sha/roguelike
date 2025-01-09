from typing import Any, Optional

from roguelike.core.constants import Colors
from roguelike.world.entity.components.base import (
    Position, Renderable, RenderOrder, Item
)

def create_food_ration(world: Any, x: int, y: int) -> int:
    """
    Create a food ration entity.
    
    Args:
        world: The ECS world
        x: X coordinate
        y: Y coordinate
        
    Returns:
        The food ration entity ID
    """
    food = world.create_entity()
    
    world.add_component(food, Position(x, y))
    world.add_component(food, Renderable(
        char='⋆',
        color=Colors.BROWN,
        render_order=RenderOrder.ITEM,
        name="Food Ration"
    ))
    world.add_component(food, Item(
        name="Food Ration",
        use_function=use_food_ration
    ))
    
    return food

def use_food_ration(user: int, world: Any, **kwargs) -> Optional[str]:
    """
    Use a food ration to restore hunger.
    
    Args:
        user: The entity using the food
        world: The ECS world
        
    Returns:
        A message describing what happened
    """
    return "You eat the food ration. It tastes good!" 