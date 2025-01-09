"""
Item action handler for the game.
"""

import logging
from typing import Any

from roguelike.core.constants import Colors
from roguelike.core.event import EventManager, Event, EventType
from roguelike.world.entity.components.base import Position, Item, Inventory, Renderable

logger = logging.getLogger(__name__)

class ItemAction:
    """Handles all item-related actions."""

    def __init__(self, world: Any, game_state: Any):
        """Initialize the item action handler.
        
        Args:
            world: The game world
            game_state: The current game state
        """
        self.world = world
        self.game_state = game_state
        self.event_manager = EventManager.get_instance()

    def handle_pickup(self) -> None:
        """Handle picking up an item."""
        try:
            player_pos = self.world.component_for_entity(self.game_state.player, Position)
            player_inventory = self.world.component_for_entity(self.game_state.player, Inventory)

            # Find items at player's position
            items_found = False
            for ent, (pos, _) in self.world.get_components(Position, Item):
                if pos.x == player_pos.x and pos.y == player_pos.y:
                    items_found = True
                    # Check if inventory is full
                    slot = player_inventory.add_item(ent)
                    item_name = self.world.component_for_entity(
                        ent, Renderable
                    ).name

                    if slot is None:
                        self.event_manager.publish(Event(
                            EventType.MESSAGE_LOG,
                            {
                                "message": f"Thy pack is full, thou canst not carry the {item_name}!",
                                "color": Colors.RED
                            }
                        ))
                        logger.info(f"Pickup failed: inventory full, item={item_name}")
                    else:
                        # Add item to inventory and remove from map
                        self.world.remove_component(ent, Position)  # Remove from map
                        
                        # Publish pickup event
                        self.event_manager.publish(Event(
                            EventType.ITEM_PICKED_UP,
                            {
                                "item": ent,
                                "item_name": item_name,
                                "player": self.game_state.player,
                                "slot": slot
                            }
                        ))
                        
                        self.event_manager.publish(Event(
                            EventType.MESSAGE_LOG,
                            {
                                "message": f"Thou dost acquire the {item_name}.",
                                "color": Colors.GREEN
                            }
                        ))
                        logger.info(f"Picked up item: {item_name}, slot={slot}")
                    break

            if not items_found:
                self.event_manager.publish(Event(
                    EventType.MESSAGE_LOG,
                    {
                        "message": "Naught is here to take.",
                        "color": Colors.YELLOW
                    }
                ))
                logger.debug("No items found at player position")

        except Exception as e:
            logger.error(f"Error in pickup handling: {e}", exc_info=True)
            self.event_manager.publish(Event(
                EventType.MESSAGE_LOG,
                {
                    "message": f"A strange force prevents thee from taking the item: {str(e)}",
                    "color": Colors.RED
                }
            ))
            raise 