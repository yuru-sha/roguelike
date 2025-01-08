"""
Item prefab functions.
"""

from typing import Dict, Any, List, Tuple, Optional
import random

from roguelike.core.constants import Colors
from roguelike.world.entity.components.base import (
    Position, Renderable, Item, Equipment,
    RenderOrder, EquipmentSlot, WeaponType
)

def create_healing_potion(world, x: int, y: int) -> int:
    """Create a healing potion."""
    potion = world.create_entity()
    
    world.add_component(potion, Position(x=x, y=y))
    world.add_component(potion, Renderable(
        char='!',
        color=Colors.VIOLET,
        render_order=RenderOrder.ITEM,
        name="Healing Potion"
    ))
    world.add_component(potion, Item(
        name="Healing Potion",
        use_function=lambda entity, **kwargs: heal(entity, 40)
    ))
    
    return potion

def create_lightning_scroll(world, x: int, y: int) -> int:
    """Create a lightning scroll."""
    scroll = world.create_entity()
    
    world.add_component(scroll, Position(x=x, y=y))
    world.add_component(scroll, Renderable(
        char='?',
        color=Colors.YELLOW,
        render_order=RenderOrder.ITEM,
        name="Lightning Scroll"
    ))
    world.add_component(scroll, Item(
        name="Lightning Scroll",
        use_function=lambda entity, **kwargs: cast_lightning(entity, damage=40, maximum_range=5)
    ))
    
    return scroll

def create_fireball_scroll(world, x: int, y: int) -> int:
    """Create a fireball scroll."""
    scroll = world.create_entity()
    
    world.add_component(scroll, Position(x=x, y=y))
    world.add_component(scroll, Renderable(
        char='?',
        color=Colors.RED,
        render_order=RenderOrder.ITEM,
        name="Fireball Scroll"
    ))
    world.add_component(scroll, Item(
        name="Fireball Scroll",
        use_function=lambda entity, **kwargs: cast_fireball(entity, damage=25, radius=3),
        targeting=True,
        targeting_message="Left-click a target tile for the fireball, or right-click to cancel."
    ))
    
    return scroll

def create_confusion_scroll(world, x: int, y: int) -> int:
    """Create a confusion scroll."""
    scroll = world.create_entity()
    
    world.add_component(scroll, Position(x=x, y=y))
    world.add_component(scroll, Renderable(
        char='?',
        color=Colors.LIGHT_PINK,
        render_order=RenderOrder.ITEM,
        name="Confusion Scroll"
    ))
    world.add_component(scroll, Item(
        name="Confusion Scroll",
        use_function=lambda entity, **kwargs: cast_confuse(entity, turns=10),
        targeting=True,
        targeting_message="Left-click an enemy to confuse it, or right-click to cancel."
    ))
    
    return scroll

def create_armor(world, x: int, y: int, slot: EquipmentSlot, name: str, defense_bonus: int, color: Tuple[int, int, int]) -> int:
    """Create an armor item."""
    armor = world.create_entity()
    
    world.add_component(armor, Position(x=x, y=y))
    world.add_component(armor, Renderable(
        char='[',
        color=color,
        render_order=RenderOrder.ITEM,
        name=name
    ))
    world.add_component(armor, Item(name=name))
    world.add_component(armor, Equipment(
        equipment_slot=slot,
        defense_bonus=defense_bonus
    ))
    
    return armor

def create_weapon(world, x: int, y: int, name: str, power_bonus: int, weapon_type: WeaponType, color: Tuple[int, int, int]) -> int:
    """Create a weapon item."""
    weapon = world.create_entity()
    
    world.add_component(weapon, Position(x=x, y=y))
    world.add_component(weapon, Renderable(
        char=')',
        color=color,
        render_order=RenderOrder.ITEM,
        name=name
    ))
    world.add_component(weapon, Item(name=name))
    world.add_component(weapon, Equipment(
        equipment_slot=EquipmentSlot.MAIN_HAND,
        power_bonus=power_bonus,
        weapon_type=weapon_type
    ))
    
    return weapon

def create_shield(world, x: int, y: int, name: str, defense_bonus: int, color: Tuple[int, int, int] = Colors.LIGHT_GRAY) -> int:
    """Create a shield item."""
    shield = world.create_entity()
    
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

def create_food_ration(world, x: int, y: int) -> int:
    """Create a food ration."""
    food = world.create_entity()
    
    world.add_component(food, Position(x=x, y=y))
    world.add_component(food, Renderable(
        char='%',
        color=Colors.BROWN,
        render_order=RenderOrder.ITEM,
        name="Food Ration"
    ))
    world.add_component(food, Item(
        name="Food Ration",
        use_function=lambda entity, **kwargs: eat_food(entity, nutrition=500)
    ))
    
    return food

# Item chances by floor
ITEM_CHANCES: Dict[str, Dict[str, Any]] = {
    'healing_potion': {
        'chance': 35,
        'create_function': lambda w, x, y: create_healing_potion(w, x, y)
    },
    'lightning_scroll': {
        'chance': 25,
        'create_function': lambda w, x, y: create_lightning_scroll(w, x, y)
    },
    'fireball_scroll': {
        'chance': 25,
        'create_function': lambda w, x, y: create_fireball_scroll(w, x, y)
    },
    'confusion_scroll': {
        'chance': 10,
        'create_function': lambda w, x, y: create_confusion_scroll(w, x, y)
    },
    'leather_armor': {
        'chance': 15,
        'create_function': lambda w, x, y: create_armor(w, x, y, EquipmentSlot.BODY, "Leather Armor", 1, Colors.BROWN)
    },
    'chain_mail': {
        'chance': 10,
        'create_function': lambda w, x, y: create_armor(w, x, y, EquipmentSlot.BODY, "Chain Mail", 2, Colors.LIGHT_GRAY)
    },
    'plate_armor': {
        'chance': 5,
        'create_function': lambda w, x, y: create_armor(w, x, y, EquipmentSlot.BODY, "Plate Armor", 3, Colors.SILVER)
    },
    'dagger': {
        'chance': 15,
        'create_function': lambda w, x, y: create_weapon(w, x, y, "Dagger", 2, WeaponType.ONE_HANDED, Colors.LIGHT_GRAY)
    },
    'sword': {
        'chance': 10,
        'create_function': lambda w, x, y: create_weapon(w, x, y, "Sword", 3, WeaponType.ONE_HANDED, Colors.LIGHT_GRAY)
    },
    'great_sword': {
        'chance': 5,
        'create_function': lambda w, x, y: create_weapon(w, x, y, "Great Sword", 4, WeaponType.TWO_HANDED, Colors.LIGHT_GRAY)
    },
    'wooden_shield': {
        'chance': 15,
        'create_function': lambda w, x, y: create_shield(w, x, y, "Wooden Shield", 1)
    },
    'iron_shield': {
        'chance': 10,
        'create_function': lambda w, x, y: create_shield(w, x, y, "Iron Shield", 2)
    },
    'tower_shield': {
        'chance': 5,
        'create_function': lambda w, x, y: create_shield(w, x, y, "Tower Shield", 3)
    },
    'food_ration': {
        'chance': 35,
        'create_function': lambda w, x, y: create_food_ration(w, x, y)
    }
} 