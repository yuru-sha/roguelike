"""
The main game engine class that coordinates all game systems.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import esper
import numpy as np
import tcod
import tcod.event
from tcod import libtcodpy

from roguelike.core.constants import (AUTO_SAVE_INTERVAL, BACKUP_ENABLED,
                                      MAP_HEIGHT, MAP_WIDTH, MAX_BACKUP_FILES,
                                      SAVE_VERSION, SCREEN_HEIGHT,
                                      SCREEN_WIDTH, TORCH_RADIUS, Colors)
from roguelike.game.states.game_state import GameState, GameStates
from roguelike.ui.handlers.input_handler import InputHandler
from roguelike.ui.screens.save_load_screen import SaveLoadScreen
from roguelike.utils.logging import GameLogger
from roguelike.utils.serialization import SaveManager
from roguelike.world.entity.components.base import (AI, Corpse, Equipment,
                                                    EquipmentSlots, Fighter,
                                                    Inventory, Item, Level,
                                                    Position, Renderable,
                                                    RenderOrder)
from roguelike.world.entity.prefabs.player import create_player
from roguelike.world.map.generator.dungeon_generator import DungeonGenerator
from roguelike.world.map.tiles import Tile, TileType
from roguelike.world.spawner.spawner import populate_dungeon

logger = GameLogger.get_instance()


class Engine:
    """
    The main game engine class that coordinates all game systems.
    """

    def __init__(self, skip_lock_check: bool = False):
        """Initialize the game engine."""
        logger.info("Initializing game engine")

        # Get the project root directory
        project_root = Path(__file__).parents[3]
        assets_path = project_root / "data" / "assets" / "dejavu10x10_gs_tc.png"

        # Check for existing lock file
        self.lock_file = project_root / ".game.lock"
        if not skip_lock_check:
            if self.lock_file.exists():
                logger.error("Game is already running")
                raise RuntimeError("Another instance of the game is already running")

            # Create lock file
            try:
                with self.lock_file.open("w") as f:
                    f.write(str(os.getpid()))
                logger.info(f"Created lock file: {self.lock_file}")
            except Exception as e:
                logger.error(f"Failed to create lock file: {e}")
                raise RuntimeError("Failed to create lock file")

        # Initialize TCOD
        self.root_console = tcod.console.Console(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.context = tcod.context.new(
            columns=SCREEN_WIDTH,
            rows=SCREEN_HEIGHT,
            title="Roguelike",
            tileset=tcod.tileset.load_tilesheet(
                str(assets_path), 32, 8, tcod.tileset.CHARMAP_TCOD
            ),
            vsync=True,
        )

        # Disable key repeat
        tcod.lib.SDL_StartTextInput()
        tcod.lib.SDL_StopTextInput()
        tcod.lib.SDL_SetHint(b"SDL_HINT_NO_SIGNAL_HANDLERS", b"1")
        tcod.lib.SDL_SetHint(b"SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS", b"1")
        tcod.lib.SDL_SetHint(b"SDL_HINT_VIDEO_ALLOW_SCREENSAVER", b"1")
        tcod.lib.SDL_SetHint(b"SDL_HINT_MOUSE_FOCUS_CLICKTHROUGH", b"1")
        tcod.lib.SDL_SetHint(b"SDL_HINT_VIDEO_X11_NET_WM_PING", b"0")
        tcod.lib.SDL_SetHint(b"SDL_HINT_MOUSE_AUTO_CAPTURE", b"0")
        tcod.lib.SDL_SetHint(b"SDL_HINT_RENDER_BATCHING", b"1")
        tcod.lib.SDL_SetHint(b"SDL_HINT_EVENT_LOGGING", b"0")
        tcod.lib.SDL_SetHint(b"SDL_HINT_KEYBOARD_TEXT_EDITING", b"0")
        tcod.lib.SDL_SetHint(b"SDL_HINT_MOUSE_TOUCH_EVENTS", b"0")
        tcod.lib.SDL_SetHint(b"SDL_HINT_TOUCH_MOUSE_EVENTS", b"0")
        tcod.lib.SDL_SetHint(b"SDL_HINT_IDLE_TIMER_DISABLED", b"1")

        # Initialize game state
        self.game_state = GameState()
        self.input_handler = InputHandler()

        # Initialize ECS world
        self.world = esper.World()

        # Initialize map
        self.dungeon_generator = DungeonGenerator()
        self.tiles: Optional[np.ndarray] = None
        self.fov_map: Optional[np.ndarray] = None

        # Player entity
        self.player: Optional[int] = None

        # Game running flag
        self.running = True

        # UI screens
        self.save_load_screen: Optional[SaveLoadScreen] = None

        # Auto-save counter
        self.turns_since_save = 0

        # Current dungeon level
        self.dungeon_level = 1

        logger.info("Game engine initialized")

    def save_game(self, slot: int = 0) -> bool:
        """
        Save the current game state.

        Args:
            slot: Save slot number (-1 for auto-save)

        Returns:
            True if save successful, False otherwise
        """
        try:
            # Prepare save data
            tiles_data = (
                [
                    [tile.to_dict() if tile is not None else None for tile in row]
                    for row in self.tiles
                ]
                if self.tiles is not None
                else None
            )
            logger.debug(f"Tiles data: {tiles_data}")

            save_data = {
                "version": SAVE_VERSION,
                "game_state": self.game_state.to_dict(),
                "entities": self._serialize_entities(),
                "tiles": tiles_data,
                "player_id": self.player,
                "dungeon_level": self.dungeon_level,
                "timestamp": datetime.now().isoformat(),
                "auto_save": slot == -1,
            }

            # Save game
            if SaveManager.save_game(save_data, slot):
                if slot != -1:  # 自動セーブでない場合のみメッセージを表示
                    self.game_state.add_message("Game saved.", Colors.GREEN)
                logger.info("Game saved successfully")
                return True
            else:
                if slot != -1:  # 自動セーブでない場合のみメッセージを表示
                    self.game_state.add_message("Failed to save game!", Colors.RED)
                logger.error("Failed to save game")
                return False

        except Exception as e:
            if slot != -1:  # 自動セーブでない場合のみメッセージを表示
                self.game_state.add_message("Failed to save game!", Colors.RED)
            logger.error(f"Error saving game: {e}")
            return False

    def _create_backup(self, slot: int) -> None:
        """
        Create a backup of the save file.

        Args:
            slot: Save slot number to backup
        """
        save_dir = SaveManager.get_save_dir()
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

    def load_game(self, slot: int = 0) -> bool:
        """
        Load a saved game state.

        Args:
            slot: Save slot number (-1 for auto-save)

        Returns:
            True if load successful, False otherwise
        """
        try:
            # Try to load save data
            save_data = SaveManager.load_game(slot)
            if not save_data:
                # If loading fails and this is not an auto-save slot,
                # try to load from backup
                if slot != -1:
                    logger.info("Attempting to load from backup...")
                    backup_data = SaveManager.load_backup(slot)
                    if backup_data:
                        save_data = backup_data
                        self.game_state.add_message(
                            "Restored from backup save.", Colors.YELLOW
                        )
                    else:
                        self.game_state.add_message("Failed to load game!", Colors.RED)
                        logger.error("Failed to load game: No save data or backup")
                        return False
                else:
                    logger.error("Failed to load auto-save")
                    return False

            # Validate version
            if save_data.get("version") != SAVE_VERSION:
                try:
                    save_data = SaveManager._migrate_save_data(save_data)
                except SaveVersionError:
                    self.game_state.add_message(
                        "Incompatible save version!", Colors.RED
                    )
                    logger.error(
                        f"Incompatible save version: {save_data.get('version')}"
                    )
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
                    self.tiles = np.array(tiles, dtype=object)

                # Restore player reference
                self.player = save_data["player_id"]

                # Restore dungeon level
                self.dungeon_level = save_data["dungeon_level"]

                # Initialize FOV map
                self._initialize_fov()

                # Update FOV
                self._recompute_fov()

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

    def _serialize_entities(self) -> Dict[int, Dict[str, Any]]:
        """
        Serialize all entities and their components.

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
        """
        Restore entities from serialized data.

        Args:
            entities_data: Dictionary mapping entity IDs to their serialized components
        """
        from roguelike.world.entity.components.base import (AI, Corpse,
                                                            Equipment,
                                                            EquipmentSlots,
                                                            Fighter, Inventory,
                                                            Item, Level,
                                                            Position,
                                                            Renderable)

        component_classes = {
            "Position": Position,
            "Renderable": Renderable,
            "Fighter": Fighter,
            "AI": AI,
            "Inventory": Inventory,
            "Item": Item,
            "Level": Level,
            "EquipmentSlots": EquipmentSlots,
            "Equipment": Equipment,
            "Corpse": Corpse,
        }

        for entity_id, components in entities_data.items():
            # Create entity with specific ID
            entity_id = int(entity_id)  # Ensure entity_id is an integer
            self.world.create_entity(entity_id)

            # Add components
            for component_name, component_data in components.items():
                # Get component class by name
                component_class = component_classes.get(component_name)
                if component_class is None:
                    raise ValueError(f"Unknown component type: {component_name}")

                # Create component instance from data
                try:
                    component = component_class.from_dict(component_data)
                    self.world.add_component(entity_id, component)
                except Exception as e:
                    logger.error(f"Failed to deserialize {component_name}: {e}")
                    raise

    def auto_save(self) -> None:
        """Automatically save the game to a special auto-save slot."""
        try:
            self.save_game(slot=-1)  # Use -1 for auto-save slot
        except Exception as e:
            logger.error(f"Auto-save failed: {e}", exc_info=True)

    def quit_game(self) -> None:
        """Safely quit the game."""
        logger.info("Quitting game")
        self.auto_save()  # Auto-save before quitting
        self.running = False

    def cleanup(self) -> None:
        """Clean up resources before exiting."""
        logger.info("Cleaning up resources")

        # Remove lock file
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
                logger.info("Removed lock file")
        except Exception as e:
            logger.error(f"Failed to remove lock file: {e}")

        if self.context:
            self.context.close()

    def _initialize_fov(self) -> None:
        """Initialize the field of view map."""
        if not self.player:
            return

        player_pos = self.world.component_for_entity(self.player, Position)

        # Create transparency map
        transparency = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=bool)
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                transparency[y][x] = not self.tiles[y][x].block_sight

        # Compute initial FOV
        self.fov_map = tcod.map.compute_fov(
            transparency=transparency,
            pov=(player_pos.y, player_pos.x),
            radius=TORCH_RADIUS,
            light_walls=True,
            algorithm=libtcodpy.FOV_BASIC,
        )

    def _recompute_fov(self) -> None:
        """Recompute the field of view."""
        if not self.player:
            return

        player_pos = self.world.component_for_entity(self.player, Position)

        # Create transparency map
        transparency = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=bool)
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                transparency[y][x] = not self.tiles[y][x].block_sight

        # Compute FOV
        self.fov_map = tcod.map.compute_fov(
            transparency=transparency,
            pov=(player_pos.y, player_pos.x),
            radius=TORCH_RADIUS,
            light_walls=True,
            algorithm=libtcodpy.FOV_BASIC,
        )

    def _render_map(self) -> None:
        """Render the game map."""
        if not self.fov_map is None:
            for y in range(MAP_HEIGHT):
                for x in range(MAP_WIDTH):
                    visible = self.fov_map[y, x]
                    if visible:
                        # Tile is visible
                        if self.tiles[y][x].tile_type == TileType.WALL:
                            # Wall
                            self.root_console.rgb[y, x]["ch"] = ord("#")
                            self.root_console.rgb[y, x]["fg"] = Colors.LIGHT_WALL
                        elif self.tiles[y][x].tile_type == TileType.STAIRS_DOWN:
                            # Down stairs
                            self.root_console.rgb[y, x]["ch"] = ord(">")
                            self.root_console.rgb[y, x]["fg"] = Colors.WHITE
                        elif self.tiles[y][x].tile_type == TileType.STAIRS_UP:
                            # Up stairs
                            self.root_console.rgb[y, x]["ch"] = ord("<")
                            self.root_console.rgb[y, x]["fg"] = Colors.WHITE
                        else:
                            # Floor
                            self.root_console.rgb[y, x]["ch"] = ord(".")
                            self.root_console.rgb[y, x]["fg"] = Colors.LIGHT_GROUND
                        self.root_console.rgb[y, x]["bg"] = (0, 0, 0)
                        self.tiles[y][x].explored = True
                    elif self.tiles[y][x].explored:
                        # Tile has been explored but is not visible
                        if self.tiles[y][x].tile_type == TileType.WALL:
                            # Wall
                            self.root_console.rgb[y, x]["ch"] = ord("#")
                            self.root_console.rgb[y, x]["fg"] = Colors.DARK_WALL
                        elif self.tiles[y][x].tile_type == TileType.STAIRS_DOWN:
                            # Down stairs
                            self.root_console.rgb[y, x]["ch"] = ord(">")
                            self.root_console.rgb[y, x]["fg"] = Colors.DARK_GROUND
                        elif self.tiles[y][x].tile_type == TileType.STAIRS_UP:
                            # Up stairs
                            self.root_console.rgb[y, x]["ch"] = ord("<")
                            self.root_console.rgb[y, x]["fg"] = Colors.DARK_GROUND
                        else:
                            # Floor
                            self.root_console.rgb[y, x]["ch"] = ord(".")
                            self.root_console.rgb[y, x]["fg"] = Colors.DARK_GROUND
                        self.root_console.rgb[y, x]["bg"] = (0, 0, 0)

    def _render_entities(self) -> None:
        """Render all entities."""
        # Sort entities by render order
        entities_in_render_order = sorted(
            self.world.get_components(Position, Renderable),
            key=lambda x: x[1][1].render_order,
        )

        logger.debug(f"Rendering {len(entities_in_render_order)} entities")

        for ent, (pos, render) in entities_in_render_order:
            # 死体は探索済みの領域では常に表示
            is_corpse = self.world.has_component(ent, Corpse)
            if is_corpse:
                logger.debug(f"Found corpse at ({pos.x}, {pos.y}): {render.name}")

            # 視界内か、死体かつ探索済みの場合に表示
            visible = self.fov_map[pos.y, pos.x] if self.fov_map is not None else False
            explored = (
                self.tiles[pos.y][pos.x].explored if self.tiles is not None else False
            )

            if visible or (is_corpse and explored):
                # 色の決定
                color = render.color
                if not visible:
                    color = Colors.DARK_GRAY
                elif is_corpse:
                    color = Colors.RED

                # エンティティの描画
                self.root_console.print(y=pos.y, x=pos.x, string=render.char, fg=color)

                if is_corpse:
                    logger.debug(
                        f"Rendered corpse at ({pos.x}, {pos.y}) with char '{render.char}' and color {color}"
                    )

    def _handle_movement(self, action: Dict[str, Any]) -> None:
        """Handle movement action."""
        try:
            dx = action.get("dx", 0)
            dy = action.get("dy", 0)

            player_pos = self.world.component_for_entity(self.player, Position)
            dest_x = player_pos.x + dx
            dest_y = player_pos.y + dy

            logger.debug(
                f"Player (ID: {self.player}) at ({player_pos.x}, {player_pos.y}) attempting to move to ({dest_x}, {dest_y})"
            )

            # Check if destination is within bounds
            if not (0 <= dest_x < MAP_WIDTH and 0 <= dest_y < MAP_HEIGHT):
                return

            # First check for entities at destination
            for ent, (pos, fighter) in self.world.get_components(Position, Fighter):
                if pos.x == dest_x and pos.y == dest_y:
                    # Attack!
                    target_name = self.world.component_for_entity(ent, Renderable).name
                    logger.debug(
                        f"Found enemy {target_name} (ID: {ent}) at ({pos.x}, {pos.y})"
                    )
                    damage = self._calculate_damage(self.player, ent)

                    if damage > 0:
                        self.game_state.add_message(
                            f"You attack {target_name} for {damage} damage!",
                            Colors.PLAYER_ATK,
                        )
                        xp = fighter.take_damage(damage)
                        logger.debug(
                            f"Dealt {damage} damage to {target_name} (ID: {ent}), HP remaining: {fighter.hp}"
                        )
                        # Check if enemy died
                        if fighter.hp <= 0:
                            self.game_state.add_message(
                                f"{target_name} dies!", Colors.ENEMY_DIE
                            )
                            self._handle_enemy_death(ent, xp)
                            # 敵が死亡したら、その位置にある他の敵エンティティを削除
                            for other_ent, (other_pos, _) in self.world.get_components(
                                Position, Fighter
                            ):
                                if (
                                    other_ent != ent
                                    and other_pos.x == pos.x
                                    and other_pos.y == pos.y
                                ):
                                    logger.debug(
                                        f"Removing duplicate enemy at ({other_pos.x}, {other_pos.y})"
                                    )
                                    self.world.delete_entity(other_ent)
                    else:
                        self.game_state.add_message(
                            f"You attack {target_name} but do no damage!",
                            Colors.PLAYER_ATK,
                        )
                    return

            # Then check if tile is blocked
            if self.tiles[dest_y][dest_x].blocked:
                logger.debug(f"Movement blocked by terrain at ({dest_x}, {dest_y})")
                return

            # Check for corpses at destination
            for ent, (pos, _) in self.world.get_components(Position, Corpse):
                if pos.x == dest_x and pos.y == dest_y:
                    # コープスの上を移動できる
                    logger.debug(f"Moving over corpse at ({pos.x}, {pos.y})")
                    player_pos.x = dest_x
                    player_pos.y = dest_y
                    logger.debug(
                        f"Player (ID: {self.player}) moved to ({player_pos.x}, {player_pos.y})"
                    )
                    return

            # Move player
            player_pos.x = dest_x
            player_pos.y = dest_y
            logger.debug(
                f"Player (ID: {self.player}) moved to ({player_pos.x}, {player_pos.y})"
            )

        except Exception as e:
            logger.error(f"Error handling movement: {str(e)}", exc_info=True)
            raise

    def _handle_stairs(self, action: Dict[str, Any]) -> None:
        """Handle stair usage action."""
        try:
            if not self.player:
                logger.warning("Stair usage attempted but no player entity exists")
                return

            direction = action.get("direction")
            player_pos = self.world.component_for_entity(self.player, Position)
            current_tile = self.tiles[player_pos.y][player_pos.x]

            logger.debug(
                f"Attempting to use stairs: direction={direction}, player_pos=({player_pos.x}, {player_pos.y})"
            )
            logger.debug(f"Current tile type: {current_tile.tile_type}")

            if direction == "down" and current_tile.tile_type == TileType.STAIRS_DOWN:
                logger.debug("Found down stairs, descending...")
                # Go down stairs
                self.game_state.dungeon_level += 1
                logger.info(
                    f"Player descended to level {self.game_state.dungeon_level}"
                )
                self.game_state.add_message(
                    f"You descend deeper into the dungeon (Level {self.game_state.dungeon_level}).",
                    Colors.WHITE,
                )
                self._change_level()

            elif direction == "up" and current_tile.tile_type == TileType.STAIRS_UP:
                logger.debug("Found up stairs, ascending...")
                # Go up stairs
                if self.game_state.dungeon_level > 1:
                    self.game_state.dungeon_level -= 1
                    logger.info(
                        f"Player ascended to level {self.game_state.dungeon_level}"
                    )
                    self.game_state.add_message(
                        f"You climb up the stairs (Level {self.game_state.dungeon_level}).",
                        Colors.WHITE,
                    )
                    self._change_level()
                else:
                    logger.info("Player attempted to leave the dungeon")
                    if self.game_state.player_has_amulet:
                        # Victory!
                        self.game_state.add_message(
                            "You escaped the dungeon with the Amulet of Yendor! You win!",
                            Colors.YELLOW,
                        )
                        logger.info("Player won the game!")
                        self.game_state.game_won = True
                        self.quit_game()
                    else:
                        self.game_state.add_message(
                            "You need the Amulet of Yendor to leave the dungeon!",
                            Colors.RED,
                        )
            else:
                # No stairs here
                if direction == "down":
                    self.game_state.add_message(
                        "There are no stairs down here.", Colors.YELLOW
                    )
                else:
                    self.game_state.add_message(
                        "There are no stairs up here.", Colors.YELLOW
                    )
                logger.debug(
                    f"No {direction} stairs at current position. Current tile type: {current_tile.tile_type}"
                )

        except Exception as e:
            logger.error(f"Error handling stairs: {str(e)}", exc_info=True)
            raise

    def _change_level(self) -> None:
        """Change to a new dungeon level."""
        try:
            logger.info(f"Generating new level {self.game_state.dungeon_level}")

            # Clear current level
            self.world.clear_database()

            # Generate new level
            self.tiles, player_pos = self.dungeon_generator.generate(
                self.game_state.dungeon_level
            )

            # Create player at appropriate position
            self.player = create_player(self.world, *player_pos)

            # Populate new level
            populate_dungeon(
                self.world, self.dungeon_generator.rooms, self.game_state.dungeon_level
            )

            # Initialize FOV
            self._initialize_fov()

            logger.info("Level change completed")

        except Exception as e:
            logger.error(f"Error changing level: {str(e)}", exc_info=True)
            raise

    def _handle_pickup(self) -> None:
        """Handle picking up an item."""
        try:
            player_pos = self.world.component_for_entity(self.player, Position)
            player_inventory = self.world.component_for_entity(self.player, Inventory)

            # Find items at player's position
            items_found = False
            for ent, (pos, _) in self.world.get_components(Position, Item):
                if pos.x == player_pos.x and pos.y == player_pos.y:
                    items_found = True
                    # Check if inventory is full
                    slot = player_inventory.add_item(ent)
                    if slot is None:
                        item_name = self.world.component_for_entity(
                            ent, Renderable
                        ).name
                        self.game_state.add_message(
                            f"Your inventory is full, cannot pick up {item_name}!",
                            Colors.RED,
                        )
                        logger.info(f"Pickup failed: inventory full, item={item_name}")
                    else:
                        # Add item to inventory and remove from map
                        item_name = self.world.component_for_entity(
                            ent, Renderable
                        ).name
                        self.world.remove_component(ent, Position)  # Remove from map
                        self.game_state.add_message(
                            f"You pick up the {item_name}!", Colors.GREEN
                        )
                        logger.info(f"Picked up item: {item_name}, slot={slot}")
                    break

            if not items_found:
                self.game_state.add_message(
                    "There is nothing here to pick up.", Colors.YELLOW
                )
                logger.debug("No items found at player position")
        except Exception as e:
            logger.error(f"Error in pickup handling: {e}", exc_info=True)
            raise

    def handle_action(self, action: Dict[str, Any]) -> None:
        """Handle a game action."""
        try:
            action_type = action.get("action")
            logger.debug(f"Handling action: {action_type}")

            if action_type == "move":
                self._handle_movement(action)
                self._check_auto_save()
            elif action_type == "use_stairs":
                self._handle_stairs(action)
                self._check_auto_save()
            elif action_type == "wait":
                logger.debug("Player waited")
                self._check_auto_save()
                pass  # Do nothing, just pass the turn
            elif action_type == "pickup":
                self._handle_pickup()
                self._check_auto_save()
            elif action_type == "exit":
                if self.game_state.state in (
                    GameStates.SAVE_GAME,
                    GameStates.LOAD_GAME,
                ):
                    self.game_state.state = GameStates.PLAYERS_TURN
                    self.save_load_screen = None
                else:
                    logger.info("Player initiated game exit")
                    self.quit_game()
                    return
            elif action_type == "save_game":
                self.game_state.state = GameStates.SAVE_GAME
                self.save_load_screen = SaveLoadScreen(self.root_console, is_save=True)
                self.game_state.add_message(
                    "Select a slot to save the game (0-9)", Colors.WHITE
                )
            elif action_type == "load_game":
                self.game_state.state = GameStates.LOAD_GAME
                self.save_load_screen = SaveLoadScreen(self.root_console, is_save=False)
                self.game_state.add_message(
                    "Select a slot to load the game (0-9)", Colors.WHITE
                )
            elif action_type == "select" and self.save_load_screen:
                if self.game_state.state == GameStates.SAVE_GAME:
                    self.save_game(self.save_load_screen.selected_slot)
                    self.game_state.state = GameStates.PLAYERS_TURN
                    self.save_load_screen = None
                elif self.game_state.state == GameStates.LOAD_GAME:
                    if self.load_game(self.save_load_screen.selected_slot):
                        self.game_state.add_message(
                            f"Game loaded from slot {self.save_load_screen.selected_slot}",
                            Colors.GREEN,
                        )
                        self.game_state.state = GameStates.PLAYERS_TURN
                        self.save_load_screen = None
                    else:
                        self.game_state.add_message("Failed to load game", Colors.RED)
            elif action_type == "move_cursor" and self.save_load_screen:
                dy = action.get("dy", 0)
                if dy < 0:
                    self.save_load_screen.selected_slot = max(
                        0, self.save_load_screen.selected_slot - 1
                    )
                elif dy > 0:
                    self.save_load_screen.selected_slot = min(
                        9, self.save_load_screen.selected_slot + 1
                    )

            # Update FOV after any action
            self._recompute_fov()
        except Exception as e:
            logger.error(f"Error handling action {action}: {str(e)}", exc_info=True)
            raise

    def _check_auto_save(self) -> None:
        """Check if auto-save should be performed."""
        try:
            auto_save_interval = self.game_state.auto_save_interval
            if auto_save_interval <= 0:
                return

            self.turns_since_save += 1
            if self.turns_since_save >= auto_save_interval:
                logger.info("Performing auto-save...")
                if self.save_game(slot=-1):  # Use special slot for auto-save
                    self.turns_since_save = 0
                    logger.info("Auto-save completed")
                else:
                    logger.error("Auto-save failed")

        except Exception as e:
            logger.error(f"Error in auto-save check: {e}")

    def new_game(self) -> None:
        """Start a new game."""
        logger.info("Starting new game")

        # Generate first dungeon level
        self.tiles, player_pos = self.dungeon_generator.generate(
            self.game_state.dungeon_level
        )

        # Create player
        self.player = create_player(self.world, *player_pos)

        # Populate dungeon
        populate_dungeon(
            self.world, self.dungeon_generator.rooms, self.game_state.dungeon_level
        )

        # Initialize FOV
        self._initialize_fov()

        # Add welcome message
        self.game_state.add_message(
            "Welcome to the Roguelike! Prepare to die...", Colors.WHITE
        )

        logger.info("New game started")

    def run(self) -> None:
        """Run the game loop."""
        logger.info("Starting game loop")

        try:
            # Start new game
            self.new_game()

            while self.running:
                try:
                    # Clear the console
                    self.root_console.clear()

                    # Render the game
                    self._render_map()
                    self._render_entities()
                    self._render_messages()

                    # Present the console
                    self.context.present(self.root_console)

                    # Handle events
                    for event in tcod.event.wait():
                        try:
                            # Convert event coordinates
                            event = self.context.convert_event(event)

                            # Handle window close button
                            if isinstance(event, tcod.event.Quit):
                                logger.info("Window close event received")
                                self.quit_game()
                                break

                            # Log event details
                            logger.debug(f"Received event: {event.__class__.__name__}")
                            if hasattr(event, "sym"):
                                logger.debug(f"Key: {event.sym}")
                            if hasattr(event, "scancode"):
                                logger.debug(f"Scancode: {event.scancode}")
                            if hasattr(event, "mod"):
                                logger.debug(f"Modifiers: {event.mod}")

                            # Handle input
                            action = self.input_handler.handle_input(
                                event, self.game_state.state
                            )
                            logger.debug(
                                f"Input event: {event}, resulting action: {action}"
                            )

                            if action:
                                # Log action details
                                logger.debug(f"Processing action: {action}")

                                # Get player state before action
                                if self.player:
                                    player_pos = self.world.component_for_entity(
                                        self.player, Position
                                    )
                                    logger.debug(
                                        f"Player position before action: ({player_pos.x}, {player_pos.y})"
                                    )

                                # Handle action
                                self.handle_action(action)

                                # Get player state after action
                                if self.player:
                                    player_pos = self.world.component_for_entity(
                                        self.player, Position
                                    )
                                    logger.debug(
                                        f"Player position after action: ({player_pos.x}, {player_pos.y})"
                                    )

                                if not self.running:
                                    break

                        except Exception as e:
                            logger.error(
                                f"Error handling event {event}: {str(e)}", exc_info=True
                            )
                            logger.error(f"Event details: {vars(event)}")
                            logger.error(f"Game state: {self.game_state.state}")
                            if self.player:
                                try:
                                    player_pos = self.world.component_for_entity(
                                        self.player, Position
                                    )
                                    logger.error(
                                        f"Player position: ({player_pos.x}, {player_pos.y})"
                                    )
                                except Exception as pe:
                                    logger.error(
                                        f"Could not get player position: {str(pe)}"
                                    )
                            raise

                except Exception as e:
                    logger.error(
                        f"Error in game loop iteration: {str(e)}", exc_info=True
                    )
                    logger.error("Current game state:", exc_info=True)
                    logger.error(f"- Game state: {self.game_state.state}")
                    logger.error(f"- Running: {self.running}")
                    logger.error(f"- Player entity: {self.player}")
                    if self.player:
                        try:
                            player_pos = self.world.component_for_entity(
                                self.player, Position
                            )
                            logger.error(
                                f"- Player position: ({player_pos.x}, {player_pos.y})"
                            )
                        except Exception as pe:
                            logger.error(f"Could not get player position: {str(pe)}")
                    raise

        except Exception as e:
            logger.error(f"Fatal error in game loop: {str(e)}", exc_info=True)
            logger.error("Final game state:", exc_info=True)
            logger.error(f"- Game state: {self.game_state.state}")
            logger.error(f"- Running: {self.running}")
            logger.error(f"- Player entity: {self.player}")
            if self.player:
                try:
                    player_pos = self.world.component_for_entity(self.player, Position)
                    logger.error(f"- Player position: ({player_pos.x}, {player_pos.y})")
                except Exception as pe:
                    logger.error(f"Could not get player position: {str(pe)}")
            raise

        finally:
            logger.info("Cleaning up game resources")
            self.cleanup()

    def render(self) -> None:
        """Render the game screen."""
        try:
            # Clear the console
            self.root_console.clear()

            if (
                self.game_state.state in (GameStates.SAVE_GAME, GameStates.LOAD_GAME)
                and self.save_load_screen
            ):
                # Render save/load screen
                self.save_load_screen.render()
            else:
                # Render normal game screen
                self._render_map()
                self._render_entities()
                self._render_messages()

            # Present the console
            self.context.present(self.root_console)

        except Exception as e:
            logger.error(f"Error in render: {str(e)}", exc_info=True)
            raise

    def _render_messages(self) -> None:
        """Render message log."""
        try:
            # メッセージ表示領域の設定
            message_x = 1
            message_y = MAP_HEIGHT + 1
            message_width = SCREEN_WIDTH - 2
            message_height = SCREEN_HEIGHT - MAP_HEIGHT - 1

            # メッセージ領域の背景を描画
            for y in range(message_y, message_y + message_height):
                for x in range(message_x, message_x + message_width):
                    self.root_console.rgb[y, x] = Colors.BLACK

            # 最新のメッセージから表示
            messages = self.game_state.game_messages[-message_height:]
            for i, message in enumerate(messages):
                self.root_console.print(
                    x=message_x, y=message_y + i, string=message.text, fg=message.color
                )

        except Exception as e:
            logger.error(f"Error rendering messages: {str(e)}", exc_info=True)
            raise

    def _calculate_damage(self, attacker: int, defender: int) -> int:
        """
        Calculate damage for an attack.

        Args:
            attacker: Entity ID of the attacker
            defender: Entity ID of the defender

        Returns:
            Amount of damage dealt
        """
        try:
            attacker_fighter = self.world.component_for_entity(attacker, Fighter)
            defender_fighter = self.world.component_for_entity(defender, Fighter)

            # 基本攻撃力を取得
            damage = attacker_fighter.power

            # 装備による攻撃力ボーナスを加算
            if self.world.has_component(attacker, EquipmentSlots):
                equipment_slots = self.world.component_for_entity(
                    attacker, EquipmentSlots
                )
                for item_id in equipment_slots.slots.values():
                    if item_id is not None and self.world.has_component(
                        item_id, Equipment
                    ):
                        equipment = self.world.component_for_entity(item_id, Equipment)
                        damage += equipment.power_bonus

            # 防御力による軽減
            damage -= defender_fighter.defense

            # 装備による防御力ボーナスを考慮
            if self.world.has_component(defender, EquipmentSlots):
                equipment_slots = self.world.component_for_entity(
                    defender, EquipmentSlots
                )
                for item_id in equipment_slots.slots.values():
                    if item_id is not None and self.world.has_component(
                        item_id, Equipment
                    ):
                        equipment = self.world.component_for_entity(item_id, Equipment)
                        damage -= equipment.defense_bonus

            return max(0, damage)  # ダメージは最低0

        except Exception as e:
            logger.error(f"Error calculating damage: {str(e)}", exc_info=True)
            return 0

    def _handle_enemy_death(self, enemy: int, xp: int) -> None:
        """
        Handle enemy death.

        Args:
            enemy: Entity ID of the dead enemy
            xp: Experience points gained
        """
        try:
            # Get enemy position and name
            enemy_pos = self.world.component_for_entity(enemy, Position)
            enemy_render = self.world.component_for_entity(enemy, Renderable)

            logger.debug(
                f"Creating corpse for {enemy_render.name} at position ({enemy_pos.x}, {enemy_pos.y})"
            )

            # 同じ位置にある他の敵エンティティを削除
            for ent, (pos, _) in self.world.get_components(Position, Fighter):
                if ent != enemy and pos.x == enemy_pos.x and pos.y == enemy_pos.y:
                    logger.debug(f"Removing duplicate enemy at ({pos.x}, {pos.y})")
                    self.world.delete_entity(ent)

            # Check if there's already a corpse at this position
            for ent, (pos, _) in self.world.get_components(Position, Corpse):
                if pos.x == enemy_pos.x and pos.y == enemy_pos.y:
                    logger.debug(
                        f"Corpse already exists at ({pos.x}, {pos.y}), skipping corpse creation"
                    )
                    # Remove enemy entity
                    self.world.delete_entity(enemy)
                    logger.debug(f"Deleted enemy entity with ID: {enemy}")

                    # Add XP to player
                    if self.world.has_component(self.player, Level):
                        player_level = self.world.component_for_entity(
                            self.player, Level
                        )
                        if player_level.add_xp(xp):
                            self.game_state.add_message(
                                "Your battle skills grow stronger! You reached level "
                                + f"{player_level.current_level}!",
                                Colors.YELLOW,
                            )

                    logger.debug(
                        f"Enemy {enemy_render.name} (ID: {enemy}) died at ({enemy_pos.x}, {enemy_pos.y}), player gained {xp} XP"
                    )
                    return

            # Create corpse
            corpse = self.world.create_entity()
            logger.debug(f"Created corpse entity with ID: {corpse}")

            corpse_name = f"remains of {enemy_render.name}"
            self.world.add_component(corpse, Position(enemy_pos.x, enemy_pos.y))
            self.world.add_component(
                corpse,
                Renderable(
                    char="%",
                    color=Colors.RED,
                    render_order=RenderOrder.CORPSE,
                    name=corpse_name,
                ),
            )
            self.world.add_component(corpse, Corpse(enemy_render.name))
            self.world.add_component(
                corpse, Item(name=corpse_name)
            )  # コープスをアイテムとして拾えるようにする

            logger.debug(
                f"Added components to corpse: Position({enemy_pos.x}, {enemy_pos.y}), Renderable('%', RED, CORPSE), Item"
            )

            # Remove all components from enemy entity
            for component_type in self.world._components:
                if self.world.has_component(enemy, component_type):
                    self.world.remove_component(enemy, component_type)

            # Remove enemy entity
            self.world.delete_entity(enemy)
            logger.debug(f"Deleted enemy entity with ID: {enemy}")

            # Add XP to player
            if self.world.has_component(self.player, Level):
                player_level = self.world.component_for_entity(self.player, Level)
                if player_level.add_xp(xp):
                    self.game_state.add_message(
                        "Your battle skills grow stronger! You reached level "
                        + f"{player_level.current_level}!",
                        Colors.YELLOW,
                    )

            logger.debug(
                f"Enemy {enemy_render.name} (ID: {enemy}) died and created corpse (ID: {corpse}) at ({enemy_pos.x}, {enemy_pos.y}), player gained {xp} XP"
            )

        except Exception as e:
            logger.error(f"Error handling enemy death: {str(e)}", exc_info=True)
            raise
