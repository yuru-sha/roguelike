from typing import Any, Dict

from roguelike.core.constants import Colors
from roguelike.world.entity.components.base import (AI, Fighter, Position,
                                                    Renderable, RenderOrder)


def create_orc(world: Any, x: int, y: int) -> int:
    """
    Create an orc entity.

    Args:
        world: The ECS world
        x: X coordinate
        y: Y coordinate

    Returns:
        The entity ID
    """
    orc = world.create_entity()

    world.add_component(orc, Position(x, y))
    world.add_component(
        orc,
        Renderable(
            char="o", color=Colors.GREEN, render_order=RenderOrder.ACTOR, name="Orc"
        ),
    )
    world.add_component(orc, Fighter(max_hp=10, hp=10, defense=0, power=3, xp=35))
    world.add_component(orc, AI())

    return orc


def create_troll(world: Any, x: int, y: int) -> int:
    """
    Create a troll entity.

    Args:
        world: The ECS world
        x: X coordinate
        y: Y coordinate

    Returns:
        The entity ID
    """
    troll = world.create_entity()

    world.add_component(troll, Position(x, y))
    world.add_component(
        troll,
        Renderable(
            char="T", color=Colors.RED, render_order=RenderOrder.ACTOR, name="Troll"
        ),
    )
    world.add_component(troll, Fighter(max_hp=16, hp=16, defense=1, power=4, xp=100))
    world.add_component(troll, AI(behavior="aggressive"))

    return troll


# Monster spawn chances by dungeon level
MONSTER_CHANCES: Dict[str, Dict[str, Any]] = {
    "orc": {
        "chance": 80,
        "min_level": 1,
        "max_level": 6,
        "create_function": create_orc,
    },
    "troll": {
        "chance": 20,
        "min_level": 3,
        "max_level": None,
        "create_function": create_troll,
    },
}
