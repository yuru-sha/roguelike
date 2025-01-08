from typing import Any, Tuple

from roguelike.core.constants import (
    Colors, PLAYER_HP, PLAYER_DEFENSE,
    PLAYER_POWER, PLAYER_XP, PLAYER_INVENTORY_CAPACITY
)
from roguelike.world.entity.components.base import (
    Position, Fighter, Level, Renderable,
    Inventory, RenderOrder
)

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
    world.add_component(player, Renderable(
        char='@',
        color=Colors.WHITE,
        render_order=RenderOrder.ACTOR,
        name="Player",
        always_visible=True
    ))
    world.add_component(player, Fighter(
        max_hp=PLAYER_HP,
        hp=PLAYER_HP,
        defense=PLAYER_DEFENSE,
        power=PLAYER_POWER,
        xp=PLAYER_XP
    ))
    world.add_component(player, Level())
    world.add_component(player, Inventory(PLAYER_INVENTORY_CAPACITY))
    
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