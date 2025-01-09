"""
Serialization utilities for saving and loading game data.
"""

import json
import gzip
import base64
import os
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, Union, Tuple, Callable
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from roguelike.utils.logging import GameLogger

logger = GameLogger.get_instance()

T = TypeVar('T')

# Current save data version
SAVE_VERSION = "1.0.0"

# Version migration functions
VERSION_MIGRATIONS: Dict[str, Tuple[str, Callable[[Dict[str, Any]], Dict[str, Any]]]] = {
    "0.9.0": ("1.0.0", lambda data: {
        **data,
        "game_state": {
            **(data.get("game_state", {})),
            "auto_save_interval": 100,  # Add auto-save interval setting
            "backup_enabled": True,     # Add backup setting
        }
    })
}

def validate_save_data(data: Dict[str, Any]) -> bool:
    """
    Validate save data structure and content.
    
    Args:
        data: Save data to validate
        
    Returns:
        True if data is valid, False otherwise
    """
    try:
        # Check required fields
        required_fields = ["version", "game_state", "entities", "tiles", "player_id", "dungeon_level"]
        if not all(field in data for field in required_fields):
            logger.error("Missing required fields in save data")
            return False
            
        # Validate version format
        version = data["version"]
        if not isinstance(version, str) or not all(part.isdigit() for part in version.split(".")):
            logger.error(f"Invalid version format: {version}")
            return False
            
        # Validate game state
        game_state = data["game_state"]
        if not isinstance(game_state, dict):
            logger.error("Invalid game state format")
            return False
            
        # Validate entities
        entities = data["entities"]
        if not isinstance(entities, dict):
            logger.error("Invalid entities format")
            return False
            
        # Validate tiles
        tiles = data["tiles"]
        if not isinstance(tiles, list) or not all(isinstance(row, list) for row in tiles):
            logger.error("Invalid tiles format")
            return False
            
        # Validate player ID
        player_id = data["player_id"]
        if not isinstance(player_id, int):
            logger.error("Invalid player ID format")
            return False
            
        # Validate dungeon level
        dungeon_level = data["dungeon_level"]
        if not isinstance(dungeon_level, int) or dungeon_level < 1:
            logger.error("Invalid dungeon level")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error validating save data: {e}")
        return False

class SaveVersionError(Exception):
    """Error raised when save data version is incompatible."""
    pass

class GameEncoder(json.JSONEncoder):
    """Custom JSON encoder for game objects."""
    
    def default(self, obj: Any) -> Any:
        """Convert object to JSON serializable format."""
        if isinstance(obj, dict):
            return obj
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
                'name': obj.name,
                'value': obj.value
            }
        if hasattr(obj, 'to_dict'):
            return {
                '__type__': obj.__class__.__name__,
                '__module__': obj.__class__.__module__,
                'data': obj.to_dict()
            }
        return super().default(obj)

def object_hook(dct: Dict[str, Any]) -> Any:
    """Convert JSON data back to Python objects."""
    if '__type__' not in dct:
        return dct
        
    if dct['__type__'] == 'Enum':
        module = __import__(dct['__module__'], fromlist=[dct['__enum__']])
        enum_class = getattr(module, dct['__enum__'])
        # 値からEnumを復元する
        if hasattr(enum_class, 'from_value'):
            return enum_class.from_value(dct['value'])
        # 名前からEnumを復元する（フォールバック）
        return enum_class[dct['name']]
        
    module = __import__(dct['__module__'], fromlist=[dct['__type__']])
    cls = getattr(module, dct['__type__'])
    
    if is_dataclass(cls):
        return cls(**dct['data'])
    elif hasattr(cls, 'from_dict'):
        return cls.from_dict(dct['data'])
        
    return dct

class SaveManager:
    """Manage game save data."""
    
    COMPRESSION_LEVEL = 9  # Maximum compression
    SALT_SIZE = 16
    _save_dir = Path('data/save')  # デフォルトのセーブディレクトリ
    
    @classmethod
    def get_save_dir(cls) -> Path:
        """Get the save directory path."""
        return cls._save_dir
    
    @classmethod
    def set_save_dir(cls, path: Union[str, Path]) -> None:
        """Set the save directory path."""
        cls._save_dir = Path(path)
        cls.initialize()
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize save directory and encryption key."""
        save_dir = cls.get_save_dir()
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate encryption key if it doesn't exist
        key_file = save_dir / '.key'
        if not key_file.exists():
            cls._generate_key()
    
    @classmethod
    def _generate_key(cls) -> None:
        """Generate and save a new encryption key."""
        # Generate a random salt
        salt = os.urandom(cls.SALT_SIZE)
        
        # Use PBKDF2 to derive a key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(b"roguelike"))
        
        # Save salt and key
        key_file = cls.get_save_dir() / '.key'
        with key_file.open('wb') as f:
            f.write(salt + key)
        
        logger.info("Generated new encryption key")
    
    @classmethod
    def _load_key(cls) -> bytes:
        """Load the encryption key."""
        key_file = cls.get_save_dir() / '.key'
        with key_file.open('rb') as f:
            data = f.read()
            salt = data[:cls.SALT_SIZE]
            key = data[cls.SALT_SIZE:]
            return key
    
    @classmethod
    def _encrypt_data(cls, data: bytes) -> bytes:
        """
        Encrypt data using Fernet symmetric encryption.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data
        """
        key = cls._load_key()
        f = Fernet(key)
        return f.encrypt(data)
    
    @classmethod
    def _decrypt_data(cls, data: bytes) -> bytes:
        """
        Decrypt Fernet-encrypted data.
        
        Args:
            data: Encrypted data
            
        Returns:
            Decrypted data
        """
        key = cls._load_key()
        f = Fernet(key)
        return f.decrypt(data)
    
    @classmethod
    def _compress_data(cls, data: str) -> bytes:
        """
        Compress JSON data using gzip.
        
        Args:
            data: JSON string to compress
            
        Returns:
            Compressed data as bytes
        """
        return gzip.compress(data.encode('utf-8'), compresslevel=cls.COMPRESSION_LEVEL)
    
    @classmethod
    def _decompress_data(cls, data: bytes) -> str:
        """
        Decompress gzipped data.
        
        Args:
            data: Compressed data
            
        Returns:
            Decompressed JSON string
        """
        return gzip.decompress(data).decode('utf-8')
    
    @classmethod
    def _migrate_save_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate save data to current version.
        
        Args:
            data: Save data to migrate
            
        Returns:
            Migrated save data
            
        Raises:
            SaveVersionError: If save data cannot be migrated
        """
        current_version = data.get('version', '0.0.0')
        
        while current_version != SAVE_VERSION:
            if current_version not in VERSION_MIGRATIONS:
                raise SaveVersionError(
                    f"Cannot migrate save data from version {current_version} to {SAVE_VERSION}"
                )
            
            next_version, migration_func = VERSION_MIGRATIONS[current_version]
            data = migration_func(data)
            current_version = next_version
            logger.info(f"Migrated save data from version {current_version} to {next_version}")
        
        return data
    
    @classmethod
    def save_game(cls, data: Dict[str, Any], slot: int = 0) -> bool:
        """
        Save game data to file.
        
        Args:
            data: Game data to save
            slot: Save slot number
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Validate data
            if not validate_save_data(data):
                logger.error("Invalid save data")
                return False
            
            # Convert tiles to serializable format
            if "tiles" in data:
                tiles_data = []
                for row in data["tiles"]:
                    tiles_row = []
                    for tile in row:
                        if tile is None:
                            tiles_row.append(None)
                        elif isinstance(tile, dict):
                            tiles_row.append(tile)
                        else:
                            tiles_row.append(tile.to_dict())
                    tiles_data.append(tiles_row)
                data["tiles"] = tiles_data
            
            # Serialize to JSON
            json_data = json.dumps(data, cls=GameEncoder)
            
            # Compress
            compressed = cls._compress_data(json_data)
            
            # Encrypt
            encrypted = cls._encrypt_data(compressed)
            
            # Save to file
            save_path = cls.get_save_dir() / f"save_{slot}.sav"
            with save_path.open('wb') as f:
                f.write(encrypted)
            
            logger.info(f"Game saved to slot {slot}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving game: {e}")
            return False
    
    @classmethod
    def load_game(cls, slot: int = 0) -> Optional[Dict[str, Any]]:
        """
        Load game data from file.
        
        Args:
            slot: Save slot number
            
        Returns:
            Loaded game data or None if load failed
        """
        try:
            # Check if save file exists
            save_path = cls.get_save_dir() / f"save_{slot}.sav"
            if not save_path.exists():
                logger.error(f"Save file not found: {save_path}")
                return None
            
            # Read encrypted data
            with save_path.open('rb') as f:
                encrypted = f.read()
            
            # Decrypt
            compressed = cls._decrypt_data(encrypted)
            
            # Decompress
            json_data = cls._decompress_data(compressed)
            
            # Parse JSON
            data = json.loads(json_data, object_hook=object_hook)
            
            # Convert tiles back to Tile objects
            if "tiles" in data:
                from roguelike.world.map.tiles import Tile
                tiles_data = data["tiles"]
                tiles = []
                for row in tiles_data:
                    tiles_row = []
                    for tile_data in row:
                        if tile_data is None:
                            tiles_row.append(None)
                        else:
                            tiles_row.append(Tile.from_dict(tile_data))
                    tiles.append(tiles_row)
                data["tiles"] = tiles
            
            logger.info(f"Game loaded from slot {slot}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading game: {e}")
            return None
            
    @classmethod
    def list_saves(cls) -> Dict[int, Path]:
        """
        List all available save files.
        
        Returns:
            Dictionary mapping slot numbers to save file paths
        """
        save_dir = cls.get_save_dir()
        saves = {}
        
        # Create save directory if it doesn't exist
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # List all save files
        for path in save_dir.glob('save_*.sav'):
            try:
                # Extract slot number from filename
                slot = int(path.stem.split('_')[1].split('.')[0])
                saves[slot] = path
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
        save_path = cls.get_save_dir() / f'save_{slot}.sav'
        
        if save_path.exists():
            save_path.unlink()
            logger.info(f"Deleted save in slot {slot}")
            return True
            
        return False 