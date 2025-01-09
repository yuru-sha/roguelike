"""
Item usage action handler for the game.
"""

import logging
from typing import Any, Dict, Optional

from roguelike.core.constants import Colors
from roguelike.core.event import EventManager, Event, EventType
from roguelike.world.entity.components.base import (
    Position, Inventory, Item, Equipment, EquipmentSlots,
    Fighter, Consumable, Renderable
)

logger = logging.getLogger(__name__)

class UseItemAction:
    """Handles all item usage actions."""

    def __init__(self, world: Any, game_state: Any):
        """Initialize the item usage action handler.
        
        Args:
            world: The game world
            game_state: The current game state
        """
        self.world = world
        self.game_state = game_state
        self.event_manager = EventManager.get_instance()

    def handle_use_item(self, action: Dict[str, Any]) -> None:
        """Handle item usage action.
        
        Args:
            action: The item usage action details
        """
        try:
            item_id = action.get("item_id")
            if not item_id:
                logger.warning("No item ID provided for use action")
                return

            # Get item components
            if not self.world.has_component(item_id, Item):
                logger.warning(f"Entity {item_id} is not an item")
                return

            item_name = self.world.component_for_entity(item_id, Renderable).name

            # Check if item is equipment
            if self.world.has_component(item_id, Equipment):
                self._handle_equipment(item_id)
            # Check if item is consumable
            elif self.world.has_component(item_id, Consumable):
                self._handle_consumable(item_id)
            else:
                self.event_manager.publish(Event(
                    EventType.MESSAGE_LOG,
                    {
                        "message": f"Thou canst not use the {item_name}.",
                        "color": Colors.YELLOW
                    }
                ))
                logger.debug(f"Item {item_name} (ID: {item_id}) cannot be used")

        except Exception as e:
            logger.error(f"Error handling item usage: {str(e)}", exc_info=True)
            raise

    def _handle_equipment(self, item_id: int) -> None:
        """Handle equipment item usage.
        
        Args:
            item_id: ID of the equipment item
        """
        try:
            equipment = self.world.component_for_entity(item_id, Equipment)
            item_name = self.world.component_for_entity(item_id, Renderable).name

            # Get player's equipment slots
            if not self.world.has_component(self.game_state.player, EquipmentSlots):
                logger.warning("Player has no equipment slots")
                return

            equipment_slots = self.world.component_for_entity(
                self.game_state.player, EquipmentSlots
            )

            # Check if item is already equipped
            for slot, equipped_id in equipment_slots.slots.items():
                if equipped_id == item_id:
                    # Unequip item
                    equipment_slots.slots[slot] = None
                    
                    # Publish equipment change event
                    self.event_manager.publish(Event(
                        EventType.EQUIPMENT_CHANGED,
                        {
                            "action": "unequip",
                            "item": item_id,
                            "item_name": item_name,
                            "slot": slot,
                            "player": self.game_state.player
                        }
                    ))
                    
                    self.event_manager.publish(Event(
                        EventType.MESSAGE_LOG,
                        {
                            "message": f"Thou removeth the {item_name}.",
                            "color": Colors.LIGHT_YELLOW
                        }
                    ))
                    logger.debug(f"Unequipped {item_name} (ID: {item_id}) from {slot}")
                    return

            # Equip item in appropriate slot
            if equipment.slot in equipment_slots.slots:
                # Remove currently equipped item if any
                current_item = equipment_slots.slots[equipment.slot]
                if current_item is not None:
                    current_name = self.world.component_for_entity(
                        current_item, Renderable
                    ).name
                    
                    # Publish unequip event for current item
                    self.event_manager.publish(Event(
                        EventType.EQUIPMENT_CHANGED,
                        {
                            "action": "unequip",
                            "item": current_item,
                            "item_name": current_name,
                            "slot": equipment.slot,
                            "player": self.game_state.player
                        }
                    ))
                    
                    self.event_manager.publish(Event(
                        EventType.MESSAGE_LOG,
                        {
                            "message": f"Thou removeth the {current_name}.",
                            "color": Colors.LIGHT_YELLOW
                        }
                    ))
                    logger.debug(
                        f"Unequipped {current_name} (ID: {current_item}) from {equipment.slot}"
                    )

                # Equip new item
                equipment_slots.slots[equipment.slot] = item_id
                
                # Publish equip event
                self.event_manager.publish(Event(
                    EventType.EQUIPMENT_CHANGED,
                    {
                        "action": "equip",
                        "item": item_id,
                        "item_name": item_name,
                        "slot": equipment.slot,
                        "player": self.game_state.player
                    }
                ))
                
                self.event_manager.publish(Event(
                    EventType.MESSAGE_LOG,
                    {
                        "message": f"Thou dost equip the {item_name}.",
                        "color": Colors.LIGHT_GREEN
                    }
                ))
                logger.debug(f"Equipped {item_name} (ID: {item_id}) to {equipment.slot}")

        except Exception as e:
            logger.error(f"Error handling equipment: {str(e)}", exc_info=True)
            raise

    def _handle_consumable(self, item_id: int) -> None:
        """Handle consumable item usage.
        
        Args:
            item_id: ID of the consumable item
        """
        try:
            consumable = self.world.component_for_entity(item_id, Consumable)
            item_name = self.world.component_for_entity(item_id, Renderable).name

            # Apply consumable effects
            if consumable.heal:
                self._apply_healing(item_id, consumable.heal)
            # Add more consumable effects here...

            # Remove item from inventory
            if self.world.has_component(self.game_state.player, Inventory):
                inventory = self.world.component_for_entity(
                    self.game_state.player, Inventory
                )
                inventory.remove_item(item_id)
                logger.debug(f"Removed consumed item {item_name} (ID: {item_id}) from inventory")

            # Publish item used event
            self.event_manager.publish(Event(
                EventType.ITEM_USED,
                {
                    "item": item_id,
                    "item_name": item_name,
                    "player": self.game_state.player,
                    "effects": {
                        "heal": consumable.heal if consumable.heal else 0
                    }
                }
            ))

            # Delete the item entity
            self.world.delete_entity(item_id)
            logger.debug(f"Deleted consumed item entity {item_name} (ID: {item_id})")

        except Exception as e:
            logger.error(f"Error handling consumable: {str(e)}", exc_info=True)
            raise

    def _apply_healing(self, item_id: int, heal_amount: int) -> None:
        """Apply healing effect from a consumable item.
        
        Args:
            item_id: ID of the healing item
            heal_amount: Amount of HP to heal
        """
        try:
            if not self.world.has_component(self.game_state.player, Fighter):
                logger.warning("Player has no Fighter component")
                return

            fighter = self.world.component_for_entity(self.game_state.player, Fighter)
            item_name = self.world.component_for_entity(item_id, Renderable).name

            if fighter.hp == fighter.max_hp:
                self.event_manager.publish(Event(
                    EventType.MESSAGE_LOG,
                    {
                        "message": "Thy health is already at its fullest.",
                        "color": Colors.YELLOW
                    }
                ))
                logger.debug("Healing failed: Player at full health")
                return

            old_hp = fighter.hp
            fighter.hp = min(fighter.hp + heal_amount, fighter.max_hp)
            healed = fighter.hp - old_hp

            self.event_manager.publish(Event(
                EventType.MESSAGE_LOG,
                {
                    "message": f"The {item_name} restoreth {healed} of thy vitality.",
                    "color": Colors.LIGHT_GREEN
                }
            ))
            logger.debug(f"Healed player for {healed} HP using {item_name} (ID: {item_id})")

        except Exception as e:
            logger.error(f"Error applying healing: {str(e)}", exc_info=True)
            raise 