"""
Event logging system for the game.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from roguelike.core.event import Event, EventType

logger = logging.getLogger(__name__)

class EventLogger:
    """Event logging system that records and manages game events."""
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.events: List[Dict[str, Any]] = []
            self.session_start = datetime.now()
            # Set up events directory
            self.events_dir = Path(__file__).parents[3] / "data" / "logs" / "events"
            self.events_dir.mkdir(parents=True, exist_ok=True)
            self._initialized = True

    @classmethod
    def get_instance(cls) -> 'EventLogger':
        """Get the singleton instance of EventLogger."""
        return cls()

    def log_event(self, event: 'Event') -> None:
        """Log a game event.
        
        Args:
            event: The event to log
        """
        try:
            event_data = {
                "timestamp": datetime.now().isoformat(),
                "type": event.type.name,
                "data": event.data
            }
            self.events.append(event_data)
            logger.debug(f"Logged event: {event.type.name}")

        except Exception as e:
            logger.error(f"Error logging event: {str(e)}", exc_info=True)

    def save_session_log(self) -> None:
        """Save the current session's event log to a file."""
        try:
            # Create log file name with timestamp
            timestamp = self.session_start.strftime("%Y%m%d_%H%M%S")
            log_file = self.events_dir / f"game_events_{timestamp}.json"

            # Save events to file
            with log_file.open("w", encoding="utf-8") as f:
                json.dump({
                    "session_start": self.session_start.isoformat(),
                    "session_end": datetime.now().isoformat(),
                    "events": self.events
                }, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved event log to {log_file}")
            self.events.clear()

        except Exception as e:
            logger.error(f"Error saving event log: {str(e)}", exc_info=True)

    def get_events_by_type(self, event_type: 'EventType') -> List[Dict[str, Any]]:
        """Get all events of a specific type.
        
        Args:
            event_type: The type of events to get
            
        Returns:
            List of events of the specified type
        """
        return [event for event in self.events if event["type"] == event_type.name]

    def get_events_in_range(self, start: datetime, end: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get all events within a time range.
        
        Args:
            start: Start time of the range
            end: End time of the range (defaults to now)
            
        Returns:
            List of events within the specified time range
        """
        end = end or datetime.now()
        return [
            event for event in self.events
            if start <= datetime.fromisoformat(event["timestamp"]) <= end
        ]

    def clear_events(self) -> None:
        """Clear all recorded events."""
        self.events.clear()
        logger.debug("Cleared event log") 