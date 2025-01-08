# TODO: Add weapon durability system
# TODO: Add weapon enchantment system
# FIXME: Missing Item component in weapon creation
# OPTIMIZE: Weapon type checks could be simplified
# WARNING: Weapon stats might need balancing
# REVIEW: Consider if weapon types should affect attack speed
# HACK: Weapon display characters should be moved to constants

from typing import Any, Tuple

from roguelike.core.constants import Colors
from roguelike.world.entity.components.base import (
    Position, Renderable, RenderOrder,
    Equipment, EquipmentSlot, WeaponType
)

def create_weapon(world: Any, x: int, y: int, name: str, power_bonus: int, weapon_type: WeaponType, color: Tuple[int, int, int] = Colors.LIGHT_GRAY) -> int:
    """
    Create a weapon entity.
    
    Args:
        world: The ECS world
        x: X coordinate
        y: Y coordinate
        name: Weapon name
        power_bonus: Power bonus when equipped
        weapon_type: Type of weapon
        color: Color of the weapon (default: light gray)
        
    Returns:
        The weapon entity ID
    """
    weapon = world.create_entity()
    
    world.add_component(weapon, Position(x, y))
    world.add_component(weapon, Renderable(
        char='/',
        color=color,
        render_order=RenderOrder.ITEM,
        name=name
    ))
    
    # 武器の種類に応じて装備スロットを決定
    slot = EquipmentSlot.MAIN_HAND
    if weapon_type in [WeaponType.TWO_HANDED, WeaponType.BOW, WeaponType.CROSSBOW]:
        slot = EquipmentSlot.MAIN_HAND  # 両手武器は主手のみ
    
    world.add_component(weapon, Equipment(
        slot=slot,
        power_bonus=power_bonus,
        weapon_type=weapon_type
    ))
    
    return weapon 