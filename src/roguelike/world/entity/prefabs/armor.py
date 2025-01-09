"""
Armor prefab functions.
"""

from typing import Tuple

from roguelike.world.entity.components.base import (Equipment, EquipmentSlot,
                                                    Item, Position, Renderable,
                                                    RenderOrder)


def create_armor(
    world,
    x: int,
    y: int,
    slot: EquipmentSlot,
    name: str,
    defense_bonus: int,
    color: Tuple[int, int, int],
) -> int:
    """
    Create an armor entity.

    Args:
        world: The ECS world
        x: X position
        y: Y position
        slot: Equipment slot
        name: Armor name
        defense_bonus: Defense bonus
        color: Render color

    Returns:
        Armor entity ID
    """
    armor = world.create_entity()

    # Add components
    world.add_component(armor, Position(x=x, y=y))
    world.add_component(
        armor,
        Renderable(char="[", color=color, render_order=RenderOrder.ITEM, name=name),
    )
    world.add_component(armor, Item(name=name))
    world.add_component(
        armor, Equipment(equipment_slot=slot, defense_bonus=defense_bonus)
    )

    return armor
