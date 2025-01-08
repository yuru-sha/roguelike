from typing import Any, Optional

from roguelike.core.constants import Colors
from roguelike.world.entity.components.base import (
    Position, Renderable, RenderOrder,
    Item, Fighter
)

def create_healing_potion(world: Any, x: int, y: int) -> int:
    """
    Create a healing potion entity.
    
    Args:
        world: The ECS world
        x: X coordinate
        y: Y coordinate
        
    Returns:
        The healing potion entity ID
    """
    potion = world.create_entity()
    
    world.add_component(potion, Position(x, y))
    world.add_component(potion, Renderable(
        char='!',
        color=Colors.MAGENTA,
        render_order=RenderOrder.ITEM,
        name="Healing Potion"
    ))
    world.add_component(potion, Item(
        name="Healing Potion",
        use_function=use_healing_potion,
        use_args={'amount': 40}
    ))
    
    return potion

def use_healing_potion(user: int, world: Any, **kwargs) -> Optional[str]:
    """
    Use a healing potion to restore HP.
    
    Args:
        user: The entity using the potion
        world: The ECS world
        
    Returns:
        A message describing what happened
    """
    amount = kwargs.get('amount', 0)
    fighter = world.component_for_entity(user, Fighter)
    
    if fighter.hp == fighter.max_hp:
        return "You are already at full health!"
    
    fighter.heal(amount)
    return f"Your wounds start to feel better! You recover {amount} HP." 