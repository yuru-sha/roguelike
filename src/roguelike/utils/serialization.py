"""
Serialization utilities for saving and loading game data.
"""

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, Union

from roguelike.utils.logging import GameLogger

logger = GameLogger.get_instance()

T = TypeVar('T')

class GameEncoder(json.JSONEncoder):
    """Custom JSON encoder for game objects."""
    
    def default(self, obj: Any) -> Any:
        """Convert object to JSON serializable format."""
        if is_dataclass(obj):
            return {
                '__type__': obj.__class__.__name__,
                '__module__': obj.__class__.__module__,
                'data': asdict(obj)
            }
        if isinstance(obj, Enum):
            return {
                '__type__': 'Enum',
                '__enum__': obj.__class__.__name__,
                '__module__': obj.__class__.__module__,
                'name': obj.name
            }
        return super().default(obj)

def object_hook(dct: Dict[str, Any]) -> Any:
    """Convert JSON data back to Python objects."""
    if '__type__' not in dct:
        return dct
        
    if dct['__type__'] == 'Enum':
        module = __import__(dct['__module__'], fromlist=[dct['__enum__']])
        enum_class = getattr(module, dct['__enum__'])
        return enum_class[dct['name']]
        
    module = __import__(dct['__module__'], fromlist=[dct['__type__']])
    cls = getattr(module, dct['__type__'])
    
    if is_dataclass(cls):
        return cls(**dct['data'])
        
    return dct

class SaveManager:
    """Manage game save data."""
    
    SAVE_DIR = Path('data/save')
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize save directory."""
        cls.SAVE_DIR.mkdir(parents=True, exist_ok=True)
        
    @classmethod
    def save_game(cls, data: Dict[str, Any], slot: int = 0) -> None:
        """
        Save game data to a file.
        
        Args:
            data: Game data to save
            slot: Save slot number
        """
        cls.initialize()
        save_path = cls.SAVE_DIR / f'save_{slot}.json'
        
        try:
            with save_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, cls=GameEncoder, indent=2)
            logger.info(f"Game saved to slot {slot}")
        except Exception as e:
            logger.error(f"Failed to save game: {e}", exc_info=True)
            raise
            
    @classmethod
    def load_game(cls, slot: int = 0) -> Optional[Dict[str, Any]]:
        """
        Load game data from a file.
        
        Args:
            slot: Save slot number
            
        Returns:
            Loaded game data or None if file doesn't exist
        """
        save_path = cls.SAVE_DIR / f'save_{slot}.json'
        
        if not save_path.exists():
            return None
            
        try:
            with save_path.open('r', encoding='utf-8') as f:
                data = json.load(f, object_hook=object_hook)
            logger.info(f"Game loaded from slot {slot}")
            return data
        except Exception as e:
            logger.error(f"Failed to load game: {e}", exc_info=True)
            raise
            
    @classmethod
    def list_saves(cls) -> Dict[int, Path]:
        """
        List all available save files.
        
        Returns:
            Dictionary mapping slot numbers to save file paths
        """
        cls.initialize()
        saves = {}
        
        for save_file in cls.SAVE_DIR.glob('save_*.json'):
            try:
                slot = int(save_file.stem.split('_')[1])
                saves[slot] = save_file
            except (ValueError, IndexError):
                continue
                
        return saves
        
    @classmethod
    def delete_save(cls, slot: int) -> bool:
        """
        Delete a save file.
        
        Args:
            slot: Save slot number
            
        Returns:
            True if file was deleted, False if it didn't exist
        """
        save_path = cls.SAVE_DIR / f'save_{slot}.json'
        
        if save_path.exists():
            save_path.unlink()
            logger.info(f"Deleted save in slot {slot}")
            return True
            
        return False 