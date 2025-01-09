"""
Combat system for handling all combat-related operations.
"""

import logging
from typing import Any, Tuple

from roguelike.core.constants import Colors
from roguelike.core.event import EventManager, Event, EventType
from roguelike.world.entity.components.base import (
    Position, Renderable, Fighter, Equipment, EquipmentSlots,
    Corpse, Item, RenderOrder, Level
)

logger = logging.getLogger(__name__)

class CombatSystem:
    """Handles all combat-related operations."""

    def __init__(self, world: Any, game_state: Any):
        """Initialize the combat system.
        
        Args:
            world: The game world
            game_state: The current game state
        """
        self.world = world
        self.game_state = game_state
        self.event_manager = EventManager.get_instance()

    def calculate_damage(self, attacker: int, defender: int) -> int:
        """Calculate damage for an attack.
        
        Args:
            attacker: Entity ID of the attacker
            defender: Entity ID of the defender
            
        Returns:
            Amount of damage dealt
        """
        try:
            attacker_fighter = self.world.component_for_entity(attacker, Fighter)
            defender_fighter = self.world.component_for_entity(defender, Fighter)
            attacker_render = self.world.component_for_entity(attacker, Renderable)
            defender_render = self.world.component_for_entity(defender, Renderable)

            # Publish attack event
            self.event_manager.publish(Event(
                EventType.COMBAT_ATTACK,
                {
                    "attacker": attacker,
                    "defender": defender,
                    "attacker_name": attacker_render.name,
                    "defender_name": defender_render.name
                }
            ))

            # Get base attack power
            damage = attacker_fighter.power

            # Add equipment attack power bonus
            if self.world.has_component(attacker, EquipmentSlots):
                equipment_slots = self.world.component_for_entity(attacker, EquipmentSlots)
                for item_id in equipment_slots.slots.values():
                    if item_id is not None and self.world.has_component(item_id, Equipment):
                        equipment = self.world.component_for_entity(item_id, Equipment)
                        damage += equipment.power_bonus

            # Reduce by defense
            damage -= defender_fighter.defense

            # Consider equipment defense bonus
            if self.world.has_component(defender, EquipmentSlots):
                equipment_slots = self.world.component_for_entity(defender, EquipmentSlots)
                for item_id in equipment_slots.slots.values():
                    if item_id is not None and self.world.has_component(item_id, Equipment):
                        equipment = self.world.component_for_entity(item_id, Equipment)
                        damage -= equipment.defense_bonus

            final_damage = max(0, damage)  # Minimum damage is 0

            # Publish damage event
            self.event_manager.publish(Event(
                EventType.COMBAT_DAMAGE if final_damage > 0 else EventType.COMBAT_MISS,
                {
                    "attacker": attacker,
                    "defender": defender,
                    "damage": final_damage,
                    "attacker_name": attacker_render.name,
                    "defender_name": defender_render.name
                }
            ))

            return final_damage

        except Exception as e:
            logger.error(f"Error calculating damage: {str(e)}", exc_info=True)
            return 0

    def handle_enemy_death(self, enemy: int, xp: int) -> None:
        """Handle enemy death.
        
        Args:
            enemy: Entity ID of the dead enemy
            xp: Experience points gained
        """
        try:
            # Get enemy position and name
            enemy_pos = self.world.component_for_entity(enemy, Position)
            enemy_render = self.world.component_for_entity(enemy, Renderable)

            # Publish death event
            self.event_manager.publish(Event(
                EventType.ENTITY_DIED,
                {
                    "entity": enemy,
                    "entity_name": enemy_render.name,
                    "position": {"x": enemy_pos.x, "y": enemy_pos.y}
                }
            ))

            logger.debug(
                f"Creating corpse for {enemy_render.name} at position ({enemy_pos.x}, {enemy_pos.y})"
            )

            # Remove other enemy entities at the same position
            for ent, (pos, _) in self.world.get_components(Position, Fighter):
                if ent != enemy and pos.x == enemy_pos.x and pos.y == enemy_pos.y:
                    logger.debug(f"Removing duplicate enemy at ({pos.x}, {pos.y})")
                    self.world.delete_entity(ent)

            # Remove existing corpses at the same position
            for ent, (pos, _) in self.world.get_components(Position, Corpse):
                if pos.x == enemy_pos.x and pos.y == enemy_pos.y:
                    logger.debug(f"Removing old corpse at ({pos.x}, {pos.y})")
                    self.world.delete_entity(ent)

            # Create new corpse
            corpse = self.world.create_entity()
            logger.debug(f"Created corpse entity with ID: {corpse}")

            corpse_name = f"remains of {enemy_render.name}"
            self.world.add_component(corpse, Position(enemy_pos.x, enemy_pos.y))
            self.world.add_component(
                corpse,
                Renderable(
                    char="%",
                    color=Colors.RED,
                    render_order=RenderOrder.CORPSE,
                    name=corpse_name,
                ),
            )
            self.world.add_component(corpse, Corpse(enemy_render.name))
            self.world.add_component(
                corpse, Item(name=corpse_name)
            )  # Make corpse collectable as an item

            # Publish kill event
            self.event_manager.publish(Event(
                EventType.COMBAT_KILL,
                {
                    "killer": self.game_state.player,
                    "victim": enemy,
                    "corpse": corpse,
                    "position": {"x": enemy_pos.x, "y": enemy_pos.y}
                }
            ))

            logger.debug(
                f"Added components to corpse: Position({enemy_pos.x}, {enemy_pos.y}), Renderable('%', RED, CORPSE), Item"
            )

            # Remove all components from enemy entity
            for component_type in self.world._components:
                if self.world.has_component(enemy, component_type):
                    self.world.remove_component(enemy, component_type)

            # Remove enemy entity
            self.world.delete_entity(enemy)
            logger.debug(f"Deleted enemy entity with ID: {enemy}")

            # Add XP to player
            if self.world.has_component(self.game_state.player, Level):
                player_level = self.world.component_for_entity(self.game_state.player, Level)
                
                # Publish experience gain event
                self.event_manager.publish(Event(
                    EventType.COMBAT_EXPERIENCE,
                    {
                        "player": self.game_state.player,
                        "xp_gained": xp,
                        "current_xp": player_level.current_xp,
                        "xp_to_next_level": player_level.xp_to_next_level
                    }
                ))
                
                if player_level.add_xp(xp):
                    # Publish level up event
                    self.event_manager.publish(Event(
                        EventType.COMBAT_LEVEL_UP,
                        {
                            "player": self.game_state.player,
                            "new_level": player_level.current_level,
                            "old_level": player_level.current_level - 1
                        }
                    ))
                    
                    self.event_manager.publish(Event(
                        EventType.MESSAGE_LOG,
                        {
                            "message": f"Thy combat prowess grows! Thou hast attained level {player_level.current_level}!",
                            "color": Colors.YELLOW
                        }
                    ))

            logger.debug(
                f"Enemy {enemy_render.name} (ID: {enemy}) died and created corpse (ID: {corpse}) at ({enemy_pos.x}, {enemy_pos.y}), player gained {xp} XP"
            )

        except Exception as e:
            logger.error(f"Error handling enemy death: {str(e)}", exc_info=True)
            raise 