"""
Save/Load system for managing game state persistence.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from roguelike.core.constants import (
    SAVE_VERSION,
    AUTO_SAVE_INTERVAL,
    BACKUP_ENABLED,
    MAX_BACKUP_FILES,
    Colors
)
from roguelike.world.entity.components.base import (
    AI, Corpse, Equipment, EquipmentSlots, Fighter,
    Inventory, Item, Level, Position, Renderable
)

logger = logging.getLogger(__name__)

class SaveManager:
    """Handles saving and loading game state."""

    def __init__(self, world: Any, game_state: Any, map_manager: Any):
        """Initialize the save manager.
        
        Args:
            world: The game world
            game_state: The current game state
            map_manager: The map manager
        """
        self.world = world
        self.game_state = game_state
        self.map_manager = map_manager
        self.turns_since_save = 0

    @staticmethod
    def get_save_dir() -> Path:
        """Get the save directory path."""
        return Path.home() / ".roguelike" / "saves"

    def save_game(self, slot: int = 0) -> bool:
        """Save the current game state.
        
        Args:
            slot: Save slot number (-1 for auto-save)
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Prepare save data
            tiles_data = [
                [tile.to_dict() if tile is not None else None for tile in row]
                for row in self.map_manager.tiles
            ] if self.map_manager.tiles is not None else None

            save_data = {
                "version": SAVE_VERSION,
                "game_state": self.game_state.to_dict(),
                "entities": self._serialize_entities(),
                "tiles": tiles_data,
                "player_id": self.game_state.player,
                "dungeon_level": self.game_state.dungeon_level,
                "timestamp": datetime.now().isoformat(),
                "auto_save": slot == -1,
            }

            # Create save directory if it doesn't exist
            save_dir = self.get_save_dir()
            save_dir.mkdir(parents=True, exist_ok=True)

            # Save file path
            save_file = save_dir / f"save_{slot}.sav"

            # Create backup if enabled
            if BACKUP_ENABLED and slot != -1 and save_file.exists():
                self._create_backup(slot)

            # Save game
            import json
            with save_file.open("w") as f:
                json.dump(save_data, f)

            if slot != -1:  # 自動セーブでない場合のみメッセージを表示
                self.game_state.add_message("Game saved.", Colors.GREEN)
            logger.info("Game saved successfully")
            return True

        except Exception as e:
            if slot != -1:  # 自動セーブでない場合のみメッセージを表示
                self.game_state.add_message("Failed to save game!", Colors.RED)
            logger.error(f"Error saving game: {e}")
            return False

    def load_game(self, slot: int = 0) -> bool:
        """Load a saved game state.
        
        Args:
            slot: Save slot number (-1 for auto-save)
            
        Returns:
            True if load successful, False otherwise
        """
        try:
            # Try to load save data
            save_file = self.get_save_dir() / f"save_{slot}.sav"
            if not save_file.exists():
                if slot != -1:
                    self.game_state.add_message("No save file found!", Colors.RED)
                logger.error("Save file not found")
                return False

            # Load save data
            import json
            with save_file.open("r") as f:
                save_data = json.load(f)

            # Validate version
            if save_data.get("version") != SAVE_VERSION:
                self.game_state.add_message("Incompatible save version!", Colors.RED)
                logger.error(f"Incompatible save version: {save_data.get('version')}")
                return False

            try:
                # Restore game state
                self.game_state.from_dict(save_data["game_state"])

                # Clear existing entities
                self.world.clear_database()

                # Restore entities
                self._deserialize_entities(save_data["entities"])

                # Restore tiles
                if save_data["tiles"] is not None:
                    from roguelike.world.map.tiles import Tile
                    tiles_data = save_data["tiles"]
                    tiles = []
                    for row in tiles_data:
                        tiles_row = []
                        for tile_data in row:
                            if tile_data is None:
                                tiles_row.append(None)
                            else:
                                tiles_row.append(Tile.from_dict(tile_data))
                        tiles.append(tiles_row)
                    self.map_manager.tiles = tiles

                # Restore player reference
                self.game_state.player = save_data["player_id"]

                # Restore dungeon level
                self.game_state.dungeon_level = save_data["dungeon_level"]

                if not save_data.get("auto_save", False):
                    self.game_state.add_message("Game loaded.", Colors.GREEN)
                logger.info("Game loaded successfully")
                return True

            except KeyError as e:
                self.game_state.add_message("Corrupted save data!", Colors.RED)
                logger.error(f"Missing key in save data: {e}")
                return False

        except Exception as e:
            self.game_state.add_message("Failed to load game!", Colors.RED)
            logger.error(f"Error loading game: {e}")
            return False

    def auto_save(self) -> None:
        """Automatically save the game to a special auto-save slot."""
        try:
            self.save_game(slot=-1)  # Use -1 for auto-save slot
        except Exception as e:
            logger.error(f"Auto-save failed: {e}", exc_info=True)

    def check_auto_save(self) -> None:
        """Check if auto-save should be performed."""
        try:
            if AUTO_SAVE_INTERVAL <= 0:
                return

            self.turns_since_save += 1
            if self.turns_since_save >= AUTO_SAVE_INTERVAL:
                logger.info("Performing auto-save...")
                if self.save_game(slot=-1):  # Use special slot for auto-save
                    self.turns_since_save = 0
                    logger.info("Auto-save completed")
                else:
                    logger.error("Auto-save failed")

        except Exception as e:
            logger.error(f"Error in auto-save check: {e}")

    def _create_backup(self, slot: int) -> None:
        """Create a backup of the save file.
        
        Args:
            slot: Save slot number to backup
        """
        save_dir = self.get_save_dir()
        save_file = save_dir / f"save_{slot}.sav"

        if not save_file.exists():
            return

        # Create backup directory
        backup_dir = save_dir / "backup"
        backup_dir.mkdir(exist_ok=True)

        # Rotate backups
        for i in range(MAX_BACKUP_FILES - 1, 0, -1):
            old_backup = backup_dir / f"save_{slot}.{i}.bak"
            new_backup = backup_dir / f"save_{slot}.{i + 1}.bak"
            if old_backup.exists():
                old_backup.rename(new_backup)

        # Create new backup
        import shutil
        backup_file = backup_dir / f"save_{slot}.1.bak"
        shutil.copy2(save_file, backup_file)
        logger.info(f"Created backup: {backup_file}")

        # Remove oldest backup if exceeding limit
        old_backup = backup_dir / f"save_{slot}.{MAX_BACKUP_FILES + 1}.bak"
        if old_backup.exists():
            old_backup.unlink()

    def _serialize_entities(self) -> Dict[int, Dict[str, Any]]:
        """Serialize all entities and their components.
        
        Returns:
            Dictionary mapping entity IDs to their serialized components
        """
        entities = {}
        for entity in self.world._entities:
            components = {}
            for component_type in self.world._components:
                if self.world.has_component(entity, component_type):
                    component = self.world.component_for_entity(entity, component_type)
                    components[component_type.__name__] = component.to_dict()
            if components:
                entities[entity] = components
        return entities

    def _deserialize_entities(self, entities_data: Dict[int, Dict[str, Any]]) -> None:
        """Restore entities from serialized data."""
        component_types = {
            "AI": AI,
            "Corpse": Corpse,
            "Equipment": Equipment,
            "Fighter": Fighter,
            "Inventory": Inventory,
            "Item": Item,
            "Level": Level,
            "Position": Position,
            "Renderable": Renderable,
        }

        for entity_id, components in entities_data.items():
            # Create new entity with same ID
            self.world.create_entity(entity_id)
            
            # Add components
            for component_name, component_data in components.items():
                if component_name in component_types:
                    component_class = component_types[component_name]
                    component = component_class.from_dict(component_data)
                    self.world.add_component(entity_id, component) 