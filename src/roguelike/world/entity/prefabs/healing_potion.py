"""
Healing potion prefab functions.
"""

from typing import Optional

from roguelike.core.constants import Colors
from roguelike.world.entity.components.base import (
    Position, Renderable, Item, Fighter,
    RenderOrder
)

def heal(entity: int, amount: int) -> Optional[str]:
    """
    Heal an entity.
    
    Args:
        entity: Entity to heal
        amount: Amount to heal
        
    Returns:
        Message describing what happened
    """
    fighter = world.component_for_entity(entity, Fighter)
    
    if fighter.hp == fighter.max_hp:
        return "You are already at full health."
    
    fighter.heal(amount)
    return f"Your wounds start to feel better! You heal for {amount} hit points."

def create_healing_potion(world, x: int, y: int) -> int:
    """
    Create a healing potion entity.
    
    Args:
        world: The ECS world
        x: X position
        y: Y position
        
    Returns:
        Healing potion entity ID
    """
    potion = world.create_entity()
    
    world.add_component(potion, Position(x=x, y=y))
    world.add_component(potion, Renderable(
        char='!',
        color=Colors.PURPLE,
        render_order=RenderOrder.ITEM,
        name="Healing Potion"
    ))
    world.add_component(potion, Item(
        name="Healing Potion",
        use_function=lambda entity, **kwargs: heal(entity, 40)
    ))
    
    return potion 