"""
Stairs action handler for the game.
"""

import logging
from typing import Any, Dict

from roguelike.core.constants import Colors
from roguelike.core.event import EventManager, Event, EventType
from roguelike.world.entity.components.base import Position
from roguelike.world.map.tiles import TileType

logger = logging.getLogger(__name__)

class StairsAction:
    """Handles all stairs-related actions."""

    def __init__(self, world: Any, game_state: Any, map_manager: Any):
        """Initialize the stairs action handler.
        
        Args:
            world: The game world
            game_state: The current game state
            map_manager: The map manager
        """
        self.world = world
        self.game_state = game_state
        self.map_manager = map_manager
        self.event_manager = EventManager.get_instance()

    def handle_stairs(self, action: Dict[str, Any]) -> None:
        """Handle stair usage action.
        
        Args:
            action: The stair action details
        """
        try:
            if not self.game_state.player:
                logger.warning("Stair usage attempted but no player entity exists")
                return

            direction = action.get("direction")
            player_pos = self.world.component_for_entity(self.game_state.player, Position)
            current_tile = self.map_manager.tiles[player_pos.y][player_pos.x]

            logger.debug(
                f"Attempting to use stairs: direction={direction}, player_pos=({player_pos.x}, {player_pos.y})"
            )
            logger.debug(f"Current tile type: {current_tile.tile_type}")

            if direction == "down" and current_tile.tile_type == TileType.STAIRS_DOWN:
                logger.debug("Found down stairs, descending...")
                # Go down stairs
                old_level = self.game_state.dungeon_level
                self.game_state.dungeon_level += 1
                logger.info(f"Player descended to level {self.game_state.dungeon_level}")
                
                # Publish level change event
                self.event_manager.publish(Event(
                    EventType.LEVEL_CHANGED,
                    {
                        "direction": "down",
                        "old_level": old_level,
                        "new_level": self.game_state.dungeon_level,
                        "player": self.game_state.player
                    }
                ))
                
                self.event_manager.publish(Event(
                    EventType.MESSAGE_LOG,
                    {
                        "message": f"Thou descendeth to level {self.game_state.dungeon_level} of the dungeon.",
                        "color": Colors.WHITE
                    }
                ))
                self.map_manager.change_level()

            elif direction == "up" and current_tile.tile_type == TileType.STAIRS_UP:
                logger.debug("Found up stairs, ascending...")
                # Go up stairs
                if self.game_state.dungeon_level > 1:
                    old_level = self.game_state.dungeon_level
                    self.game_state.dungeon_level -= 1
                    logger.info(f"Player ascended to level {self.game_state.dungeon_level}")
                    
                    # Publish level change event
                    self.event_manager.publish(Event(
                        EventType.LEVEL_CHANGED,
                        {
                            "direction": "up",
                            "old_level": old_level,
                            "new_level": self.game_state.dungeon_level,
                            "player": self.game_state.player
                        }
                    ))
                    
                    self.event_manager.publish(Event(
                        EventType.MESSAGE_LOG,
                        {
                            "message": f"Thou climbeth to level {self.game_state.dungeon_level} of the dungeon.",
                            "color": Colors.WHITE
                        }
                    ))
                    self.map_manager.change_level()
                else:
                    logger.info("Player attempted to leave the dungeon")
                    if self.game_state.player_has_amulet:
                        # Victory!
                        self.event_manager.publish(Event(
                            EventType.MESSAGE_LOG,
                            {
                                "message": "Thou hast escaped with the Amulet of Yendor! Victory is thine!",
                                "color": Colors.YELLOW
                            }
                        ))
                        logger.info("Player won the game!")
                        self.game_state.game_won = True
                        self.game_state.running = False
                    else:
                        self.event_manager.publish(Event(
                            EventType.MESSAGE_LOG,
                            {
                                "message": "The Amulet of Yendor thou must possess to leave this place!",
                                "color": Colors.RED
                            }
                        ))
            else:
                # No stairs here
                if direction == "down":
                    self.event_manager.publish(Event(
                        EventType.MESSAGE_LOG,
                        {
                            "message": "No stairs descendeth from here.",
                            "color": Colors.YELLOW
                        }
                    ))
                else:
                    self.event_manager.publish(Event(
                        EventType.MESSAGE_LOG,
                        {
                            "message": "No stairs ascendeth from here.",
                            "color": Colors.YELLOW
                        }
                    ))
                logger.debug(
                    f"No {direction} stairs at current position. Current tile type: {current_tile.tile_type}"
                )

        except Exception as e:
            logger.error(f"Error handling stairs: {str(e)}", exc_info=True)
            self.event_manager.publish(Event(
                EventType.MESSAGE_LOG,
                {
                    "message": f"A strange force prevents thy movement: {str(e)}",
                    "color": Colors.RED
                }
            ))
            raise 