# TODO: Add armor durability system
# TODO: Add armor enchantment system
# FIXME: Missing Item component in armor creation
# OPTIMIZE: Armor slot validation could be added
# WARNING: Armor stats might need balancing
# REVIEW: Consider if armor should affect movement speed
# HACK: Armor display characters should be moved to constants

from typing import Any, Tuple

from roguelike.core.constants import Colors
from roguelike.world.entity.components.base import (
    Position, Renderable, RenderOrder,
    Equipment, EquipmentSlot
)

def create_armor(world: Any, x: int, y: int, slot: EquipmentSlot, name: str, defense_bonus: int, color: Tuple[int, int, int] = Colors.LIGHT_GRAY) -> int:
    """
    Create an armor entity.
    
    Args:
        world: The ECS world
        x: X coordinate
        y: Y coordinate
        slot: Equipment slot for the armor
        name: Armor name
        defense_bonus: Defense bonus when equipped
        color: Color of the armor (default: light gray)
        
    Returns:
        The armor entity ID
    """
    armor = world.create_entity()
    
    world.add_component(armor, Position(x, y))
    world.add_component(armor, Renderable(
        char='[',
        color=color,
        render_order=RenderOrder.ITEM,
        name=name
    ))
    world.add_component(armor, Equipment(
        slot=slot,
        defense_bonus=defense_bonus
    ))
    
    return armor 