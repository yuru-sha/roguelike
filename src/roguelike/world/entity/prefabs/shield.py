from typing import Any

from roguelike.core.constants import Colors
from roguelike.world.entity.components.base import (
    Position, Renderable, RenderOrder,
    Equipment, EquipmentSlot
)

def create_shield(world: Any, x: int, y: int, name: str, defense_bonus: int) -> int:
    """
    Create a shield entity.
    
    Args:
        world: The ECS world
        x: X coordinate
        y: Y coordinate
        name: Shield name
        defense_bonus: Defense bonus when equipped
        
    Returns:
        The shield entity ID
    """
    shield = world.create_entity()
    
    world.add_component(shield, Position(x, y))
    world.add_component(shield, Renderable(
        char=']',
        color=Colors.BROWN,
        render_order=RenderOrder.ITEM,
        name=name
    ))
    world.add_component(shield, Equipment(
        slot=EquipmentSlot.OFF_HAND,
        defense_bonus=defense_bonus
    ))
    
    return shield 