"""
Serialization utilities for saving and loading game data.
"""

import base64
import gzip
import json
import os
import threading
import time
import zlib
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import (Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar,
                    Union)

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from roguelike.utils.logging import GameLogger

logger = GameLogger.get_instance()

T = TypeVar("T")

# Current save data version
SAVE_VERSION = "1.1.0"

# Version migration functions
VERSION_MIGRATIONS: Dict[
    str, Tuple[str, Callable[[Dict[str, Any]], Dict[str, Any]]]
] = {
    "0.9.0": (
        "1.0.0",
        lambda data: {
            **data,
            "game_state": {
                **(data.get("game_state", {})),
                "auto_save_interval": 100,  # Add auto-save interval setting
                "backup_enabled": True,  # Add backup setting
            },
        },
    ),
    "1.0.0": (
        "1.1.0",
        lambda data: {
            **data,
            "entities": [
                {
                    **entity,
                    "components": {
                        **entity.get("components", {}),
                        # Add default values for new components
                        "StatusEffects": {"effects": {}},
                        "Vision": {
                            "range": 8,
                            "can_see_invisible": False,
                            "night_vision": False,
                        },
                        "Skills": {"available_skills": {}, "cooldowns": {}},
                        "Experience": {"level": 1, "current_xp": 0, "skill_points": 0},
                    },
                }
                for entity in data.get("entities", [])
            ],
        },
    ),
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
        required_fields = {
            "version",
            "game_state",
            "entities",
            "tiles",
            "player_id",
            "dungeon_level",
        }
        if not all(field in data for field in required_fields):
            logger.error(
                f"Missing required fields: {required_fields - set(data.keys())}"
            )
            return False

        # Validate version format
        version = data["version"]
        if not isinstance(version, str) or not version.count(".") == 2:
            logger.error("Invalid version format")
            return False

        # Validate game state
        game_state = data["game_state"]
        if not isinstance(game_state, dict):
            logger.error("Invalid game state format")
            return False

        # Validate entities
        entities = data["entities"]
        if not isinstance(entities, list):
            logger.error("Invalid entities format")
            return False

        for entity in entities:
            if not isinstance(entity, dict):
                logger.error("Invalid entity format")
                return False
            if "components" not in entity:
                logger.error("Entity missing components")
                return False

        # Validate tiles
        tiles = data["tiles"]
        if tiles is not None and not isinstance(tiles, list):
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


class SaveError(Exception):
    """Base class for save-related errors"""
    pass


class SaveFileNotFoundError(SaveError):
    """Error when save file is not found"""
    pass


class SaveFileCorruptedError(SaveError):
    """Error when save file is corrupted"""
    pass


class SaveVersionError(SaveError):
    """Error when save data version is incompatible"""
    pass


class SaveEncryptionError(SaveError):
    """Error related to encryption/decryption"""
    pass


class SaveCompressionError(SaveError):
    """Error related to compression/decompression"""
    pass


class SaveValidationError(SaveError):
    """Error when save data validation fails"""
    def __init__(self, message: str, validation_errors: Dict[str, str]):
        super().__init__(message)
        self.validation_errors = validation_errors


class GameEncoder(json.JSONEncoder):
    """Custom JSON encoder for game objects."""

    def default(self, obj: Any) -> Any:
        """Convert object to JSON serializable format."""
        if isinstance(obj, dict):
            return obj
        if is_dataclass(obj):
            return {
                "__type__": obj.__class__.__name__,
                "__module__": obj.__class__.__module__,
                "data": asdict(obj),
            }
        if isinstance(obj, Enum):
            return {
                "__type__": "Enum",
                "__enum__": obj.__class__.__name__,
                "__module__": obj.__class__.__module__,
                "name": obj.name,
                "value": obj.value,
            }
        if hasattr(obj, "to_dict"):
            return {
                "__type__": obj.__class__.__name__,
                "__module__": obj.__class__.__module__,
                "data": obj.to_dict(),
            }
        return super().default(obj)


def object_hook(dct: Dict[str, Any]) -> Any:
    """Convert JSON data back to Python objects."""
    if "__type__" not in dct:
        return dct

    if dct["__type__"] == "Enum":
        module = __import__(dct["__module__"], fromlist=[dct["__enum__"]])
        enum_class = getattr(module, dct["__enum__"])
        # 値からEnumを復元する
        if hasattr(enum_class, "from_value"):
            return enum_class.from_value(dct["value"])
        # 名前からEnumを復元する（フォールバック）
        return enum_class[dct["name"]]

    module = __import__(dct["__module__"], fromlist=[dct["__type__"]])
    cls = getattr(module, dct["__type__"])

    if is_dataclass(cls):
        return cls(**dct["data"])
    elif hasattr(cls, "from_dict"):
        return cls.from_dict(dct["data"])

    return dct


class SaveManager:
    """Manage game save data."""

    COMPRESSION_LEVEL = 9  # Maximum compression
    SALT_SIZE = 16
    _save_dir = Path("data/save")  # Default save directory

    # Compression settings
    COMPRESSION_CHUNK_SIZE = 16 * 1024  # 16KB chunks
    COMPRESSION_WBITS = 31  # Enable gzip format with maximum window size
    COMPRESSION_STRATEGY = zlib.Z_DEFAULT_STRATEGY  # Default compression strategy

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
        key_file = save_dir / ".key"
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
        key_file = cls.get_save_dir() / ".key"
        with key_file.open("wb") as f:
            f.write(salt + key)

        logger.info("Generated new encryption key")

    @classmethod
    def _load_key(cls) -> bytes:
        """Load the encryption key."""
        key_file = cls.get_save_dir() / ".key"
        with key_file.open("rb") as f:
            data = f.read()
            salt = data[: cls.SALT_SIZE]
            key = data[cls.SALT_SIZE :]
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
        Compress JSON data using gzip with optimized settings.

        Args:
            data: JSON string to compress

        Returns:
            Compressed data as bytes
        """
        compressor = zlib.compressobj(
            level=cls.COMPRESSION_LEVEL,
            method=zlib.DEFLATED,
            wbits=cls.COMPRESSION_WBITS,
            memLevel=9,  # Maximum memory level
            strategy=cls.COMPRESSION_STRATEGY,
        )

        chunks = []
        for i in range(0, len(data), cls.COMPRESSION_CHUNK_SIZE):
            chunk = data[i : i + cls.COMPRESSION_CHUNK_SIZE].encode("utf-8")
            if chunk:
                compressed_chunk = compressor.compress(chunk)
                if compressed_chunk:
                    chunks.append(compressed_chunk)

        chunks.append(compressor.flush())
        return b"".join(chunks)

    @classmethod
    def _decompress_data(cls, data: bytes) -> str:
        """
        Decompress gzipped data with optimized settings.

        Args:
            data: Compressed data

        Returns:
            Decompressed JSON string
        """
        decompressor = zlib.decompressobj(wbits=cls.COMPRESSION_WBITS)
        chunks = []

        for i in range(0, len(data), cls.COMPRESSION_CHUNK_SIZE):
            chunk = data[i : i + cls.COMPRESSION_CHUNK_SIZE]
            if chunk:
                decompressed_chunk = decompressor.decompress(chunk)
                if decompressed_chunk:
                    chunks.append(decompressed_chunk)

        chunks.append(decompressor.flush())
        return b"".join(chunks).decode("utf-8")

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
        current_version = data.get("version", "0.0.0")

        while current_version != SAVE_VERSION:
            if current_version not in VERSION_MIGRATIONS:
                raise SaveVersionError(
                    f"Cannot migrate save data from version {current_version} to {SAVE_VERSION}"
                )

            next_version, migration_func = VERSION_MIGRATIONS[current_version]
            data = migration_func(data)
            current_version = next_version
            logger.info(
                f"Migrated save data from version {current_version} to {next_version}"
            )

        return data

    @classmethod
    def save_game(cls, data: Dict[str, Any], slot: int = 0) -> bool:
        """
        Save game data to file with optimized compression.

        Args:
            data: Game data to save
            slot: Save slot number

        Returns:
            True if save successful, False otherwise

        Raises:
            SaveValidationError: セーブデータの検証に失敗した場合
            SaveCompressionError: データの圧縮に失敗した場合
            SaveEncryptionError: データの暗号化に失敗した場合
            SaveError: その他のセーブ関連エラー
        """
        try:
            # Validate data
            validation_errors = {}
            if "version" not in data:
                validation_errors["version"] = "Version is required"
            if "game_state" not in data:
                validation_errors["game_state"] = "Game state is required"
            if "entities" not in data:
                validation_errors["entities"] = "Entities are required"
            if "player_id" not in data:
                validation_errors["player_id"] = "Player ID is required"

            if validation_errors:
                raise SaveValidationError("Invalid save data", validation_errors)

            # Create backup if enabled
            if data.get("game_state", {}).get("backup_enabled", True):
                cls._create_backup(slot)

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
            try:
                json_data = json.dumps(data, cls=GameEncoder)
            except (TypeError, ValueError) as e:
                raise SaveError(f"Failed to serialize game data: {str(e)}")

            # Compress
            try:
                compressed = cls._compress_data(json_data)
            except Exception as e:
                raise SaveCompressionError(f"Failed to compress save data: {str(e)}")

            # Encrypt
            try:
                encrypted = cls._encrypt_data(compressed)
            except Exception as e:
                raise SaveEncryptionError(f"Failed to encrypt save data: {str(e)}")

            # Save to file
            save_path = cls.get_save_dir() / f"save_{slot}.sav"
            try:
                with save_path.open("wb") as f:
                    f.write(encrypted)
            except IOError as e:
                raise SaveError(f"Failed to write save file: {str(e)}")

            logger.info(f"Game saved to slot {slot}")
            return True

        except SaveError:
            raise
        except Exception as e:
            raise SaveError(f"Unexpected error during save: {str(e)}")

    @classmethod
    def load_game(cls, slot: int = 0) -> Optional[Dict[str, Any]]:
        """
        Load game data from file.

        Args:
            slot: Save slot number

        Returns:
            Loaded game data

        Raises:
            SaveFileNotFoundError: セーブファイルが見つからない場合
            SaveFileCorruptedError: セーブファイルが破損している場合
            SaveVersionError: セーブデータのバージョンが非互換の場合
            SaveEncryptionError: データの復号化に失敗した場合
            SaveCompressionError: データの展開に失敗した場合
            SaveError: その他のロード関連エラー
        """
        try:
            # Check if save file exists
            save_path = cls.get_save_dir() / f"save_{slot}.sav"
            if not save_path.exists():
                raise SaveFileNotFoundError(f"Save file not found: {save_path}")

            # Read encrypted data
            try:
                with save_path.open("rb") as f:
                    encrypted = f.read()
            except IOError as e:
                raise SaveFileCorruptedError(f"Failed to read save file: {str(e)}")

            # Decrypt
            try:
                compressed = cls._decrypt_data(encrypted)
            except Exception as e:
                raise SaveEncryptionError(f"Failed to decrypt save data: {str(e)}")

            # Decompress
            try:
                json_data = cls._decompress_data(compressed)
            except Exception as e:
                raise SaveCompressionError(f"Failed to decompress save data: {str(e)}")

            # Parse JSON
            try:
                data = json.loads(json_data, object_hook=object_hook)
            except json.JSONDecodeError as e:
                raise SaveFileCorruptedError(f"Failed to parse save data: {str(e)}")

            # Validate version
            if data.get("version") != SAVE_VERSION:
                try:
                    data = cls._migrate_save_data(data)
                except Exception as e:
                    raise SaveVersionError(f"Failed to migrate save data: {str(e)}")

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
                            try:
                                tiles_row.append(Tile.from_dict(tile_data))
                            except Exception as e:
                                raise SaveFileCorruptedError(
                                    f"Failed to convert tile data: {str(e)}"
                                )
                    tiles.append(tiles_row)
                data["tiles"] = tiles

            logger.info(f"Game loaded from slot {slot}")
            return data

        except SaveError:
            raise
        except Exception as e:
            raise SaveError(f"Unexpected error during load: {str(e)}")

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
        for path in save_dir.glob("save_*.sav"):
            try:
                # Extract slot number from filename
                slot = int(path.stem.split("_")[1].split(".")[0])
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
        save_path = cls.get_save_dir() / f"save_{slot}.sav"

        if save_path.exists():
            save_path.unlink()
            logger.info(f"Deleted save in slot {slot}")
            return True

        return False

    @classmethod
    def _compress_backup(cls, backup_path: Path) -> None:
        """
        バックアップファイルを圧縮する。
        圧縮後のファイルは .gz 拡張子が付加される。

        Args:
            backup_path: 圧縮するバックアップファイルのパス
        """
        try:
            compressed_path = backup_path.with_suffix(".sav.gz")
            with backup_path.open("rb") as f_in:
                with gzip.open(compressed_path, "wb", compresslevel=9) as f_out:
                    f_out.write(f_in.read())

            # 元のファイルを削除
            backup_path.unlink()
            logger.info(f"Compressed backup: {backup_path}")

        except Exception as e:
            logger.error(f"Failed to compress backup {backup_path}: {e}")
            if compressed_path.exists():
                compressed_path.unlink()

    @classmethod
    def _decompress_backup(cls, compressed_path: Path) -> bool:
        """
        圧縮されたバックアップファイルを展開する。

        Args:
            compressed_path: 展開する圧縮ファイルのパス

        Returns:
            展開に成功した場合はTrue、失敗した場合はFalse
        """
        try:
            decompressed_path = compressed_path.with_suffix("")
            with gzip.open(compressed_path, "rb") as f_in:
                with decompressed_path.open("wb") as f_out:
                    f_out.write(f_in.read())

            # 圧縮ファイルを削除
            compressed_path.unlink()
            logger.info(f"Decompressed backup: {compressed_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to decompress backup {compressed_path}: {e}")
            if decompressed_path.exists():
                decompressed_path.unlink()
            return False

    @classmethod
    def _create_backup(cls, slot: int) -> None:
        """
        セーブファイルのバックアップを作成する。
        最大5世代までのバックアップを保持し、自動的に圧縮する。

        Args:
            slot: セーブスロット番号
        """
        save_path = cls.get_save_dir() / f"save_{slot}.sav"
        if not save_path.exists():
            return

        # 既存のバックアップをローテーション
        for i in range(4, 0, -1):
            old_backup = cls.get_save_dir() / f"save_{slot}.bak{i}"
            old_compressed = old_backup.with_suffix(".sav.gz")
            new_backup = cls.get_save_dir() / f"save_{slot}.bak{i+1}"
            new_compressed = new_backup.with_suffix(".sav.gz")

            if old_backup.exists():
                old_backup.rename(new_backup)
            elif old_compressed.exists():
                old_compressed.rename(new_compressed)

        # 新しいバックアップを作成
        backup_path = cls.get_save_dir() / f"save_{slot}.bak1"
        save_path.rename(backup_path)

        # バックアップを圧縮
        cls._compress_backup(backup_path)
        logger.info(f"Created and compressed backup of save slot {slot}")

    @classmethod
    def restore_backup(cls, slot: int, backup_number: int = 1) -> bool:
        """
        指定したバックアップからセーブデータを復元する。
        圧縮されたバックアップの場合は自動的に展開する。

        Args:
            slot: セーブスロット番号
            backup_number: 復元するバックアップの世代番号（1-5）

        Returns:
            復元に成功した場合はTrue、失敗した場合はFalse

        Raises:
            SaveFileNotFoundError: 指定したバックアップが存在しない場合
        """
        if not 1 <= backup_number <= 5:
            raise ValueError("Backup number must be between 1 and 5")

        backup_path = cls.get_save_dir() / f"save_{slot}.bak{backup_number}"
        compressed_path = backup_path.with_suffix(".sav.gz")
        save_path = cls.get_save_dir() / f"save_{slot}.sav"

        # 圧縮/非圧縮のバックアップを確認
        if not backup_path.exists() and not compressed_path.exists():
            raise SaveFileNotFoundError(f"Backup file not found: {backup_path}")

        # 現在のセーブファイルを一時バックアップ
        if save_path.exists():
            temp_backup = cls.get_save_dir() / f"save_{slot}.tmp"
            save_path.rename(temp_backup)

        try:
            if compressed_path.exists():
                # 圧縮されたバックアップを展開
                if not cls._decompress_backup(compressed_path):
                    raise SaveError("Failed to decompress backup")

            # バックアップを復元
            backup_path.rename(save_path)
            logger.info(f"Restored backup {backup_number} for slot {slot}")

            # 一時バックアップを削除
            if temp_backup.exists():
                temp_backup.unlink()

            return True

        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            # 復元に失敗した場合、一時バックアップを戻す
            if temp_backup.exists():
                temp_backup.rename(save_path)
            return False

    @classmethod
    def list_backups(cls, slot: int) -> Dict[int, Path]:
        """
        指定したスロットの利用可能なバックアップを一覧表示する。
        圧縮されたバックアップも含める。

        Args:
            slot: セーブスロット番号

        Returns:
            バックアップ番号とパスのマッピング
        """
        backups = {}
        for i in range(1, 6):
            backup_path = cls.get_save_dir() / f"save_{slot}.bak{i}"
            compressed_path = backup_path.with_suffix(".sav.gz")
            if backup_path.exists():
                backups[i] = backup_path
            elif compressed_path.exists():
                backups[i] = compressed_path
        return backups

    @classmethod
    def verify_save_integrity(cls, slot: int) -> Tuple[bool, List[str]]:
        """
        セーブデータの整合性を検証する。

        Args:
            slot: セーブスロット番号

        Returns:
            (整合性チェックの結果, エラーメッセージのリスト)
        """
        errors = []
        try:
            data = cls.load_game(slot)
            if not data:
                return False, ["Failed to load save data"]

            # 必須フィールドの検証
            required_fields = {
                "version",
                "game_state",
                "entities",
                "player_id",
                "dungeon_level",
            }
            missing_fields = required_fields - set(data.keys())
            if missing_fields:
                errors.append(f"Missing required fields: {missing_fields}")

            # バージョン形式の検証
            if not isinstance(data.get("version", ""), str):
                errors.append("Invalid version format")

            # プレイヤーIDの検証
            if not isinstance(data.get("player_id", 0), int):
                errors.append("Invalid player ID format")

            # エンティティデータの検証
            entities = data.get("entities", [])
            if not isinstance(entities, list):
                errors.append("Invalid entities format")
            else:
                for i, entity in enumerate(entities):
                    if not isinstance(entity, dict) or "components" not in entity:
                        errors.append(f"Invalid entity format at index {i}")

            return len(errors) == 0, errors

        except Exception as e:
            return False, [f"Verification failed: {str(e)}"]

    @classmethod
    def auto_repair(cls, slot: int) -> Tuple[bool, List[str]]:
        """
        破損したセーブデータの自動修復を試みる。

        Args:
            slot: セーブスロット番号

        Returns:
            (修復の成功/失敗, 実行された修復アクションのリスト)
        """
        actions = []
        success = False

        try:
            # まず整合性チェックを実行
            is_valid, errors = cls.verify_save_integrity(slot)
            if is_valid:
                return True, ["Save data is valid, no repair needed"]

            # 最新のバックアップを探す
            backups = cls.list_backups(slot)
            if backups:
                latest_backup = min(backups.keys())
                if cls.restore_backup(slot, latest_backup):
                    actions.append(f"Restored from backup {latest_backup}")
                    is_valid, new_errors = cls.verify_save_integrity(slot)
                    if is_valid:
                        success = True
                        actions.append("Restored save data verified successfully")
                    else:
                        actions.append(f"Restored save data has errors: {new_errors}")
            else:
                actions.append("No backups available for restoration")

            if not success:
                actions.append("Automatic repair failed")

            return success, actions

        except Exception as e:
            return False, [f"Auto-repair failed: {str(e)}"]

    @classmethod
    def cleanup_old_backups(cls, max_age_days: int = 30) -> List[str]:
        """
        指定した日数より古いバックアップを削除する。

        Args:
            max_age_days: 保持する最大日数

        Returns:
            削除されたファイルのリスト
        """
        deleted_files = []
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        try:
            save_dir = cls.get_save_dir()
            # バックアップファイルを検索
            backup_pattern = "save_*.bak*"
            for backup_file in save_dir.glob(backup_pattern):
                try:
                    # ファイルの最終更新日時を取得
                    mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if mtime < cutoff_date:
                        backup_file.unlink()
                        deleted_files.append(str(backup_file))
                        logger.info(f"Deleted old backup: {backup_file}")
                except Exception as e:
                    logger.error(f"Failed to process backup file {backup_file}: {e}")

            return deleted_files

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            return deleted_files

    @classmethod
    def schedule_backup_cleanup(
        cls, interval_days: int = 7, max_age_days: int = 30
    ) -> None:
        """
        バックアップの定期的なクリーンアップをスケジュールする。

        Args:
            interval_days: クリーンアップの実行間隔（日数）
            max_age_days: バックアップの保持期間（日数）
        """

        def cleanup_task():
            while True:
                try:
                    deleted = cls.cleanup_old_backups(max_age_days)
                    if deleted:
                        logger.info(
                            f"Scheduled cleanup removed {len(deleted)} old backups"
                        )
                except Exception as e:
                    logger.error(f"Scheduled backup cleanup failed: {e}")

                # 次の実行まで待機
                time.sleep(interval_days * 24 * 60 * 60)

        # バックグラウンドスレッドでクリーンアップタスクを開始
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
        logger.info(f"Scheduled backup cleanup every {interval_days} days")

    @classmethod
    def get_backup_stats(cls) -> Dict[str, Any]:
        """
        バックアップの統計情報を取得する。

        Returns:
            統計情報を含む辞書
        """
        stats = {
            "total_backups": 0,
            "compressed_backups": 0,
            "total_size": 0,
            "compressed_size": 0,
            "oldest_backup": None,
            "newest_backup": None,
            "backup_by_slot": {},
        }

        try:
            save_dir = cls.get_save_dir()
            from datetime import datetime

            # バックアップファイルを検索
            for backup_file in save_dir.glob("save_*.bak*"):
                stats["total_backups"] += 1
                size = backup_file.stat().st_size
                mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)

                # スロット番号を抽出
                try:
                    slot = int(backup_file.stem.split("_")[1].split(".")[0])
                    if slot not in stats["backup_by_slot"]:
                        stats["backup_by_slot"][slot] = 0
                    stats["backup_by_slot"][slot] += 1
                except (ValueError, IndexError):
                    continue

                # 圧縮ファイルの統計
                if backup_file.suffix == ".gz":
                    stats["compressed_backups"] += 1
                    stats["compressed_size"] += size
                else:
                    stats["total_size"] += size

                # 最古・最新のバックアップを更新
                if stats["oldest_backup"] is None or mtime < stats["oldest_backup"]:
                    stats["oldest_backup"] = mtime
                if stats["newest_backup"] is None or mtime > stats["newest_backup"]:
                    stats["newest_backup"] = mtime

            return stats

        except Exception as e:
            logger.error(f"Failed to get backup stats: {e}")
            return stats
