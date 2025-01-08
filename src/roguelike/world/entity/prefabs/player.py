import esper

from roguelike.world.entity.components.base import (
    Position, Renderable, Fighter, Inventory, Level
)
from roguelike.core.constants import Colors, LEVEL_UP_BASE, LEVEL_UP_FACTOR

def create_player(world: esper.World, x: int, y: int) -> int:
    """
    Create the player entity.
    
    Args:
        world: The game world
        x: X coordinate
        y: Y coordinate
        
    Returns:
        The entity ID
    """
    player = world.create_entity()
    
    world.add_component(player, Position(x=x, y=y))
    world.add_component(player, Renderable(
        char='@',
        color=Colors.PLAYER,
        render_order=2  # Player is rendered above all other entities
    ))
    world.add_component(player, Fighter(
        max_hp=30,
        hp=30,
        defense=2,
        power=5,
        xp=0
    ))
    world.add_component(player, Inventory(capacity=26))  # A-Z inventory slots
    world.add_component(player, Level(
        current_level=1,
        current_xp=0,
        level_up_base=LEVEL_UP_BASE,
        level_up_factor=LEVEL_UP_FACTOR
    ))
    
    return player

def level_up_player(world: esper.World, player: int) -> None:
    """
    Level up the player entity.
    
    Args:
        world: The game world
        player: The player entity ID
    """
    fighter = world.component_for_entity(player, Fighter)
    
    # Increase stats
    fighter.max_hp += 10
    fighter.hp = fighter.max_hp
    fighter.defense += 1
    fighter.power += 1 