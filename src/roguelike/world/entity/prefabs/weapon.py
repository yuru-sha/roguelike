"""
Weapon prefabs for the game.
"""

from typing import Any, Dict, Optional, Tuple
import random

from roguelike.world.entity.components.base import (
    Item,
    Position,
    Renderable,
)
from roguelike.world.entity.components.equipment import Equipment
from roguelike.world.entity.components.identification import Identifiable, ItemType
from roguelike.core.constants import RenderOrder, EquipmentSlot, WeaponType


# 武器の基本パラメータ（Rogueの仕様に完全準拠）
WEAPON_STATS = {
    "dagger": {
        "type": WeaponType.ONE_HANDED,
        "damage": (1, 4),  # 1d4
        "hit_bonus": 0,
    },
    "mace": {
        "type": WeaponType.ONE_HANDED,
        "damage": (2, 4),  # 2d4
        "hit_bonus": 0,
    },
    "short sword": {
        "type": WeaponType.ONE_HANDED,
        "damage": (2, 5),  # 2d5
        "hit_bonus": 0,
    },
    "long sword": {
        "type": WeaponType.ONE_HANDED,
        "damage": (1, 6),  # 1d6
        "hit_bonus": 0,
    },
    "two-handed sword": {
        "type": WeaponType.TWO_HANDED,
        "damage": (2, 6),  # 2d6
        "hit_bonus": 0,
    },
}

# Rogueの仕様：魔法の武器の出現確率は一律7%
MAGIC_WEAPON_CHANCE = 0.07


def roll_damage(dice_count: int, dice_sides: int) -> int:
    """Roll dice for damage calculation."""
    return sum(random.randint(1, dice_sides) for _ in range(dice_count))


def create_weapon(
    world: Any,
    x: int,
    y: int,
    name: str,
    weapon_type: WeaponType,
    damage: Tuple[int, int],  # (dice_count, dice_sides)
    hit_bonus: int = 0,
    enchantment: int = 0,
    cursed: bool = False,
) -> int:
    """Create a weapon with the given parameters."""
    weapon = world.create_entity()

    # 呪われた武器は必ず負のエンチャントを持つ（Rogueの仕様）
    if cursed:
        enchantment = -random.randint(1, 3)

    # 武器の名前を設定（未識別の場合は単なる武器名）
    display_name = name
    if enchantment != 0:
        sign = "" if enchantment < 0 else "+"
        display_name = f"{name} {sign}{enchantment}"

    world.add_component(weapon, Position(x=x, y=y))
    world.add_component(
        weapon,
        Renderable(
            char=")",
            color=(255, 0, 0) if cursed else (255, 255, 255),
            render_order=RenderOrder.ITEM,
            name=display_name,
        ),
    )
    world.add_component(
        weapon,
        Item(
            name=name,
            description=f"A {name.lower()}.",
        ),
    )
    world.add_component(
        weapon,
        Equipment(
            slot=EquipmentSlot.MAIN_HAND,
            power_bonus=0,  # 基本攻撃力は0（ダメージはダイスロールで決定）
            weapon_type=weapon_type,
            enchantment=enchantment,
            cursed=cursed,
            hits_to_identify=random.randint(8, 12),  # Rogueでは使用回数がランダム
            damage_dice=damage,  # ダメージダイスを保存
            hit_bonus=hit_bonus,  # 命中修正値
        ),
    )
    world.add_component(
        weapon,
        Identifiable(
            item_type=ItemType.WEAPON,
            true_name=display_name,
            appearance=name,  # 未識別時は基本名のみ
        ),
    )

    return weapon


def create_magic_weapon(
    world: Any, x: int, y: int, base_weapon_func: Any, enchantment: Optional[int] = None
) -> int:
    """Create an enchanted version of a weapon."""
    weapon = base_weapon_func(world, x, y)
    
    # Rogueの仕様：
    # - エンチャント値は+1から+3（呪われている場合は-1から-3）
    # - 5%の確率で呪われている
    cursed = random.random() < 0.05
    if enchantment is None:
        enchantment = random.randint(1, 3)
    
    equipment = world.component_for_entity(weapon, Equipment)
    equipment.enchantment = -abs(enchantment) if cursed else abs(enchantment)
    equipment.cursed = cursed
    
    # 名前を更新（Rogueの表記に合わせる）
    renderable = world.component_for_entity(weapon, Renderable)
    base_name = renderable.name
    if cursed:
        renderable.name = f"{base_name} {equipment.enchantment}"  # 例: "dagger -2"
    else:
        renderable.name = f"{base_name} +{equipment.enchantment}"  # 例: "dagger +1"
    
    # Identifiableコンポーネントも更新
    identifiable = world.component_for_entity(weapon, Identifiable)
    identifiable.true_name = renderable.name
    identifiable.appearance = base_name  # 未識別時は基本名のみ
    
    return weapon


def create_dagger(world: Any, x: int, y: int, cursed: bool = False) -> int:
    """Create a dagger entity."""
    stats = WEAPON_STATS["dagger"]
    # 魔法の武器判定
    if not cursed and random.random() < MAGIC_WEAPON_CHANCE:
        return create_magic_weapon(
            world,
            x,
            y,
            lambda w, x, y: create_weapon(
                w, x, y, "dagger",
                weapon_type=stats["type"],
                damage=stats["damage"],
                hit_bonus=stats["hit_bonus"],
            ),
        )
    return create_weapon(
        world,
        x,
        y,
        "dagger",
        weapon_type=stats["type"],
        damage=stats["damage"],
        hit_bonus=stats["hit_bonus"],
        cursed=cursed,
    )


def create_short_sword(world: Any, x: int, y: int, cursed: bool = False) -> int:
    """Create a short sword entity."""
    stats = WEAPON_STATS["short sword"]
    if not cursed and random.random() < MAGIC_WEAPON_CHANCE:
        return create_magic_weapon(
            world,
            x,
            y,
            lambda w, x, y: create_weapon(
                w, x, y, "short sword",
                weapon_type=stats["type"],
                damage=stats["damage"],
                hit_bonus=stats["hit_bonus"],
            ),
        )
    return create_weapon(
        world,
        x,
        y,
        "short sword",
        weapon_type=stats["type"],
        damage=stats["damage"],
        hit_bonus=stats["hit_bonus"],
        cursed=cursed,
    )


def create_long_sword(world: Any, x: int, y: int, cursed: bool = False) -> int:
    """Create a long sword entity."""
    stats = WEAPON_STATS["long sword"]
    if not cursed and random.random() < MAGIC_WEAPON_CHANCE:
        return create_magic_weapon(
            world,
            x,
            y,
            lambda w, x, y: create_weapon(
                w, x, y, "long sword",
                weapon_type=stats["type"],
                damage=stats["damage"],
                hit_bonus=stats["hit_bonus"],
            ),
        )
    return create_weapon(
        world,
        x,
        y,
        "long sword",
        weapon_type=stats["type"],
        damage=stats["damage"],
        hit_bonus=stats["hit_bonus"],
        cursed=cursed,
    )


def create_two_handed_sword(world: Any, x: int, y: int, cursed: bool = False) -> int:
    """Create a two-handed sword entity."""
    stats = WEAPON_STATS["two-handed sword"]
    if not cursed and random.random() < MAGIC_WEAPON_CHANCE:
        return create_magic_weapon(
            world,
            x,
            y,
            lambda w, x, y: create_weapon(
                w, x, y, "two-handed sword",
                weapon_type=stats["type"],
                damage=stats["damage"],
                hit_bonus=stats["hit_bonus"],
            ),
        )
    return create_weapon(
        world,
        x,
        y,
        "two-handed sword",
        weapon_type=stats["type"],
        damage=stats["damage"],
        hit_bonus=stats["hit_bonus"],
        cursed=cursed,
    )


def create_mace(world: Any, x: int, y: int, cursed: bool = False) -> int:
    """Create a mace entity."""
    stats = WEAPON_STATS["mace"]
    if not cursed and random.random() < MAGIC_WEAPON_CHANCE:
        return create_magic_weapon(
            world,
            x,
            y,
            lambda w, x, y: create_weapon(
                w, x, y, "mace",
                weapon_type=stats["type"],
                damage=stats["damage"],
                hit_bonus=stats["hit_bonus"],
            ),
        )
    return create_weapon(
        world,
        x,
        y,
        "mace",
        weapon_type=stats["type"],
        damage=stats["damage"],
        hit_bonus=stats["hit_bonus"],
        cursed=cursed,
    )
