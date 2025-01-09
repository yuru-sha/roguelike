import gzip
import json
import logging
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import esper
import numpy as np
import pytest

from roguelike.core.constants import MAP_HEIGHT, MAP_WIDTH, Colors
from roguelike.core.engine import Engine
from roguelike.world.entity.components.base import (Corpse, Equipment,
                                                    EquipmentSlot,
                                                    EquipmentSlots, Experience,
                                                    Fighter, Item, Position,
                                                    Renderable, RenderOrder,
                                                    Skills, StatusEffect,
                                                    StatusEffects, Vision,
                                                    WeaponType)
from roguelike.world.map.tiles import Tile, TileType

logger = logging.getLogger(__name__)


def initialize_test_map(engine):
    """Initialize a test map.

    Args:
        engine: Game engine instance
    """
    # Initialize map
    engine.tiles = np.empty((MAP_HEIGHT, MAP_WIDTH), dtype=object)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            tile = Tile(TileType.FLOOR)
            engine.tiles[y][x] = tile
            logger.debug(f"Created tile at ({x}, {y}): {tile.tile_type}")

    # Initialize FOV map
    engine._initialize_fov()
    logger.debug("FOV map initialized")


def test_save_load_basic_entity():
    """Test saving and loading basic entities."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        # Create test engine instance
        engine = Engine(skip_lock_check=True)
        initialize_test_map(engine)

        # Create player entity
        player = engine.world.create_entity()
        engine.world.add_component(player, Position(x=5, y=5))
        engine.world.add_component(
            player,
            Renderable(
                char="@",
                color=Colors.WHITE,
                render_order=RenderOrder.ACTOR,
                name="Player",
            ),
        )
        engine.player = player

        # Create test entity
        test_entity = engine.world.create_entity()
        engine.world.add_component(test_entity, Position(x=10, y=20))
        engine.world.add_component(
            test_entity,
            Renderable(
                char="@",
                color=Colors.WHITE,
                render_order=RenderOrder.ACTOR,
                name="Test Entity",
            ),
        )

        # Save game
        assert engine.save_game(slot=0)

        # Create new engine and load
        new_engine = Engine(skip_lock_check=True)
        assert new_engine.load_game(slot=0)

        # Verify entities
        entities = list(new_engine.world.get_components(Position, Renderable))
        assert len(entities) == 2

        # Verify player entity
        player_entities = [
            (eid, pos, render)
            for eid, (pos, render) in entities
            if eid == new_engine.player
        ]
        assert len(player_entities) == 1
        player_id, player_pos, player_render = player_entities[0]
        assert player_pos.x == 5 and player_pos.y == 5
        assert player_render.char == "@"
        assert player_render.name == "Player"

        # Verify test entity
        test_entities = [
            (eid, pos, render)
            for eid, (pos, render) in entities
            if eid != new_engine.player
        ]
        assert len(test_entities) == 1
        entity_id, pos, render = test_entities[0]
        assert pos.x == 10 and pos.y == 20
        assert render.char == "@"
        assert render.name == "Test Entity"


def test_save_load_complex_entity():
    """Test saving and loading entities with complex components."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        engine = Engine(skip_lock_check=True)
        initialize_test_map(engine)

        # Create player entity
        player = engine.world.create_entity()
        engine.world.add_component(player, Position(x=5, y=5))
        engine.world.add_component(
            player,
            Renderable(
                char="@",
                color=Colors.WHITE,
                render_order=RenderOrder.ACTOR,
                name="Player",
            ),
        )
        engine.player = player

        # Create complex entity (orc corpse)
        corpse = engine.world.create_entity()
        engine.world.add_component(corpse, Position(x=5, y=15))
        engine.world.add_component(
            corpse,
            Renderable(
                char="%",
                color=Colors.RED,
                render_order=RenderOrder.CORPSE,
                name="remains of orc",
            ),
        )
        engine.world.add_component(corpse, Corpse("orc"))
        engine.world.add_component(corpse, Item(name="remains of orc"))

        # Add status effects
        status_effects = StatusEffects()
        status_effects.add_effect(StatusEffect.POISONED, 3, 2)
        engine.world.add_component(player, status_effects)

        # Add vision
        vision = Vision(range=8, can_see_invisible=True, night_vision=True)
        engine.world.add_component(player, vision)

        # Save game
        assert engine.save_game(slot=1)

        # Create new engine and load
        new_engine = Engine(skip_lock_check=True)
        assert new_engine.load_game(slot=1)

        # Verify player entity
        player_components = list(
            new_engine.world.get_components(Position, Renderable, StatusEffects, Vision)
        )
        assert len(player_components) == 1
        player_id, (pos, render, status, vision) = player_components[0]
        assert player_id == new_engine.player
        assert pos.x == 5 and pos.y == 5
        assert render.char == "@"
        assert StatusEffect.POISONED in status.effects
        assert vision.can_see_invisible is True

        # Verify corpse entity
        corpse_entities = list(
            new_engine.world.get_components(Position, Renderable, Corpse, Item)
        )
        assert len(corpse_entities) == 1
        entity_id, (pos, render, corpse, item) = corpse_entities[0]
        assert pos.x == 5 and pos.y == 15
        assert render.char == "%"
        assert corpse.original_name == "orc"
        assert item.name == "remains of orc"


def test_save_load_equipment():
    """Test saving and loading equipment."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        engine = Engine(skip_lock_check=True)
        initialize_test_map(engine)

        # Create player with equipment
        player = engine.world.create_entity()
        engine.world.add_component(player, Position(x=10, y=10))
        engine.world.add_component(
            player,
            Renderable(
                char="@",
                color=Colors.WHITE,
                render_order=RenderOrder.ACTOR,
                name="Player",
            ),
        )
        equipment_slots = EquipmentSlots()
        engine.world.add_component(player, equipment_slots)

        # Create sword
        sword = engine.world.create_entity()
        engine.world.add_component(sword, Position(x=11, y=10))
        engine.world.add_component(
            sword,
            Renderable(
                char="/",
                color=Colors.LIGHT_BLUE,
                render_order=RenderOrder.ITEM,
                name="Short Sword",
            ),
        )
        sword_equipment = Equipment(
            equipment_slot=EquipmentSlot.MAIN_HAND,
            power_bonus=2,
            weapon_type=WeaponType.ONE_HANDED,
        )
        engine.world.add_component(sword, sword_equipment)

        # Equip sword
        equipment_slots.equip(EquipmentSlot.MAIN_HAND, sword, engine.world)
        engine.player = player

        # Save game
        assert engine.save_game(slot=2)

        # Create new engine and load
        new_engine = Engine(skip_lock_check=True)
        assert new_engine.load_game(slot=2)

        # Verify equipment
        player_equipment = list(new_engine.world.get_components(EquipmentSlots))
        assert len(player_equipment) == 1
        player_id, (equipment_slots,) = player_equipment[0]
        assert player_id == new_engine.player

        main_hand_id = equipment_slots.get_equipped(EquipmentSlot.MAIN_HAND)
        assert main_hand_id is not None
        main_hand = new_engine.world.component_for_entity(main_hand_id, Equipment)
        assert main_hand.slot == EquipmentSlot.MAIN_HAND
        assert main_hand.power_bonus == 2
        assert main_hand.weapon_type == WeaponType.ONE_HANDED


def test_save_validation_errors():
    """Test validation errors for save data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        # Create invalid data missing required fields
        invalid_data = {"game_state": {}, "entities": []}

        with pytest.raises(SaveValidationError) as exc_info:
            SaveManager.save_game(invalid_data)

        assert "version" in exc_info.value.validation_errors
        assert "player_id" in exc_info.value.validation_errors


def test_save_file_not_found():
    """Test loading non-existent save file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        with pytest.raises(SaveFileNotFoundError):
            SaveManager.load_game(slot=999)


def test_save_file_corrupted():
    """Test loading corrupted save file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        # Write corrupted data
        save_path = Path(temp_dir) / "save_0.sav"
        with save_path.open("wb") as f:
            f.write(b"corrupted data")

        with pytest.raises(SaveFileCorruptedError):
            SaveManager.load_game(slot=0)


def test_save_version_error():
    """Test incompatible save version handling."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        engine = Engine(skip_lock_check=True)
        initialize_test_map(engine)

        # Create player entity
        player = engine.world.create_entity()
        engine.world.add_component(player, Position(x=5, y=5))
        engine.player = player

        # Create data with old version
        save_data = {
            "version": "0.0.1",  # Non-existent version
            "game_state": {},
            "entities": [],
            "tiles": None,
            "player_id": player,
            "dungeon_level": 1,
        }

        with pytest.raises(SaveVersionError):
            SaveManager.save_game(save_data)


def test_save_compression_error():
    """Test compression error handling."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        # Create uncompressable data
        class UncompressableObject:
            def __repr__(self):
                raise Exception("Compression test error")

        invalid_data = {
            "version": "1.1.0",
            "game_state": {"uncompressable": UncompressableObject()},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }

        with pytest.raises(SaveCompressionError):
            SaveManager.save_game(invalid_data)


def test_save_encryption_error():
    """Test encryption error handling."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        # Corrupt encryption key file
        key_file = Path(temp_dir) / ".key"
        with key_file.open("wb") as f:
            f.write(b"invalid key")

        valid_data = {
            "version": "1.1.0",
            "game_state": {},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }

        with pytest.raises(SaveEncryptionError):
            SaveManager.save_game(valid_data)


def test_backup_rotation():
    """Test backup rotation functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        # Create test data
        valid_data = {
            "version": "1.1.0",
            "game_state": {},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }

        # Create multiple saves to trigger backup rotation
        for i in range(6):
            SaveManager.save_game(valid_data)

        # Verify backup files
        backups = SaveManager.list_backups(0)
        assert len(backups) == 5  # Maximum 5 generations of backups
        for i in range(1, 6):
            assert i in backups


def test_backup_restoration():
    """Test backup restoration functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        # Create original save data
        original_data = {
            "version": "1.1.0",
            "game_state": {"value": "original"},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }
        SaveManager.save_game(original_data)

        # Overwrite with corrupted data
        corrupted_data = {
            "version": "1.1.0",
            "game_state": {"value": "corrupted"},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }
        SaveManager.save_game(corrupted_data)

        # Restore from backup
        assert SaveManager.restore_backup(0, 1)

        # Verify restored data
        restored_data = SaveManager.load_game(0)
        assert restored_data["game_state"]["value"] == "original"


def test_save_integrity_verification():
    """Test save data integrity verification."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        # Test valid data
        valid_data = {
            "version": "1.1.0",
            "game_state": {},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }
        SaveManager.save_game(valid_data)

        # Verify integrity
        is_valid, errors = SaveManager.verify_save_integrity(0)
        assert is_valid
        assert len(errors) == 0

        # Test invalid data
        invalid_data = {
            "version": "1.1.0",
            "game_state": {},
            # Missing entities field
            "tiles": None,
            "player_id": "invalid",  # Invalid type
            "dungeon_level": 1,
        }
        SaveManager.save_game(invalid_data)

        # Verify integrity
        is_valid, errors = SaveManager.verify_save_integrity(0)
        assert not is_valid
        assert len(errors) > 0
        assert any("entities" in error for error in errors)
        assert any("player ID" in error for error in errors)


def test_auto_repair():
    """Test automatic repair functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        # Create valid save
        valid_data = {
            "version": "1.1.0",
            "game_state": {"value": "original"},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }
        SaveManager.save_game(valid_data)

        # Corrupt save file
        save_path = Path(temp_dir) / "save_0.sav"
        with save_path.open("wb") as f:
            f.write(b"corrupted data")

        # Run auto repair
        success, actions = SaveManager.auto_repair(0)
        assert success
        assert any("Restored from backup" in action for action in actions)
        assert any("verified successfully" in action for action in actions)

        # Verify repaired data
        restored_data = SaveManager.load_game(0)
        assert restored_data["game_state"]["value"] == "original"


def test_save_version_compatibility():
    """Test save data version compatibility."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        # Create old version data
        old_data = {
            "version": "1.0.0",  # Old version
            "game_state": {},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }

        # Run version check
        with pytest.raises(SaveVersionError):
            SaveManager.validate_version(old_data)

        # Test migration
        migrated_data = SaveManager.migrate_save_data(old_data)
        assert migrated_data["version"] == "1.1.0"  # Latest version


def test_save_data_compression_ratio():
    """Test save data compression ratio."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        # Create large data
        large_data = {
            "version": "1.1.0",
            "game_state": {"large_array": [i for i in range(1000)]},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }

        # Calculate uncompressed size
        uncompressed_size = len(json.dumps(large_data).encode())

        # Save data
        SaveManager.save_game(large_data)

        # Get compressed file size
        save_path = Path(temp_dir) / "save_0.sav"
        compressed_size = save_path.stat().st_size

        # Check compression ratio
        compression_ratio = compressed_size / uncompressed_size
        assert compression_ratio < 0.5  # Expect at least 50% compression


def test_save_data_encryption():
    """Test save data encryption."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        test_data = {
            "version": "1.1.0",
            "game_state": {"secret": "sensitive_data"},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }

        # Save data
        SaveManager.save_game(test_data)

        # Read raw file contents
        save_path = Path(temp_dir) / "save_0.sav"
        with save_path.open("rb") as f:
            raw_data = f.read()

        # Verify sensitive data is not in plain text
        assert b"sensitive_data" not in raw_data


def test_save_data_recovery_with_checksum():
    """Test save data recovery using checksums."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        original_data = {
            "version": "1.1.0",
            "game_state": {"value": "important"},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }

        # Save data
        SaveManager.save_game(original_data)

        # Corrupt file
        save_path = Path(temp_dir) / "save_0.sav"
        with save_path.open("rb+") as f:
            f.seek(-10, 2)  # Go to 10 bytes before end
            f.write(b"corrupted")

        # Detect corruption using checksum
        is_valid, errors = SaveManager.verify_save_integrity(0)
        assert not is_valid
        assert any("checksum" in error for error in errors)

        # Recover from latest valid backup
        recovered = SaveManager.restore_latest_valid_backup(0)
        assert recovered

        # Verify recovered data
        loaded_data = SaveManager.load_game(0)
        assert loaded_data["game_state"]["value"] == "important"


def test_save_data_concurrent_access():
    """Test concurrent save data access."""
    with tempfile.TemporaryDirectory() as temp_dir:
        import threading

        SaveManager.set_save_dir(temp_dir)

        def save_operation(slot: int):
            data = {
                "version": "1.1.0",
                "game_state": {"thread_id": slot},
                "entities": [],
                "tiles": None,
                "player_id": 1,
                "dungeon_level": 1,
            }
            SaveManager.save_game(data, slot=slot)

        # Create multiple threads for concurrent saves
        threads = []
        for i in range(5):
            thread = threading.Thread(target=save_operation, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify each slot's data
        for i in range(5):
            loaded_data = SaveManager.load_game(slot=i)
            assert loaded_data["game_state"]["thread_id"] == i


def test_security_config():
    """Test security configuration."""
    config = SecurityConfig(
        key_rotation_days=15,
        key_iterations=150000,
        checksum_algorithm="sha512",
        temp_file_permissions=0o400
    )
    SaveManager.configure_security(config)

    # Verify configuration
    assert SaveManager._security_config.key_rotation_days == 15
    assert SaveManager._security_config.key_iterations == 150000
    assert SaveManager._security_config.checksum_algorithm == "sha512"
    assert SaveManager._security_config.temp_file_permissions == 0o400


def test_key_rotation():
    """Test encryption key rotation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        # Create initial save
        data = create_test_save_data()
        assert SaveManager.save_game(data, slot=0)

        # Store original key
        key_file = Path(temp_dir) / ".key"
        with key_file.open("r") as f:
            original_key_data = json.load(f)

        # Simulate key expiration
        key_data = original_key_data.copy()
        key_data["created"] = (
            datetime.now() - timedelta(days=SaveManager._security_config.key_rotation_days + 1)
        ).isoformat()
        with key_file.open("w") as f:
            json.dump(key_data, f)

        # Load game to trigger rotation
        loaded_data = SaveManager.load_game(slot=0)
        assert loaded_data is not None

        # Verify key rotation
        with key_file.open("r") as f:
            new_key_data = json.load(f)
        assert new_key_data["created"] != original_key_data["created"]
        assert new_key_data["key"] != original_key_data["key"]


def test_checksum_verification():
    """Test save data checksum verification."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        # Create save with checksum
        data = create_test_save_data()
        assert SaveManager.save_game(data, slot=0)

        # Corrupt save file
        save_path = Path(temp_dir) / "save_0.sav"
        with save_path.open("rb+") as f:
            f.seek(-10, 2)  # Go to 10 bytes before end
            f.write(b"corrupted")

        # Attempt to load corrupted save
        with pytest.raises(SaveFileCorruptedError) as exc_info:
            SaveManager.load_game(slot=0)
        assert "checksum mismatch" in str(exc_info.value)


def test_concurrent_save_load():
    """Test concurrent save/load operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        def save_operation(slot: int):
            data = create_test_save_data()
            data["slot_id"] = slot
            assert SaveManager.save_game(data, slot=slot)

        def load_operation(slot: int):
            data = SaveManager.load_game(slot=slot)
            assert data is not None
            assert data["slot_id"] == slot

        # Create multiple threads for concurrent operations
        threads = []
        for i in range(5):
            save_thread = threading.Thread(target=save_operation, args=(i,))
            load_thread = threading.Thread(target=load_operation, args=(i,))
            threads.extend([save_thread, load_thread])

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()


def test_large_save_data():
    """Test handling of large save data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        # Create large test data
        large_data = create_test_save_data()
        large_data["large_array"] = list(range(10000))  # Add large array
        large_data["nested_data"] = {
            str(i): {
                "value": i,
                "data": "x" * 1000  # Add large strings
            }
            for i in range(100)
        }

        # Save large data
        assert SaveManager.save_game(large_data, slot=0)

        # Load and verify
        loaded_data = SaveManager.load_game(slot=0)
        assert loaded_data is not None
        assert len(loaded_data["large_array"]) == 10000
        assert len(loaded_data["nested_data"]) == 100


def test_save_file_permissions():
    """Test save file permissions."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        # Configure restrictive permissions
        config = SecurityConfig(temp_file_permissions=0o600)
        SaveManager.configure_security(config)

        # Create save
        data = create_test_save_data()
        assert SaveManager.save_game(data, slot=0)

        # Check file permissions
        save_path = Path(temp_dir) / "save_0.sav"
        assert save_path.exists()
        assert oct(save_path.stat().st_mode)[-3:] == "600"


def test_backup_recovery():
    """Test backup recovery with corrupted save."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        # Create original save
        original_data = create_test_save_data()
        assert SaveManager.save_game(original_data, slot=0)

        # Create backup
        SaveManager._create_backup(0)

        # Corrupt save file
        save_path = Path(temp_dir) / "save_0.sav"
        with save_path.open("wb") as f:
            f.write(b"corrupted data")

        # Attempt to load should trigger recovery
        loaded_data = SaveManager.load_game(slot=0)
        assert loaded_data is not None
        assert loaded_data["version"] == original_data["version"]
        assert loaded_data["player_id"] == original_data["player_id"]


def test_save_data_migration():
    """Test save data version migration."""
    with tempfile.TemporaryDirectory() as temp_dir:
        SaveManager.set_save_dir(temp_dir)

        # Create old version data
        old_data = {
            "version": "0.9.0",
            "game_state": {},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }

        # Save old version data
        save_path = Path(temp_dir) / "save_0.sav"
        json_data = json.dumps(old_data)
        compressed = SaveManager._compress_data(json_data)
        encrypted = SaveManager._encrypt_data(compressed)
        with save_path.open("wb") as f:
            f.write(encrypted)

        # Load should trigger migration
        loaded_data = SaveManager.load_game(slot=0)
        assert loaded_data is not None
        assert loaded_data["version"] == "1.1.0"
        assert "auto_save_interval" in loaded_data["game_state"]
        assert "backup_enabled" in loaded_data["game_state"]


def test_async_save_load():
    """Test asynchronous save/load operations."""
    import asyncio

    async def test_async():
        with tempfile.TemporaryDirectory() as temp_dir:
            SaveManager.set_save_dir(temp_dir)

            # Test async save
            data = create_test_save_data()
            assert await SaveManager.save_game_async(data, slot=0)

            # Test async load
            loaded_data = await SaveManager.load_game_async(slot=0)
            assert loaded_data is not None
            assert loaded_data["version"] == data["version"]
            assert loaded_data["player_id"] == data["player_id"]

    asyncio.run(test_async())
