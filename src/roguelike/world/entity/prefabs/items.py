from typing import Dict, Any, Optional, Callable

from roguelike.core.constants import Colors
from roguelike.world.entity.components.base import Position, Item, Renderable, RenderOrder, Fighter, AI

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

# Item spawn chances by dungeon level
ITEM_CHANCES: Dict[str, Dict[str, Any]] = {
    'healing_potion': {
        'chance': 35,
        'min_level': 1,
        'max_level': None,
        'create_function': create_healing_potion
    },
    'lightning_scroll': {
        'chance': 25,
        'min_level': 4,
        'max_level': None,
        'create_function': create_lightning_scroll
    },
    'fireball_scroll': {
        'chance': 25,
        'min_level': 6,
        'max_level': None,
        'create_function': create_fireball_scroll
    },
    'confusion_scroll': {
        'chance': 10,
        'min_level': 2,
        'max_level': None,
        'create_function': create_confusion_scroll
    }
} 