# TODO: Add scroll identification system
# TODO: Add more scroll types
# FIXME: Teleport should check for valid destination
# OPTIMIZE: Scroll targeting could be simplified
# WARNING: Scroll effects might need balancing
# REVIEW: Consider if scrolls should require magic power
# HACK: Scroll display characters should be moved to constants

from typing import Any, Optional
import random

from roguelike.core.constants import Colors, MAP_WIDTH, MAP_HEIGHT
from roguelike.world.entity.components.base import Position, Item, Renderable, RenderOrder

def create_identify_scroll(world: Any, x: int, y: int) -> int:
    """Create an identify scroll entity."""
    scroll = world.create_entity()
    
    world.add_component(scroll, Position(x, y))
    world.add_component(scroll, Renderable(
        char='?',
        color=Colors.LIGHT_BLUE,
        render_order=RenderOrder.ITEM,
        name="Scroll of Identify"
    ))
    world.add_component(scroll, Item(
        name="Scroll of Identify",
        use_function=use_identify,
        targeting=True,
        targeting_message="Select an item to identify, or right-click to cancel."
    ))
    
    return scroll

def create_teleport_scroll(world: Any, x: int, y: int) -> int:
    """Create a teleport scroll entity."""
    scroll = world.create_entity()
    
    world.add_component(scroll, Position(x, y))
    world.add_component(scroll, Renderable(
        char='?',
        color=Colors.VIOLET,
        render_order=RenderOrder.ITEM,
        name="Scroll of Teleportation"
    ))
    world.add_component(scroll, Item(
        name="Scroll of Teleportation",
        use_function=use_teleport
    ))
    
    return scroll

def use_identify(user: int, world: Any, target_item: int, **kwargs) -> Optional[str]:
    """
    Use an identify scroll.
    
    Args:
        user: The entity using the scroll
        world: The ECS world
        target_item: The item to identify
        
    Returns:
        A message describing what happened
    """
    if not world.has_component(target_item, Item):
        return "You can only identify items!"
    
    item = world.component_for_entity(target_item, Item)
    renderable = world.component_for_entity(target_item, Renderable)
    
    # 本来はここでアイテムの本当の性質を明らかにする
    # 今回は仮実装として名前を表示
    return f"You identify the item as: {renderable.name}"

def use_teleport(user: int, world: Any, **kwargs) -> Optional[str]:
    """
    Use a teleport scroll.
    
    Args:
        user: The entity using the scroll
        world: The ECS world
        
    Returns:
        A message describing what happened
    """
    player_pos = world.component_for_entity(user, Position)
    
    # ランダムな位置に移動（実際には通行可能な場所を探す必要あり）
    old_x, old_y = player_pos.x, player_pos.y
    player_pos.x = random.randint(1, MAP_WIDTH - 2)
    player_pos.y = random.randint(1, MAP_HEIGHT - 2)
    
    return f"You teleport from ({old_x}, {old_y}) to ({player_pos.x}, {player_pos.y})!" 