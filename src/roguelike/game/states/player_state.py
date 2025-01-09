"""
Player state management system.
"""

import logging
from typing import Any, Dict, Optional, Tuple

from roguelike.core.constants import Colors
from roguelike.world.entity.components.base import (
    Fighter, Level, Position, Inventory, EquipmentSlots
)

logger = logging.getLogger(__name__)

class PlayerState:
    """Manages the player's state and attributes."""

    def __init__(self, world: Any, game_state: Any):
        """Initialize the player state manager.
        
        Args:
            world: The game world
            game_state: The current game state
        """
        self.world = world
        self.game_state = game_state

    def get_stats(self) -> Dict[str, Any]:
        """Get the player's current stats.
        
        Returns:
            Dictionary containing player stats
        """
        try:
            stats = {}

            if not self.game_state.player:
                logger.warning("No player entity exists")
                return stats

            # Get fighter stats
            if self.world.has_component(self.game_state.player, Fighter):
                fighter = self.world.component_for_entity(self.game_state.player, Fighter)
                stats.update({
                    "hp": fighter.hp,
                    "max_hp": fighter.max_hp,
                    "power": fighter.power,
                    "defense": fighter.defense
                })

            # Get level stats
            if self.world.has_component(self.game_state.player, Level):
                level = self.world.component_for_entity(self.game_state.player, Level)
                stats.update({
                    "level": level.current_level,
                    "xp": level.current_xp,
                    "next_level_xp": level.experience_to_next_level
                })

            logger.debug(f"Retrieved player stats: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error getting player stats: {str(e)}", exc_info=True)
            raise

    def get_position(self) -> Optional[Tuple[int, int]]:
        """Get the player's current position.
        
        Returns:
            Tuple of (x, y) coordinates, or None if player doesn't exist
        """
        try:
            if not self.game_state.player:
                logger.warning("No player entity exists")
                return None

            if self.world.has_component(self.game_state.player, Position):
                pos = self.world.component_for_entity(self.game_state.player, Position)
                return (pos.x, pos.y)

            return None

        except Exception as e:
            logger.error(f"Error getting player position: {str(e)}", exc_info=True)
            raise

    def heal(self, amount: int) -> int:
        """Heal the player.
        
        Args:
            amount: Amount of HP to heal
            
        Returns:
            Amount of HP actually healed
        """
        try:
            if not self.game_state.player:
                logger.warning("No player entity exists")
                return 0

            if not self.world.has_component(self.game_state.player, Fighter):
                logger.warning("Player has no Fighter component")
                return 0

            fighter = self.world.component_for_entity(self.game_state.player, Fighter)
            old_hp = fighter.hp
            fighter.hp = min(fighter.hp + amount, fighter.max_hp)
            healed = fighter.hp - old_hp

            if healed > 0:
                self.game_state.add_message(
                    f"You are healed for {healed} HP.", Colors.GREEN
                )
                logger.debug(f"Healed player for {healed} HP")

            return healed

        except Exception as e:
            logger.error(f"Error healing player: {str(e)}", exc_info=True)
            raise

    def take_damage(self, amount: int) -> None:
        """Apply damage to the player.
        
        Args:
            amount: Amount of damage to take
        """
        try:
            if not self.game_state.player:
                logger.warning("No player entity exists")
                return

            if not self.world.has_component(self.game_state.player, Fighter):
                logger.warning("Player has no Fighter component")
                return

            fighter = self.world.component_for_entity(self.game_state.player, Fighter)
            fighter.take_damage(amount)

            if fighter.hp <= 0:
                self.game_state.player_dead = True
                self.game_state.add_message("You died!", Colors.RED)
                logger.info("Player died")

            logger.debug(f"Player took {amount} damage, HP remaining: {fighter.hp}")

        except Exception as e:
            logger.error(f"Error applying damage to player: {str(e)}", exc_info=True)
            raise

    def add_xp(self, xp: int) -> bool:
        """Add experience points to the player.
        
        Args:
            xp: Amount of XP to add
            
        Returns:
            True if player leveled up, False otherwise
        """
        try:
            if not self.game_state.player:
                logger.warning("No player entity exists")
                return False

            if not self.world.has_component(self.game_state.player, Level):
                logger.warning("Player has no Level component")
                return False

            level = self.world.component_for_entity(self.game_state.player, Level)
            leveled_up = level.add_xp(xp)

            if leveled_up:
                self.game_state.add_message(
                    f"You reached level {level.current_level}!", Colors.YELLOW
                )
                logger.info(f"Player reached level {level.current_level}")

            logger.debug(f"Added {xp} XP to player")
            return leveled_up

        except Exception as e:
            logger.error(f"Error adding XP to player: {str(e)}", exc_info=True)
            raise

    def get_inventory_items(self) -> list:
        """Get the player's inventory items.
        
        Returns:
            List of item entity IDs
        """
        try:
            if not self.game_state.player:
                logger.warning("No player entity exists")
                return []

            if not self.world.has_component(self.game_state.player, Inventory):
                logger.warning("Player has no Inventory component")
                return []

            inventory = self.world.component_for_entity(self.game_state.player, Inventory)
            logger.debug(f"Retrieved {len(inventory.items)} inventory items")
            return inventory.items

        except Exception as e:
            logger.error(f"Error getting inventory items: {str(e)}", exc_info=True)
            raise

    def get_equipment(self) -> Dict[str, Optional[int]]:
        """Get the player's equipped items.
        
        Returns:
            Dictionary mapping slot names to item entity IDs
        """
        try:
            if not self.game_state.player:
                logger.warning("No player entity exists")
                return {}

            if not self.world.has_component(self.game_state.player, EquipmentSlots):
                logger.warning("Player has no EquipmentSlots component")
                return {}

            equipment = self.world.component_for_entity(
                self.game_state.player, EquipmentSlots
            )
            logger.debug(f"Retrieved equipment slots: {equipment.slots}")
            return equipment.slots

        except Exception as e:
            logger.error(f"Error getting equipment: {str(e)}", exc_info=True)
            raise 