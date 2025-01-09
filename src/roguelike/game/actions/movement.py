"""
Movement action handler for the game.
"""

import logging
from typing import Any, Dict, Optional

from roguelike.core.constants import MAP_WIDTH, MAP_HEIGHT, Colors
from roguelike.world.entity.components.base import Position, Fighter, Corpse, Renderable

logger = logging.getLogger(__name__)

class MovementAction:
    """Handles all movement-related actions."""

    def __init__(self, world: Any, game_state: Any, combat_system: Any, map_manager: Any):
        """Initialize the movement action handler.
        
        Args:
            world: The game world
            game_state: The current game state
            combat_system: The combat system
            map_manager: The map manager
        """
        self.world = world
        self.game_state = game_state
        self.combat_system = combat_system
        self.map_manager = map_manager

    def handle_movement(self, action: Dict[str, Any]) -> None:
        """Handle movement action.
        
        Args:
            action: The movement action details
        """
        try:
            dx = action.get("dx", 0)
            dy = action.get("dy", 0)

            player_pos = self.world.component_for_entity(self.game_state.player, Position)
            dest_x = player_pos.x + dx
            dest_y = player_pos.y + dy

            logger.debug(
                f"Player (ID: {self.game_state.player}) at ({player_pos.x}, {player_pos.y}) attempting to move to ({dest_x}, {dest_y})"
            )

            # Check if destination is within bounds
            if not (0 <= dest_x < MAP_WIDTH and 0 <= dest_y < MAP_HEIGHT):
                return

            # First check for entities at destination
            for ent, (pos, fighter) in self.world.get_components(Position, Fighter):
                if pos.x == dest_x and pos.y == dest_y:
                    # Attack!
                    target_name = self.world.component_for_entity(ent, Renderable).name
                    logger.debug(
                        f"Found enemy {target_name} (ID: {ent}) at ({pos.x}, {pos.y})"
                    )
                    damage = self.combat_system.calculate_damage(self.game_state.player, ent)

                    if damage > 0:
                        self.game_state.add_message(
                            f"You attack {target_name} for {damage} damage!",
                            Colors.PLAYER_ATK,
                        )
                        xp = fighter.take_damage(damage)
                        logger.debug(
                            f"Dealt {damage} damage to {target_name} (ID: {ent}), HP remaining: {fighter.hp}"
                        )
                        # Check if enemy died
                        if fighter.hp <= 0:
                            self.game_state.add_message(
                                f"{target_name} dies!", Colors.ENEMY_DIE
                            )
                            self.combat_system.handle_enemy_death(ent, xp)
                    else:
                        self.game_state.add_message(
                            f"You attack {target_name} but do no damage!",
                            Colors.PLAYER_ATK,
                        )
                    return

            # Then check if tile is blocked
            if self.map_manager.tiles[dest_y][dest_x].blocked:
                logger.debug(f"Movement blocked by terrain at ({dest_x}, {dest_y})")
                return

            # Check for corpses at destination
            for ent, (pos, _) in self.world.get_components(Position, Corpse):
                if pos.x == dest_x and pos.y == dest_y:
                    # Can move over corpses
                    logger.debug(f"Moving over corpse at ({pos.x}, {pos.y})")
                    player_pos.x = dest_x
                    player_pos.y = dest_y
                    logger.debug(
                        f"Player (ID: {self.game_state.player}) moved to ({player_pos.x}, {player_pos.y})"
                    )
                    return

            # Move player
            player_pos.x = dest_x
            player_pos.y = dest_y
            logger.debug(
                f"Player (ID: {self.game_state.player}) moved to ({player_pos.x}, {player_pos.y})"
            )

        except Exception as e:
            logger.error(f"Error handling movement: {str(e)}", exc_info=True)
            raise 