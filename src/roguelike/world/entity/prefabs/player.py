"""
Player entity prefab.
"""


from typing import Any, Tuple

from roguelike.core.constants import (PLAYER_DEFENSE, PLAYER_HP,
                                      PLAYER_INVENTORY_CAPACITY, PLAYER_POWER,
                                      PLAYER_XP, Colors)
from roguelike.world.entity.components.base import (EquipmentSlot,
                                                    EquipmentSlots, Fighter,
                                                    Inventory, Level, Position,
                                                    Renderable, RenderOrder,
                                                    WeaponType)
from roguelike.world.entity.prefabs.armor import create_armor
from roguelike.world.entity.prefabs.food_ration import create_food_ration
from roguelike.world.entity.prefabs.healing_potion import create_healing_potion
from roguelike.world.entity.prefabs.scroll import (create_identify_scroll,
                                                   create_teleport_scroll)
from roguelike.world.entity.prefabs.shield import create_shield
from roguelike.world.entity.prefabs.weapon import create_weapon


def create_player(world: Any, x: int, y: int) -> int:
    """
    Create the player entity.

    Args:
        world: The ECS world
        x: X coordinate
        y: Y coordinate

    Returns:
        The player entity ID
    """
    player = world.create_entity()

    world.add_component(player, Position(x, y))
    world.add_component(
        player,
        Renderable(
            char="@", color=Colors.WHITE, render_order=RenderOrder.ACTOR, name="Player"
        ),
    )
    world.add_component(player, Fighter(hp=100, max_hp=100, defense=1, power=2))
    world.add_component(player, Inventory(26))  # 26スロット（a-z）
    world.add_component(player, EquipmentSlots())

    # 初期装備の作成と装備
    # 武器
    dagger = create_weapon(
        world, 0, 0, "Dagger", 2, WeaponType.ONE_HANDED, Colors.LIGHT_GRAY
    )
    bow = create_weapon(world, 0, 0, "Short Bow", 2, WeaponType.BOW, Colors.BROWN)

    # 防具
    leather_armor = create_armor(
        world, 0, 0, EquipmentSlot.BODY, "Leather Armor", 1, Colors.BROWN
    )
    wooden_shield = create_shield(world, 0, 0, "Wooden Shield", 1)

    # 消耗品
    healing_potions = [create_healing_potion(world, 0, 0) for _ in range(2)]
    scrolls = [create_identify_scroll(world, 0, 0), create_teleport_scroll(world, 0, 0)]
    food_rations = [create_food_ration(world, 0, 0) for _ in range(3)]

    # インベントリに追加
    inventory = world.component_for_entity(player, Inventory)
    equipment_slots = world.component_for_entity(player, EquipmentSlots)

    # 装備品を装備
    equipment_slots.equip(EquipmentSlot.MAIN_HAND, dagger, world)
    inventory.add_item(bow)
    equipment_slots.equip(EquipmentSlot.BODY, leather_armor, world)
    equipment_slots.equip(EquipmentSlot.OFF_HAND, wooden_shield, world)

    # 消耗品をインベントリに追加
    for potion in healing_potions:
        inventory.add_item(potion)
    for scroll in scrolls:
        inventory.add_item(scroll)
    for food in food_rations:
        inventory.add_item(food)

    return player


def level_up_player(world: Any, player: int) -> None:
    """
    Level up the player entity.

    Args:
        world: The ECS world
        player: The player entity ID
    """
    fighter = world.component_for_entity(player, Fighter)

    # Increase stats
    fighter.max_hp += 20
    fighter.hp = fighter.max_hp
    fighter.defense += 1
    fighter.power += 1
