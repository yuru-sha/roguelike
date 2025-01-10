"""
Action handler for the game.

This module provides a centralized handler for all game actions.
"""

import logging
from typing import Optional, Any, Dict

from roguelike.core.constants import Colors, MAP_WIDTH, MAP_HEIGHT
from roguelike.core.event import EventManager, Event, EventType
from roguelike.world.entity.components.base import (
    Position,
    Fighter,
    Corpse,
    Renderable,
    Item,
    Inventory,
)
from roguelike.world.map.tiles import TileType
from .base import (
    MovementAction,
    UseStairsAction,
    UseItemAction,
    PickupAction,
    SearchAction,
    ReadAction,
    ThrowAction,
    ZapAction,
    IdentifyAction,
    DropAction,
)

logger = logging.getLogger(__name__)


class ActionHandler:
    """Centralized handler for all game actions."""

    def __init__(self, world: Any, game_state: Any, combat_system: Any):
        """Initialize the action handler.
        
        Args:
            world: The game world
            game_state: The current game state
            combat_system: The combat system
        """
        self.world = world
        self.game_state = game_state
        self.combat_system = combat_system
        self.event_manager = EventManager.get_instance()

    def handle_movement(self, action: MovementAction) -> Optional[str]:
        """Handle movement action.
        
        Args:
            action: The movement action
            
        Returns:
            Optional message about the movement result
        """
        try:
            player_pos = self.world.component_for_entity(
                self.game_state.player, Position
            )
            dest_x = player_pos.x + action.dx
            dest_y = player_pos.y + action.dy

            # Check bounds
            if not (0 <= dest_x < MAP_WIDTH and 0 <= dest_y < MAP_HEIGHT):
                return None

            # Check for entities
            for ent, (pos, fighter) in self.world.get_components(Position, Fighter):
                if pos.x == dest_x and pos.y == dest_y:
                    return self._handle_combat(ent)

            # Check terrain
            if self.game_state.dungeon.tiles[dest_y][dest_x].blocked:
                return None

            # Move player
            player_pos.x = dest_x
            player_pos.y = dest_y
            return None

        except Exception as e:
            logger.error(f"Error handling movement: {e}", exc_info=True)
            raise

    def handle_stairs(self, action: UseStairsAction) -> Optional[str]:
        """Handle stairs action.
        
        Args:
            action: The stairs action
            
        Returns:
            Message about the stairs result
        """
        try:
            player_pos = self.world.component_for_entity(
                self.game_state.player, Position
            )
            current_tile = self.game_state.dungeon.tiles[player_pos.y][player_pos.x]

            if current_tile.tile_type == TileType.STAIRS_DOWN:
                return self._handle_descend()
            elif current_tile.tile_type == TileType.STAIRS_UP:
                return self._handle_ascend()
            
            return "There are no stairs here."

        except Exception as e:
            logger.error(f"Error handling stairs: {e}", exc_info=True)
            raise

    def handle_pickup(self, action: PickupAction) -> Optional[str]:
        """Handle pickup action.
        
        Args:
            action: The pickup action
            
        Returns:
            Message about the pickup result
        """
        try:
            player_pos = self.world.component_for_entity(
                self.game_state.player, Position
            )
            player_inventory = self.world.component_for_entity(
                self.game_state.player, Inventory
            )

            # Find items at player's position
            for ent, (pos, _) in self.world.get_components(Position, Item):
                if pos.x == player_pos.x and pos.y == player_pos.y:
                    return self._handle_item_pickup(ent, player_inventory)

            return "Naught is here to take."

        except Exception as e:
            logger.error(f"Error handling pickup: {e}", exc_info=True)
            raise

    def handle_use_item(self, action: UseItemAction) -> Optional[str]:
        """Handle item use action.
        
        Args:
            action: The item use action
            
        Returns:
            Message about the item use result
        """
        try:
            item = self.world.component_for_entity(action.item_id, Item)
            if not item.use_function:
                return f"The {item.name} cannot be used."

            if item.targeting and not action.target_pos:
                return "No target selected."

            result = item.use_function(
                self.game_state.player,
                target_pos=action.target_pos,
                **item.use_args or {}
            )

            if result:
                self.event_manager.publish(
                    Event(
                        EventType.ITEM_USED,
                        {
                            "item": action.item_id,
                            "player": self.game_state.player,
                            "result": result,
                        },
                    )
                )
                return result

            return "The item fails to take effect."

        except Exception as e:
            logger.error(f"Error handling item use: {e}", exc_info=True)
            raise

    def _handle_combat(self, target: int) -> str:
        """Handle combat with target entity.
        
        Args:
            target: Target entity ID
            
        Returns:
            Combat result message
        """
        target_name = self.world.component_for_entity(target, Renderable).name
        damage = self.combat_system.calculate_damage(self.game_state.player, target)

        if damage > 0:
            fighter = self.world.component_for_entity(target, Fighter)
            xp = fighter.take_damage(damage)
            
            if fighter.hp <= 0:
                self.combat_system.handle_enemy_death(target, xp)
                return f"You attack {target_name} for {damage} damage and slay them!"
            
            return f"You attack {target_name} for {damage} damage!"
        
        return f"You attack {target_name} but do no damage!"

    def _handle_item_pickup(self, item: int, inventory: Inventory) -> str:
        """Handle picking up an item.
        
        Args:
            item: Item entity ID
            inventory: Player's inventory
            
        Returns:
            Pickup result message
        """
        item_name = self.world.component_for_entity(item, Renderable).name
        slot = inventory.add_item(item)

        if slot is None:
            return f"Thy pack is full, thou canst not carry the {item_name}!"

        self.world.remove_component(item, Position)
        return f"Thou dost acquire the {item_name}."

    def _handle_descend(self) -> str:
        """Handle descending stairs.
        
        Returns:
            Descent result message
        """
        self.game_state.change_level(self.game_state.dungeon_level + 1)
        return f"You descend to dungeon level {self.game_state.dungeon_level}."

    def _handle_ascend(self) -> str:
        """Handle ascending stairs.
        
        Returns:
            Ascent result message
        """
        if self.game_state.dungeon_level == 1:
            if self.game_state.player_has_amulet:
                self.game_state.check_victory_condition()
                return "You escape the dungeon with the Amulet of Yendor!"
            return "You need the Amulet of Yendor to escape!"

        self.game_state.change_level(self.game_state.dungeon_level - 1)
        return f"You ascend to dungeon level {self.game_state.dungeon_level}."

    def handle_search(self, action: SearchAction) -> Optional[str]:
        """Handle search action.
        
        Args:
            action: The search action
            
        Returns:
            Message about the search result
        """
        # TODO: Implement search functionality
        # - Get player position
        # - Check adjacent tiles for traps and secret doors
        # - Calculate success chance based on player stats
        # - Reveal discovered features
        try:
            player_pos = self.world.component_for_entity(
                self.game_state.player, Position
            )
            # Implementation will go here
            return "You search the surrounding area."

        except Exception as e:
            logger.error(f"Error handling search: {e}", exc_info=True)
            raise

    def handle_read(self, action: ReadAction) -> Optional[str]:
        """Handle read action.
        
        Args:
            action: The read action
            
        Returns:
            Message about the reading result
        """
        # TODO: Implement scroll reading
        # - Verify item is a scroll
        # - Apply scroll effects
        # - Handle cursed scrolls
        # - Remove scroll from inventory if consumed
        try:
            # Implementation will go here
            return "You begin to read the scroll."

        except Exception as e:
            logger.error(f"Error handling read: {e}", exc_info=True)
            raise

    def handle_throw(self, action: ThrowAction) -> Optional[str]:
        """Handle throw action.
        
        Args:
            action: The throw action
            
        Returns:
            Message about the throwing result
        """
        # TODO: Implement item throwing
        # - Calculate trajectory to target
        # - Handle different item types (weapons, potions, food)
        # - Apply effects on impact
        # - Handle item breaking/recovery
        try:
            # Implementation will go here
            return "You throw the item."

        except Exception as e:
            logger.error(f"Error handling throw: {e}", exc_info=True)
            raise

    def handle_zap(self, action: ZapAction) -> Optional[str]:
        """Handle zap action.
        
        Args:
            action: The zap action
            
        Returns:
            Message about the zapping result
        """
        # TODO: Implement wand zapping
        # - Verify item is a wand
        # - Calculate beam path
        # - Apply wand effects along path
        # - Decrease wand charges
        try:
            # Implementation will go here
            return "You zap the wand."

        except Exception as e:
            logger.error(f"Error handling zap: {e}", exc_info=True)
            raise

    def handle_identify(self, action: IdentifyAction) -> Optional[str]:
        """Handle identify action.
        
        Args:
            action: The identify action
            
        Returns:
            Message about the identification result
        """
        # TODO: Implement item identification
        # - Verify scroll of identify
        # - Select target item
        # - Reveal true properties
        # - Mark similar items as identified
        try:
            # Implementation will go here
            return "You identify the item."

        except Exception as e:
            logger.error(f"Error handling identify: {e}", exc_info=True)
            raise

    def handle_drop(self, action: DropAction) -> Optional[str]:
        """Handle drop action.
        
        Args:
            action: The drop action
            
        Returns:
            Message about the dropping result
        """
        # TODO: Implement item dropping
        # - Check for cursed equipment
        # - Remove from inventory
        # - Place on ground at player position
        # - Handle stacking with existing items
        try:
            # Implementation will go here
            return "You drop the item."

        except Exception as e:
            logger.error(f"Error handling drop: {e}", exc_info=True)
            raise 