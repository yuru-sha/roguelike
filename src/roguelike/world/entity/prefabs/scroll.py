"""
Scroll prefabs for the game.
"""

from typing import Any, Dict, Optional
import random

from roguelike.world.entity.components.base import (
    Consumable,
    Item,
    Position,
    Renderable,
)
from roguelike.world.entity.components.identification import Identifiable, ItemType
from roguelike.world.entity.components.equipment import Equipment, EquipmentSlots
from roguelike.core.constants import RenderOrder, EquipmentSlot


# 巻物の種類と出現確率（Rogueの仕様に合わせる）
SCROLL_TYPES = {
    "identify": {
        "name": "scroll of identify",
        "chance": 0.25,  # 25%の確率で出現
        "appearance": [
            "ZELGO MER",
            "JUYED AWK YACC",
            "NR 9",
            "XIXAXA XOXAXA XUXAXA",
            "PRATYAVAYAH",
            "DAIYEN FOOELS",
        ],
    },
    "enchant_weapon": {
        "name": "scroll of enchant weapon",
        "chance": 0.15,  # 15%の確率で出現
        "appearance": [
            "TEMOV",
            "ANDOVA BEGARIN",
            "DUP DUP",
            "XLARG QASX",
            "RZEH",
            "GHAHGH",
        ],
    },
    "remove_curse": {
        "name": "scroll of remove curse",
        "chance": 0.10,  # 10%の確率で出現
        "appearance": [
            "FOOBIE BLETCH",
            "HACKEM MUCHE",
            "KERNOD WEL",
            "ELAM EBOW",
            "VERR YED HORRE",
            "READ ME",
        ],
    },
}


def _create_scroll_base(
    world: Any, x: int, y: int, scroll_type: str, appearance: Optional[str] = None
) -> int:
    """Create a base scroll entity."""
    scroll = world.create_entity()
    scroll_data = SCROLL_TYPES[scroll_type]

    # 未識別時の表示をランダムに選択
    if appearance is None:
        appearance = random.choice(scroll_data["appearance"])

    world.add_component(scroll, Position(x=x, y=y))
    world.add_component(
        scroll,
        Renderable(
            char="?",
            color=(255, 255, 255),
            render_order=RenderOrder.ITEM,
            name=scroll_data["name"],
        ),
    )
    world.add_component(
        scroll,
        Item(
            name=scroll_data["name"],
            description=f"A scroll labeled '{appearance}'.",
            targeting=True if scroll_type in ["identify", "enchant_weapon"] else False,
            targeting_message="Select an item to identify."
            if scroll_type == "identify"
            else "Select a weapon to enchant."
            if scroll_type == "enchant_weapon"
            else "",
        ),
    )
    world.add_component(
        scroll,
        Identifiable(
            item_type=ItemType.SCROLL,
            true_name=scroll_data["name"],
            appearance=f"scroll labeled '{appearance}'",
        ),
    )

    return scroll


def create_identify_scroll(world: Any, x: int, y: int, appearance: Optional[str] = None) -> int:
    """Create a scroll of identify."""
    scroll = _create_scroll_base(world, x, y, "identify", appearance)

    def identify_item(user: int, target: int, world: Any) -> bool:
        """Identify the target item."""
        if not world.has_component(target, Identifiable):
            return False

        identifiable = world.component_for_entity(target, Identifiable)
        if identifiable.is_identified:
            return False

        identifiable.identify()
        return True

    world.add_component(
        scroll,
        Consumable(
            use_function=identify_item,
            targeting=True,
            auto_identify=True,  # 識別の巻物は使用時に自動識別
        ),
    )

    return scroll


def create_enchant_scroll(world: Any, x: int, y: int, appearance: Optional[str] = None) -> int:
    """Create a scroll of enchant weapon."""
    scroll = _create_scroll_base(world, x, y, "enchant_weapon", appearance)

    def enchant_weapon(user: int, target: int, world: Any) -> bool:
        """Enchant the target weapon."""
        if not world.has_component(target, Equipment):
            return False

        equipment = world.component_for_entity(target, Equipment)
        if equipment.slot != EquipmentSlot.MAIN_HAND or not equipment.weapon_type:
            return False

        # Rogueの仕様：エンチャントは+3まで
        if equipment.enchantment >= 3:
            return False

        # Rogueの仕様：呪われた武器は強化できない
        if equipment.cursed:
            return False

        equipment.enchantment += 1
        if world.has_component(target, Identifiable):
            identifiable = world.component_for_entity(target, Identifiable)
            identifiable.identify()  # 武器は強化時に識別される

            # 名前を更新
            renderable = world.component_for_entity(target, Renderable)
            renderable.name = f"{renderable.name.split(' ')[0]} +{equipment.enchantment}"
            identifiable.true_name = renderable.name

        return True

    world.add_component(
        scroll,
        Consumable(
            use_function=enchant_weapon,
            targeting=True,
            auto_identify=True,
        ),
    )

    return scroll


def create_remove_curse_scroll(world: Any, x: int, y: int, appearance: Optional[str] = None) -> int:
    """Create a scroll of remove curse."""
    scroll = _create_scroll_base(world, x, y, "remove_curse", appearance)

    def remove_curse(user: int, world: Any) -> bool:
        """Remove curses from all equipped items."""
        if not world.has_component(user, EquipmentSlots):
            return False

        equipment_slots = world.component_for_entity(user, EquipmentSlots)
        cursed_items_found = False

        # 装備中のアイテムの呪いを解除
        for slot in equipment_slots.slots.values():
            if slot is None:
                continue

            if world.has_component(slot, Equipment):
                equipment = world.component_for_entity(slot, Equipment)
                if equipment.cursed:
                    equipment.cursed = False
                    cursed_items_found = True
                    # 呪いが解けた時点でそのアイテムは識別される
                    if world.has_component(slot, Identifiable):
                        identifiable = world.component_for_entity(slot, Identifiable)
                        identifiable.identify()

                        # 名前を更新
                        renderable = world.component_for_entity(slot, Renderable)
                        base_name = renderable.name.split(" ")[0]
                        if equipment.enchantment != 0:
                            sign = "" if equipment.enchantment < 0 else "+"
                            renderable.name = f"{base_name} {sign}{equipment.enchantment}"
                        else:
                            renderable.name = base_name
                        identifiable.true_name = renderable.name

        return cursed_items_found

    world.add_component(
        scroll,
        Consumable(
            use_function=remove_curse,
            auto_identify=True,
        ),
    )

    return scroll


def create_random_scroll(world: Any, x: int, y: int) -> int:
    """Create a random scroll based on the probability distribution."""
    scroll_type = random.choices(
        list(SCROLL_TYPES.keys()),
        weights=[data["chance"] for data in SCROLL_TYPES.values()],
    )[0]

    if scroll_type == "identify":
        return create_identify_scroll(world, x, y)
    elif scroll_type == "enchant_weapon":
        return create_enchant_scroll(world, x, y)
    else:  # remove_curse
        return create_remove_curse_scroll(world, x, y)
