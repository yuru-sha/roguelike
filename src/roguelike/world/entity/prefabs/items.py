# TODO: Add item identification system for unidentified items
# TODO: Add item durability system
# TODO: Add item enchantment system
# FIXME: Ring and necklace creation functions are missing Item name parameter
# OPTIMIZE: Item chance calculations could be cached
# WARNING: Amulet of Yendor stats might need balancing
# REVIEW: Consider if weapon types should affect damage calculation
# HACK: Magic numbers in item stats should be moved to constants

from typing import Dict, Any, Optional, Callable, Tuple

from roguelike.core.constants import Colors
from roguelike.world.entity.components.base import (
    Position, Item, Renderable, RenderOrder, Fighter, AI, Equipment, EquipmentSlot, WeaponType
)

# Add MAGENTA color
Colors.MAGENTA = (255, 0, 255)  # Bright purple/magenta color

def create_healing_potion(world: Any, x: int, y: int) -> int:
    """
    Create a healing potion entity.
    
    Args:
        world: The ECS world
        x: X coordinate
        y: Y coordinate
        
    Returns:
        The entity ID
    """
    potion = world.create_entity()
    
    world.add_component(potion, Position(x, y))
    world.add_component(potion, Renderable(
        char='!',
        color=Colors.MAGENTA,
        render_order=RenderOrder.ITEM,
        name="Healing Potion"
    ))
    world.add_component(potion, Item(
        name="Healing Potion",
        use_function=use_healing_potion,
        use_args={'amount': 40}
    ))
    
    return potion

def create_lightning_scroll(world: Any, x: int, y: int) -> int:
    """
    Create a lightning scroll entity.
    
    Args:
        world: The ECS world
        x: X coordinate
        y: Y coordinate
        
    Returns:
        The entity ID
    """
    scroll = world.create_entity()
    
    world.add_component(scroll, Position(x, y))
    world.add_component(scroll, Renderable(
        char='?',
        color=Colors.YELLOW,
        render_order=RenderOrder.ITEM,
        name="Lightning Scroll"
    ))
    world.add_component(scroll, Item(
        name="Lightning Scroll",
        use_function=use_lightning,
        use_args={'damage': 40, 'maximum_range': 5}
    ))
    
    return scroll

def create_fireball_scroll(world: Any, x: int, y: int) -> int:
    """
    Create a fireball scroll entity.
    
    Args:
        world: The ECS world
        x: X coordinate
        y: Y coordinate
        
    Returns:
        The entity ID
    """
    scroll = world.create_entity()
    
    world.add_component(scroll, Position(x, y))
    world.add_component(scroll, Renderable(
        char='?',
        color=Colors.RED,
        render_order=RenderOrder.ITEM,
        name="Fireball Scroll"
    ))
    world.add_component(scroll, Item(
        name="Fireball Scroll",
        use_function=use_fireball,
        targeting=True,
        targeting_message="Left-click a target tile for the fireball, or right-click to cancel.",
        use_args={'damage': 25, 'radius': 3}
    ))
    
    return scroll

def create_confusion_scroll(world: Any, x: int, y: int) -> int:
    """
    Create a confusion scroll entity.
    
    Args:
        world: The ECS world
        x: X coordinate
        y: Y coordinate
        
    Returns:
        The entity ID
    """
    scroll = world.create_entity()
    
    world.add_component(scroll, Position(x, y))
    world.add_component(scroll, Renderable(
        char='?',
        color=Colors.BLUE,
        render_order=RenderOrder.ITEM,
        name="Confusion Scroll"
    ))
    world.add_component(scroll, Item(
        name="Confusion Scroll",
        use_function=use_confusion,
        targeting=True,
        targeting_message="Left-click an enemy to confuse it, or right-click to cancel.",
        use_args={'turns': 10}
    ))
    
    return scroll

def create_amulet_of_yendor(world: Any, x: int, y: int) -> int:
    """
    Create the Amulet of Yendor entity.
    
    Args:
        world: The ECS world
        x: X coordinate
        y: Y coordinate
        
    Returns:
        The entity ID
    """
    amulet = world.create_entity()
    
    world.add_component(amulet, Position(x, y))
    world.add_component(amulet, Renderable(
        char='"',
        color=Colors.YELLOW,
        render_order=RenderOrder.ITEM,
        name="The Amulet of Yendor"
    ))
    world.add_component(amulet, Item(
        name="The Amulet of Yendor",
        is_amulet=True
    ))
    world.add_component(amulet, Equipment(
        slot=EquipmentSlot.AMULET,
        power_bonus=5,
        defense_bonus=5,
        max_hp_bonus=20
    ))
    
    return amulet

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
    world.add_component(armor, Item(name=name))
    world.add_component(armor, Equipment(
        slot=slot,
        defense_bonus=defense_bonus
    ))
    
    return armor

def create_ring(world: Any, x: int, y: int, slot: EquipmentSlot, name: str, bonus_type: str, bonus: int) -> int:
    """Create a ring."""
    ring = world.create_entity()
    
    world.add_component(ring, Position(x, y))
    world.add_component(ring, Renderable(
        char='=',
        color=Colors.YELLOW,
        render_order=RenderOrder.ITEM,
        name=name
    ))
    world.add_component(ring, Item())
    
    # Set appropriate bonus based on type
    if bonus_type == 'power':
        world.add_component(ring, Equipment(
            slot=slot,
            power_bonus=bonus
        ))
    elif bonus_type == 'defense':
        world.add_component(ring, Equipment(
            slot=slot,
            defense_bonus=bonus
        ))
    elif bonus_type == 'hp':
        world.add_component(ring, Equipment(
            slot=slot,
            max_hp_bonus=bonus
        ))
    
    return ring

def create_cloak(world: Any, x: int, y: int, name: str, defense: int) -> int:
    """Create a cloak."""
    cloak = world.create_entity()
    
    world.add_component(cloak, Position(x, y))
    world.add_component(cloak, Renderable(
        char='(',
        color=Colors.BLUE,
        render_order=RenderOrder.ITEM,
        name=name
    ))
    world.add_component(cloak, Item())
    world.add_component(cloak, Equipment(
        slot=EquipmentSlot.CLOAK,
        defense_bonus=defense
    ))
    
    return cloak

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
    world.add_component(shield, Item(name=name))
    world.add_component(shield, Equipment(
        slot=EquipmentSlot.OFF_HAND,
        defense_bonus=defense_bonus
    ))
    
    return shield

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
    world.add_component(weapon, Item(name=name))
    world.add_component(weapon, Equipment(
        slot=EquipmentSlot.MAIN_HAND,
        power_bonus=power_bonus,
        weapon_type=weapon_type
    ))
    
    return weapon

def use_healing_potion(user: int, world: Any, **kwargs) -> Optional[str]:
    """
    Use a healing potion.
    
    Args:
        user: The entity using the potion
        world: The ECS world
        kwargs: Additional arguments
        
    Returns:
        A message describing what happened
    """
    amount = kwargs.get('amount', 0)
    fighter = world.component_for_entity(user, Fighter)
    
    if fighter.hp == fighter.max_hp:
        return "You are already at full health."
    
    fighter.heal(amount)
    return f"Your wounds start to feel better! You heal for {amount} hit points."

def use_lightning(user: int, world: Any, **kwargs) -> Optional[str]:
    """
    Use a lightning scroll.
    
    Args:
        user: The entity using the scroll
        world: The ECS world
        kwargs: Additional arguments
        
    Returns:
        A message describing what happened
    """
    damage = kwargs.get('damage', 0)
    maximum_range = kwargs.get('maximum_range', 0)
    
    user_pos = world.component_for_entity(user, Position)
    closest_distance = maximum_range + 1
    target = None
    
    for ent, (pos, fighter) in world.get_components(Position, Fighter):
        if ent != user:
            distance = user_pos.distance_to(pos)
            if distance < closest_distance:
                closest_distance = distance
                target = ent
    
    if target is None:
        return "No enemy is close enough to strike."
    
    fighter = world.component_for_entity(target, Fighter)
    fighter.take_damage(damage)
    target_name = world.component_for_entity(target, Renderable).name
    return f"A lighting bolt strikes the {target_name} with a loud thunder! The damage is {damage}."

def use_fireball(user: int, world: Any, target_x: int, target_y: int, **kwargs) -> Optional[str]:
    """
    Use a fireball scroll.
    
    Args:
        user: The entity using the scroll
        world: The ECS world
        target_x: Target X coordinate
        target_y: Target Y coordinate
        kwargs: Additional arguments
        
    Returns:
        A message describing what happened
    """
    damage = kwargs.get('damage', 0)
    radius = kwargs.get('radius', 0)
    
    targets_hit = []
    for ent, (pos, fighter) in world.get_components(Position, Fighter):
        if ent != user:
            distance = max(abs(target_x - pos.x), abs(target_y - pos.y))
            if distance <= radius:
                fighter.take_damage(damage)
                targets_hit.append(world.component_for_entity(ent, Renderable).name)
    
    if not targets_hit:
        return "The fireball explodes in vain."
    
    return f"The fireball explodes, burning {', '.join(targets_hit)}! The damage is {damage}."

def use_confusion(user: int, world: Any, target: int, **kwargs) -> Optional[str]:
    """
    Use a confusion scroll.
    
    Args:
        user: The entity using the scroll
        world: The ECS world
        target: The target entity
        kwargs: Additional arguments
        
    Returns:
        A message describing what happened
    """
    turns = kwargs.get('turns', 0)
    
    if not world.has_component(target, AI):
        return "You cannot confuse that!"
    
    ai = world.component_for_entity(target, AI)
    ai.behavior = "confused"
    ai.turns_confused = turns
    
    target_name = world.component_for_entity(target, Renderable).name
    return f"The eyes of the {target_name} look vacant, as it starts to stumble around!"

def create_necklace(world: Any, x: int, y: int, name: str, bonus_type: str, bonus: int) -> int:
    """Create a necklace."""
    necklace = world.create_entity()
    
    world.add_component(necklace, Position(x, y))
    world.add_component(necklace, Renderable(
        char='"',  # 首飾りは " で表示
        color=Colors.LIGHT_VIOLET,
        render_order=RenderOrder.ITEM,
        name=name
    ))
    world.add_component(necklace, Item())
    
    # Set appropriate bonus based on type
    if bonus_type == 'power':
        world.add_component(necklace, Equipment(
            slot=EquipmentSlot.NECK,
            power_bonus=bonus
        ))
    elif bonus_type == 'defense':
        world.add_component(necklace, Equipment(
            slot=EquipmentSlot.NECK,
            defense_bonus=bonus
        ))
    elif bonus_type == 'hp':
        world.add_component(necklace, Equipment(
            slot=EquipmentSlot.NECK,
            max_hp_bonus=bonus
        ))
    
    return necklace

# Item spawn chances by dungeon level
ITEM_CHANCES: Dict[str, Dict[str, Any]] = {
    # Weapons
    'dagger': {
        'chance': 30,
        'min_level': 1,
        'max_level': 5,
        'create_function': lambda w, x, y: create_weapon(w, x, y, "Dagger", 2, WeaponType.DUAL_WIELD, Colors.LIGHT_GRAY)
    },
    'short_sword': {
        'chance': 25,
        'min_level': 2,
        'max_level': 7,
        'create_function': lambda w, x, y: create_weapon(w, x, y, "Short Sword", 3, WeaponType.ONE_HANDED, Colors.LIGHT_GRAY)
    },
    'wakizashi': {  # 脇差（二刀流用の短剣）
        'chance': 20,
        'min_level': 3,
        'max_level': None,
        'create_function': lambda w, x, y: create_weapon(w, x, y, "Wakizashi", 2, WeaponType.DUAL_WIELD, Colors.LIGHT_GRAY)
    },
    'ninja_to': {  # 忍者刀（二刀流用の短剣）
        'chance': 15,
        'min_level': 4,
        'max_level': None,
        'create_function': lambda w, x, y: create_weapon(w, x, y, "Ninja-to", 3, WeaponType.DUAL_WIELD, Colors.LIGHT_GRAY)
    },
    'long_sword': {
        'chance': 20,
        'min_level': 4,
        'max_level': None,
        'create_function': lambda w, x, y: create_weapon(w, x, y, "Long Sword", 4, WeaponType.ONE_HANDED, Colors.LIGHT_GRAY)
    },
    'great_sword': {
        'chance': 15,
        'min_level': 6,
        'max_level': None,
        'create_function': lambda w, x, y: create_weapon(w, x, y, "Great Sword", 6, WeaponType.TWO_HANDED, Colors.WHITE)
    },
    'bow': {
        'chance': 20,
        'min_level': 3,
        'max_level': None,
        'create_function': lambda w, x, y: create_weapon(w, x, y, "Bow", 3, WeaponType.BOW, Colors.BROWN)
    },
    
    # Armor
    'leather_armor': {
        'chance': 35,
        'min_level': 1,
        'max_level': 5,
        'create_function': lambda w, x, y: create_armor(w, x, y, EquipmentSlot.BODY, "Leather Armor", 1, Colors.BROWN)
    },
    'chain_mail': {
        'chance': 25,
        'min_level': 3,
        'max_level': 7,
        'create_function': lambda w, x, y: create_armor(w, x, y, EquipmentSlot.BODY, "Chain Mail", 2, Colors.GRAY)
    },
    'plate_mail': {
        'chance': 15,
        'min_level': 5,
        'max_level': None,
        'create_function': lambda w, x, y: create_armor(w, x, y, EquipmentSlot.BODY, "Plate Mail", 3, Colors.WHITE)
    },
    
    # Shields
    'wooden_shield': {
        'chance': 30,
        'min_level': 1,
        'max_level': 5,
        'create_function': lambda w, x, y: create_shield(w, x, y, "Wooden Shield", 1)
    },
    'iron_shield': {
        'chance': 20,
        'min_level': 3,
        'max_level': None,
        'create_function': lambda w, x, y: create_shield(w, x, y, "Iron Shield", 2)
    },
    
    # Rings
    'ring_protection': {
        'chance': 15,
        'min_level': 4,
        'max_level': None,
        'create_function': lambda w, x, y: create_ring(w, x, y, EquipmentSlot.RING_LEFT, "Ring of Protection", 'defense', 1)
    },
    'ring_strength': {
        'chance': 15,
        'min_level': 4,
        'max_level': None,
        'create_function': lambda w, x, y: create_ring(w, x, y, EquipmentSlot.RING_RIGHT, "Ring of Strength", 'power', 1)
    },
    
    # Necklaces
    'necklace_vitality': {
        'chance': 15,
        'min_level': 3,
        'max_level': None,
        'create_function': lambda w, x, y: create_necklace(w, x, y, "Necklace of Vitality", 'hp', 10)
    },
    'necklace_power': {
        'chance': 15,
        'min_level': 4,
        'max_level': None,
        'create_function': lambda w, x, y: create_necklace(w, x, y, "Necklace of Power", 'power', 2)
    },
    'necklace_protection': {
        'chance': 15,
        'min_level': 4,
        'max_level': None,
        'create_function': lambda w, x, y: create_necklace(w, x, y, "Necklace of Protection", 'defense', 2)
    },
    
    # Cloaks
    'cloak_protection': {
        'chance': 20,
        'min_level': 2,
        'max_level': None,
        'create_function': lambda w, x, y: create_cloak(w, x, y, "Cloak of Protection", 1)
    },
    
    # Keep existing items
    'healing_potion': {
        'chance': 35,
        'min_level': 1,
        'max_level': None,
        'create_function': create_healing_potion
    },
    'amulet_of_yendor': {
        'chance': 100,
        'min_level': 26,
        'max_level': 26,
        'create_function': create_amulet_of_yendor
    }
} 