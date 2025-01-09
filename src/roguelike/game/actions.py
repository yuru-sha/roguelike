"""
Game actions that can be performed by entities.
"""

from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from roguelike.core.engine import Engine


class Action:
    def perform(self, engine: "Engine") -> Optional[str]:
        raise NotImplementedError()


class MovementAction(Action):
    """Action for moving in a direction."""

    def __init__(self, dx: int, dy: int):
        self.dx = dx
        self.dy = dy


class WaitAction(Action):
    """Action for doing nothing and waiting a turn."""

    pass


class QuitAction(Action):
    """Action for quitting the game."""

    pass


class UseStairsAction(Action):
    def perform(self, engine: "Engine") -> Optional[str]:
        """Use stairs to move between dungeon levels."""
        player_pos = engine.world.component_for_entity(
            engine.player, engine.components.Position
        )
        current_tile = engine.dungeon_generator.tiles[player_pos.y][player_pos.x]

        if current_tile.tile_type == engine.tiles.TileType.STAIRS_DOWN:
            # Save current position
            engine.game_state.save_player_position(
                engine.game_state.dungeon_level, (player_pos.x, player_pos.y)
            )

            # Go down
            engine.game_state.dungeon_level += 1
            engine.generate_floor()

            # Place player at up stairs if returning to a previously visited level
            prev_pos = engine.game_state.get_player_position(
                engine.game_state.dungeon_level
            )
            if prev_pos:
                player_pos.x, player_pos.y = prev_pos
            elif engine.dungeon_generator.stairs_up:
                player_pos.x, player_pos.y = engine.dungeon_generator.stairs_up

            return f"You descend to dungeon level {engine.game_state.dungeon_level}."

        elif current_tile.tile_type == engine.tiles.TileType.STAIRS_UP:
            if engine.game_state.dungeon_level == 1:
                if engine.game_state.player_has_amulet:
                    engine.game_state.check_victory_condition()
                    return None
                return "You need the Amulet of Yendor to escape!"

            # Save current position
            engine.game_state.save_player_position(
                engine.game_state.dungeon_level, (player_pos.x, player_pos.y)
            )

            # Go up
            engine.game_state.dungeon_level -= 1
            engine.generate_floor()

            # Place player at down stairs if returning to a previously visited level
            prev_pos = engine.game_state.get_player_position(
                engine.game_state.dungeon_level
            )
            if prev_pos:
                player_pos.x, player_pos.y = prev_pos
            elif engine.dungeon_generator.stairs_down:
                player_pos.x, player_pos.y = engine.dungeon_generator.stairs_down

            return f"You ascend to dungeon level {engine.game_state.dungeon_level}."

        return "There are no stairs here."
