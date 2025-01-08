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
    # Example migration:
    # "0.9.0": ("1.0.0", lambda data: {
    #     **data,
    #     "new_field": "default_value"
    # })
}

class SaveVersionError(Exception):
    """Error raised when save data version is incompatible."""
    pass

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
    COMPRESSION_LEVEL = 9  # Maximum compression
    KEY_FILE = SAVE_DIR / '.key'
    SALT_SIZE = 16
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize save directory and encryption key."""
        cls.SAVE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Generate encryption key if it doesn't exist
        if not cls.KEY_FILE.exists():
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
        with cls.KEY_FILE.open('wb') as f:
            f.write(salt + key)
        
        logger.info("Generated new encryption key")
    
    @classmethod
    def _load_key(cls) -> bytes:
        """Load the encryption key."""
        with cls.KEY_FILE.open('rb') as f:
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
    def save_game(cls, data: Dict[str, Any], slot: int = 0) -> None:
        """
        Save game data to a file.
        
        Args:
            data: Game data to save
            slot: Save slot number
        """
        cls.initialize()
        save_path = cls.SAVE_DIR / f'save_{slot}.sav'
        
        try:
            # Add version information
            data['version'] = SAVE_VERSION
            
            # Convert data to JSON
            json_data = json.dumps(data, cls=GameEncoder)
            
            # Compress the JSON data
            compressed_data = cls._compress_data(json_data)
            
            # Encrypt the compressed data
            encrypted_data = cls._encrypt_data(compressed_data)
            
            # Write encrypted data to file
            with save_path.open('wb') as f:
                f.write(encrypted_data)
                
            logger.info(f"Game saved to slot {slot}")
            
            # Log compression and encryption stats
            original_size = len(json_data)
            compressed_size = len(compressed_data)
            final_size = len(encrypted_data)
            compression_ratio = (1 - compressed_size / original_size) * 100
            logger.debug(
                f"Save data stats: "
                f"Original size: {original_size} bytes, "
                f"Compressed size: {compressed_size} bytes, "
                f"Final size: {final_size} bytes, "
                f"Compression ratio: {compression_ratio:.1f}%"
            )
            
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
            
        Raises:
            SaveVersionError: If save data version is incompatible
        """
        save_path = cls.SAVE_DIR / f'save_{slot}.sav'
        
        if not save_path.exists():
            return None
            
        try:
            # Read encrypted data from file
            with save_path.open('rb') as f:
                encrypted_data = f.read()
            
            # Decrypt data
            compressed_data = cls._decrypt_data(encrypted_data)
            
            # Decompress data
            json_data = cls._decompress_data(compressed_data)
            
            # Parse JSON data
            data = json.loads(json_data, object_hook=object_hook)
            
            # Check version and migrate if necessary
            if 'version' not in data:
                raise SaveVersionError("Save data has no version information")
                
            if data['version'] != SAVE_VERSION:
                data = cls._migrate_save_data(data)
            
            logger.info(f"Game loaded from slot {slot}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to load game: {e}", exc_info=True)
            raise
            
    @classmethod
    def list_saves(cls) -> Dict[int, Tuple[Path, str]]:
        """
        List all available save files.
        
        Returns:
            Dictionary mapping slot numbers to tuples of (file path, version)
        """
        cls.initialize()
        saves = {}
        
        for save_file in cls.SAVE_DIR.glob('save_*.sav'):
            try:
                slot = int(save_file.stem.split('_')[1])
                # Try to read version information
                with save_file.open('rb') as f:
                    encrypted_data = f.read()
                compressed_data = cls._decrypt_data(encrypted_data)
                json_data = cls._decompress_data(compressed_data)
                data = json.loads(json_data)
                version = data.get('version', 'unknown')
                saves[slot] = (save_file, version)
            except Exception:
                # If we can't read the version, still include the save but mark it as unknown
                saves[slot] = (save_file, 'unknown')
                
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
        save_path = cls.SAVE_DIR / f'save_{slot}.sav'
        
        if save_path.exists():
            save_path.unlink()
            logger.info(f"Deleted save in slot {slot}")
            return True
            
        return False 