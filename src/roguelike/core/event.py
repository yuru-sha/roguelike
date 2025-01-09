"""
Event system implementation for the game.
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set
from weakref import WeakSet


class EventType(Enum):
    """Base event types for the game."""
    ENTITY_MOVED = auto()
    ENTITY_ATTACKED = auto()
    ENTITY_DIED = auto()
    ITEM_PICKED_UP = auto()
    ITEM_USED = auto()
    LEVEL_CHANGED = auto()
    GAME_STATE_CHANGED = auto()
    MESSAGE_LOG = auto()
    
    # Combat related events
    COMBAT_ATTACK = auto()
    COMBAT_DAMAGE = auto()
    COMBAT_MISS = auto()
    COMBAT_CRITICAL = auto()
    COMBAT_KILL = auto()
    COMBAT_EXPERIENCE = auto()
    COMBAT_LEVEL_UP = auto()
    EQUIPMENT_CHANGED = auto()


@dataclass
class Event:
    """Base event class."""
    type: EventType
    data: Dict[str, Any]


class EventManager:
    """Manages event publishing and subscription."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._subscribers: Dict[EventType, WeakSet] = {
                event_type: WeakSet() for event_type in EventType
            }
            # Import EventLogger here to avoid circular imports
            from roguelike.utils.event_logger import EventLogger
            self.event_logger = EventLogger.get_instance()
            self._initialized = True

    @classmethod
    def get_instance(cls) -> 'EventManager':
        """Get the singleton instance of EventManager."""
        return cls()

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Subscribe to an event type."""
        self._subscribers[event_type].add(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Unsubscribe from an event type."""
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        # Log the event
        self.event_logger.log_event(event)
        
        # Notify subscribers
        for callback in self._subscribers[event.type]:
            try:
                callback(event)
            except Exception as e:
                # TODO: Add proper error logging
                print(f"Error handling event {event.type}: {e}")

    def clear_subscribers(self, event_type: Optional[EventType] = None) -> None:
        """Clear all subscribers for a specific event type or all event types."""
        if event_type:
            self._subscribers[event_type].clear()
        else:
            for subscribers in self._subscribers.values():
                subscribers.clear()

    def save_event_log(self) -> None:
        """Save the current event log to a file."""
        self.event_logger.save_session_log()

    def get_events_by_type(self, event_type: EventType) -> List[Dict[str, Any]]:
        """Get all events of a specific type.
        
        Args:
            event_type: The type of events to get
            
        Returns:
            List of events of the specified type
        """
        return self.event_logger.get_events_by_type(event_type)

    def clear_events(self) -> None:
        """Clear all recorded events."""
        self.event_logger.clear_events() 