"""
Base action classes for the game.

This module defines the base action hierarchy for all game actions.
Actions are divided into several categories:
- GameAction: Basic game system actions (movement, wait, quit)
- ItemAction: Item-related actions (pickup, use, equip)
- DungeonAction: Dungeon interaction actions (stairs, doors, traps)
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Dict, Any
import logging

if TYPE_CHECKING:
    from roguelike.core.engine import Engine

logger = logging.getLogger(__name__)


class Action:
    """Base class for all actions in the game."""

    def perform(self, engine: "Engine") -> Optional[str]:
        """Perform the action.
        
        Args:
            engine: Game engine instance
            
        Returns:
            Optional message to display
        """
        raise NotImplementedError()


@dataclass
class GameAction(Action):
    """Base class for game system actions."""
    pass


@dataclass
class ItemAction(Action):
    """Base class for item-related actions."""
    item_id: int


@dataclass
class DungeonAction(Action):
    """Base class for dungeon interaction actions."""
    pass


@dataclass
class MovementAction(GameAction):
    """Action for moving in a direction."""
    dx: int
    dy: int

    def perform(self, engine: "Engine") -> Optional[str]:
        """Perform movement action.
        
        Args:
            engine: Game engine instance
            
        Returns:
            Optional message about the movement result
        """
        try:
            return engine.action_handler.handle_movement(self)
        except Exception as e:
            logger.error(f"Error in movement action: {e}", exc_info=True)
            return f"Movement failed: {str(e)}"


@dataclass
class WaitAction(GameAction):
    """Action for doing nothing and waiting a turn."""

    def perform(self, engine: "Engine") -> Optional[str]:
        """Perform wait action.
        
        Args:
            engine: Game engine instance
            
        Returns:
            Optional message about waiting
        """
        return None  # Just pass the turn


@dataclass
class QuitAction(GameAction):
    """Action for quitting the game."""

    def perform(self, engine: "Engine") -> Optional[str]:
        """Perform quit action.
        
        Args:
            engine: Game engine instance
            
        Returns:
            Quit message
        """
        engine.game_state.running = False
        return "Quitting game..."


@dataclass
class PickupAction(ItemAction):
    """Action for picking up an item."""

    def perform(self, engine: "Engine") -> Optional[str]:
        """Perform pickup action.
        
        Args:
            engine: Game engine instance
            
        Returns:
            Message about pickup result
        """
        try:
            return engine.action_handler.handle_pickup(self)
        except Exception as e:
            logger.error(f"Error in pickup action: {e}", exc_info=True)
            return f"Pickup failed: {str(e)}"


@dataclass
class UseItemAction(ItemAction):
    """Action for using an item."""
    target_pos: Optional[tuple[int, int]] = None

    def perform(self, engine: "Engine") -> Optional[str]:
        """Perform item use action.
        
        Args:
            engine: Game engine instance
            
        Returns:
            Message about item use result
        """
        try:
            return engine.action_handler.handle_use_item(self)
        except Exception as e:
            logger.error(f"Error in use item action: {e}", exc_info=True)
            return f"Item use failed: {str(e)}"


@dataclass
class UseStairsAction(DungeonAction):
    """Action for using stairs."""

    def perform(self, engine: "Engine") -> Optional[str]:
        """Perform stairs use action.
        
        Args:
            engine: Game engine instance
            
        Returns:
            Message about stairs use result
        """
        try:
            return engine.action_handler.handle_stairs(self)
        except Exception as e:
            logger.error(f"Error in stairs action: {e}", exc_info=True)
            return f"Stairs use failed: {str(e)}"


@dataclass
class SearchAction(GameAction):
    """Action for searching adjacent squares for traps and secret doors."""

    def perform(self, engine: "Engine") -> Optional[str]:
        """Perform search action.
        
        Args:
            engine: Game engine instance
            
        Returns:
            Message about search result
        """
        # TODO: Check adjacent squares for traps and secret doors
        # - Reveal hidden traps within 1 tile radius
        # - Discover secret doors within 1 tile radius
        # - Chance based on player's level and stats
        try:
            return engine.action_handler.handle_search(self)
        except Exception as e:
            logger.error(f"Error in search action: {e}", exc_info=True)
            return f"Search failed: {str(e)}"


@dataclass
class ReadAction(ItemAction):
    """Action for reading scrolls."""

    def perform(self, engine: "Engine") -> Optional[str]:
        """Perform read action.
        
        Args:
            engine: Game engine instance
            
        Returns:
            Message about reading result
        """
        # TODO: Handle scroll reading
        # - Check if item is a scroll
        # - Apply scroll effects
        # - Handle cursed scrolls
        try:
            return engine.action_handler.handle_read(self)
        except Exception as e:
            logger.error(f"Error in read action: {e}", exc_info=True)
            return f"Reading failed: {str(e)}"


@dataclass
class ThrowAction(ItemAction):
    """Action for throwing items."""
    target_pos: tuple[int, int]

    def perform(self, engine: "Engine") -> Optional[str]:
        """Perform throw action.
        
        Args:
            engine: Game engine instance
            
        Returns:
            Message about throwing result
        """
        # TODO: Handle item throwing
        # - Calculate trajectory
        # - Handle weapon throwing (daggers, darts)
        # - Handle potion throwing (break and apply effects)
        # - Handle food throwing (feed pets)
        try:
            return engine.action_handler.handle_throw(self)
        except Exception as e:
            logger.error(f"Error in throw action: {e}", exc_info=True)
            return f"Throw failed: {str(e)}"


@dataclass
class ZapAction(ItemAction):
    """Action for zapping wands."""
    target_pos: tuple[int, int]

    def perform(self, engine: "Engine") -> Optional[str]:
        """Perform zap action.
        
        Args:
            engine: Game engine instance
            
        Returns:
            Message about zapping result
        """
        # TODO: Handle wand zapping
        # - Check if item is a wand
        # - Calculate beam trajectory
        # - Apply wand effects
        # - Handle wand charges
        try:
            return engine.action_handler.handle_zap(self)
        except Exception as e:
            logger.error(f"Error in zap action: {e}", exc_info=True)
            return f"Zap failed: {str(e)}"


@dataclass
class IdentifyAction(ItemAction):
    """Action for identifying items."""

    def perform(self, engine: "Engine") -> Optional[str]:
        """Perform identify action.
        
        Args:
            engine: Game engine instance
            
        Returns:
            Message about identification result
        """
        # TODO: Handle item identification
        # - Check if scroll of identify
        # - Select item to identify
        # - Reveal true item name and properties
        # - Mark similar items as identified
        try:
            return engine.action_handler.handle_identify(self)
        except Exception as e:
            logger.error(f"Error in identify action: {e}", exc_info=True)
            return f"Identification failed: {str(e)}"


@dataclass
class DropAction(ItemAction):
    """Action for dropping items."""

    def perform(self, engine: "Engine") -> Optional[str]:
        """Perform drop action.
        
        Args:
            engine: Game engine instance
            
        Returns:
            Message about dropping result
        """
        # TODO: Handle item dropping
        # - Check if item can be dropped
        # - Handle cursed equipment
        # - Place item on ground
        # - Remove from inventory
        try:
            return engine.action_handler.handle_drop(self)
        except Exception as e:
            logger.error(f"Error in drop action: {e}", exc_info=True)
            return f"Drop failed: {str(e)}" 