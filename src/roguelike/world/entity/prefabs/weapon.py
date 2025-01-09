"""
Weapon prefab functions.
"""

from typing import Tuple

from roguelike.world.entity.components.base import (Equipment, EquipmentSlot,
                                                    Item, Position, Renderable,
                                                    RenderOrder, WeaponType)


def create_weapon(
    world,
    x: int,
    y: int,
    name: str,
    power_bonus: int,
    weapon_type: WeaponType,
    color: Tuple[int, int, int],
) -> int:
    """
    Create a weapon entity.

    Args:
        world: The ECS world
        x: X position
        y: Y position
        name: Weapon name
        power_bonus: Power bonus
        weapon_type: Type of weapon
        color: Render color

    Returns:
        Weapon entity ID
    """
    weapon = world.create_entity()

    # Add components
    world.add_component(weapon, Position(x=x, y=y))
    world.add_component(
        weapon,
        Renderable(char=")", color=color, render_order=RenderOrder.ITEM, name=name),
    )
    world.add_component(weapon, Item(name=name))
    world.add_component(
        weapon,
        Equipment(
            equipment_slot=EquipmentSlot.MAIN_HAND,
            power_bonus=power_bonus,
            weapon_type=weapon_type,
        ),
    )

    return weapon
