"""
Shield prefab functions.
"""

from typing import Tuple

from roguelike.core.constants import Colors
from roguelike.world.entity.components.base import (
    Position, Renderable, Item, Equipment,
    RenderOrder, EquipmentSlot
)

def create_shield(
    world,
    x: int,
    y: int,
    name: str,
    defense_bonus: int,
    color: Tuple[int, int, int] = Colors.LIGHT_GRAY
) -> int:
    """
    Create a shield entity.
    
    Args:
        world: The ECS world
        x: X position
        y: Y position
        name: Shield name
        defense_bonus: Defense bonus
        color: Render color
        
    Returns:
        Shield entity ID
    """
    shield = world.create_entity()
    
    # Add components
    world.add_component(shield, Position(x=x, y=y))
    world.add_component(shield, Renderable(
        char=']',
        color=color,
        render_order=RenderOrder.ITEM,
        name=name
    ))
    world.add_component(shield, Item(name=name))
    world.add_component(shield, Equipment(
        equipment_slot=EquipmentSlot.OFF_HAND,
        defense_bonus=defense_bonus
    ))
    
    return shield 