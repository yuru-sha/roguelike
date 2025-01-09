"""
The main game engine class that coordinates all game systems.
"""

from typing import Dict, Any, Optional, List, Tuple
import sys
import os
from pathlib import Path
import numpy as np
import tcod
import tcod.event
from tcod import libtcodpy
import esper

from roguelike.core.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    MAP_WIDTH, MAP_HEIGHT,
    TORCH_RADIUS,
    Colors
)
from roguelike.game.states.game_state import GameState, GameStates
from roguelike.ui.handlers.input_handler import InputHandler
from roguelike.ui.screens.save_load_screen import SaveLoadScreen
from roguelike.world.map.generator.dungeon_generator import DungeonGenerator
from roguelike.world.entity.components.base import (
    Position, Renderable, Fighter, Item, Equipment,
    Level, AI, Inventory, EquipmentSlots, Corpse
)
from roguelike.world.entity.prefabs.player import create_player
from roguelike.world.spawner.spawner import populate_dungeon
from roguelike.world.map.tiles import TileType
from roguelike.utils.logging import GameLogger
from roguelike.utils.serialization import SaveManager

logger = GameLogger.get_instance()

class Engine:
    """
    The main game engine class that coordinates all game systems.
    """
    
    def __init__(self):
        """Initialize the game engine."""
        logger.info("Initializing game engine")
        
        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent.parent
        assets_path = project_root / 'data' / 'assets' / 'dejavu10x10_gs_tc.png'
        
        # Initialize TCOD
        self.root_console = tcod.console.Console(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.context = tcod.context.new(
            columns=SCREEN_WIDTH,
            rows=SCREEN_HEIGHT,
            title="Roguelike",
            tileset=tcod.tileset.load_tilesheet(
                str(assets_path),
                32, 8, tcod.tileset.CHARMAP_TCOD
            ),
            vsync=True
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
        
        logger.info("Game engine initialized")
    
    def save_game(self, slot: int = 0) -> None:
        """
        Save the current game state.
        
        Args:
            slot: Save slot number
        """
        logger.info(f"Saving game to slot {slot}")
        
        # Collect all entities and their components
        entities = {}
        for entity_id in self.world.entities:
            components = {}
            for component_type in self.world.components_for_entity(entity_id):
                component = self.world.component_for_entity(entity_id, component_type)
                components[component_type.__name__] = component.to_dict()
            entities[entity_id] = components
        
        # Convert tiles to serializable format
        tiles_data = []
        for row in self.tiles:
            tiles_row = []
            for tile in row:
                tiles_row.append({
                    'blocked': tile.blocked,
                    'block_sight': tile.block_sight,
                    'explored': tile.explored,
                    'tile_type': tile.tile_type.name
                })
            tiles_data.append(tiles_row)
        
        # Prepare save data
        save_data = {
            'game_state': self.game_state.to_dict(),
            'entities': entities,
            'tiles': tiles_data,
            'player_id': self.player,
            'dungeon_level': self.game_state.dungeon_level
        }
        
        # Save to file
        SaveManager.save_game(save_data, slot)
        logger.info("Game saved successfully")
    
    def load_game(self, slot: int = 0) -> bool:
        """
        Load a saved game state.
        
        Args:
            slot: Save slot number
            
        Returns:
            True if game was loaded successfully
        """
        logger.info(f"Loading game from slot {slot}")
        
        # Load save data
        save_data = SaveManager.load_game(slot)
        if not save_data:
            logger.warning(f"No save file found in slot {slot}")
            return False
        
        try:
            # Clear current state
            self.world = esper.World()
            
            # Restore game state
            self.game_state = GameState.from_dict(save_data['game_state'])
            
            # Restore tiles
            self.tiles = np.empty((MAP_HEIGHT, MAP_WIDTH), dtype=object)
            for y, row in enumerate(save_data['tiles']):
                for x, tile_data in enumerate(row):
                    self.tiles[y][x] = TileType[tile_data['tile_type']].value
                    self.tiles[y][x].explored = tile_data['explored']
            
            # Restore entities
            for entity_id, components in save_data['entities'].items():
                entity_id = int(entity_id)  # JSON converts keys to strings
                for component_name, component_data in components.items():
                    module = __import__('roguelike.world.entity.components.base', fromlist=[component_name])
                    component_class = getattr(module, component_name)
                    component = component_class.from_dict(component_data)
                    self.world.add_component(entity_id, component)
            
            # Restore player reference
            self.player = save_data['player_id']
            
            # Recompute FOV
            self._initialize_fov()
            
            logger.info("Game loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load game: {e}", exc_info=True)
            return False
    
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
            algorithm=libtcodpy.FOV_BASIC
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
            algorithm=libtcodpy.FOV_BASIC
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
                            self.root_console.rgb[y, x]["ch"] = ord('#')
                            self.root_console.rgb[y, x]["fg"] = Colors.LIGHT_WALL
                        elif self.tiles[y][x].tile_type == TileType.STAIRS_DOWN:
                            # Down stairs
                            self.root_console.rgb[y, x]["ch"] = ord('>')
                            self.root_console.rgb[y, x]["fg"] = Colors.WHITE
                        elif self.tiles[y][x].tile_type == TileType.STAIRS_UP:
                            # Up stairs
                            self.root_console.rgb[y, x]["ch"] = ord('<')
                            self.root_console.rgb[y, x]["fg"] = Colors.WHITE
                        else:
                            # Floor
                            self.root_console.rgb[y, x]["ch"] = ord('.')
                            self.root_console.rgb[y, x]["fg"] = Colors.LIGHT_GROUND
                        self.root_console.rgb[y, x]["bg"] = (0, 0, 0)
                        self.tiles[y][x].explored = True
                    elif self.tiles[y][x].explored:
                        # Tile has been explored but is not visible
                        if self.tiles[y][x].tile_type == TileType.WALL:
                            # Wall
                            self.root_console.rgb[y, x]["ch"] = ord('#')
                            self.root_console.rgb[y, x]["fg"] = Colors.DARK_WALL
                        elif self.tiles[y][x].tile_type == TileType.STAIRS_DOWN:
                            # Down stairs
                            self.root_console.rgb[y, x]["ch"] = ord('>')
                            self.root_console.rgb[y, x]["fg"] = Colors.DARK_GROUND
                        elif self.tiles[y][x].tile_type == TileType.STAIRS_UP:
                            # Up stairs
                            self.root_console.rgb[y, x]["ch"] = ord('<')
                            self.root_console.rgb[y, x]["fg"] = Colors.DARK_GROUND
                        else:
                            # Floor
                            self.root_console.rgb[y, x]["ch"] = ord('.')
                            self.root_console.rgb[y, x]["fg"] = Colors.DARK_GROUND
                        self.root_console.rgb[y, x]["bg"] = (0, 0, 0)
    
    def _render_entities(self) -> None:
        """Render all entities."""
        # Sort entities by render order
        entities_in_render_order = sorted(
            self.world.get_components(Position, Renderable),
            key=lambda x: x[1][1].render_order
        )
        
        for ent, (pos, render) in entities_in_render_order:
            if self.fov_map is not None and self.fov_map[pos.y, pos.x]:
                self.root_console.print(
                    y=pos.y,
                    x=pos.x,
                    string=render.char,
                    fg=render.color
                )
    
    def _handle_movement(self, action: Dict[str, Any]) -> None:
        """Handle movement action."""
        try:
            if not self.player:
                logger.warning("Movement attempted but no player entity exists")
                return
                
            dx = action.get('dx', 0)
            dy = action.get('dy', 0)
            logger.debug(f"Movement attempt: dx={dx}, dy={dy}")
            
            player_pos = self.world.component_for_entity(self.player, Position)
            dest_x = player_pos.x + dx
            dest_y = player_pos.y + dy
            logger.debug(f"Current position: ({player_pos.x}, {player_pos.y}), Target position: ({dest_x}, {dest_y})")
            
            # Check if destination is within bounds
            if not (0 <= dest_x < MAP_WIDTH and 0 <= dest_y < MAP_HEIGHT):
                logger.debug(f"Movement blocked: destination out of bounds ({dest_x}, {dest_y})")
                return
                
            # Check if destination is walkable
            if self.tiles[dest_y][dest_x].blocked or self.tiles[dest_y][dest_x].block_sight:
                logger.debug(f"Movement blocked: destination is blocked at ({dest_x}, {dest_y})")
                return
                
            # Check for combat
            target = None
            for ent, (pos, fighter) in self.world.get_components(Position, Fighter):
                if ent != self.player and pos.x == dest_x and pos.y == dest_y:
                    target = ent
                    break
            
            if target is not None:
                # Handle combat
                attacker_fighter = self.world.component_for_entity(self.player, Fighter)
                defender_fighter = self.world.component_for_entity(target, Fighter)
                
                damage = attacker_fighter.power - defender_fighter.defense
                if damage > 0:
                    defender_fighter.hp -= damage
                    defender_name = self.world.component_for_entity(target, Renderable).name
                    self.game_state.add_message(
                        f"You attack the {defender_name} for {damage} damage!",
                        Colors.WHITE
                    )
                    logger.info(f"Combat: Player dealt {damage} damage to {defender_name}")
                    
                    if defender_fighter.hp <= 0:
                        self.game_state.add_message(
                            f"The {defender_name} dies!",
                            Colors.RED
                        )
                        self.world.delete_entity(target)
                        logger.info(f"Combat: {defender_name} was defeated")
                else:
                    defender_name = self.world.component_for_entity(target, Renderable).name
                    self.game_state.add_message(
                        f"You attack the {defender_name} but do no damage!",
                        Colors.WHITE
                    )
                    logger.info(f"Combat: Attack on {defender_name} did no damage")
            else:
                # Check for items at destination
                for ent, (pos, item) in self.world.get_components(Position, Item):
                    if pos.x == dest_x and pos.y == dest_y:
                        item_name = self.world.component_for_entity(ent, Renderable).name
                        self.game_state.add_message(
                            f"There is {item_name} here.",
                            Colors.LIGHT_CYAN
                        )
                        break
                
                # Move player
                player_pos.x = dest_x
                player_pos.y = dest_y
                logger.debug(f"Player moved to ({dest_x}, {dest_y})")
                self._recompute_fov()
        except Exception as e:
            logger.error(f"Error in movement handling: {str(e)}", exc_info=True)
            raise
    
    def _handle_stairs(self, action: Dict[str, Any]) -> None:
        """Handle stair usage action."""
        try:
            if not self.player:
                logger.warning("Stair usage attempted but no player entity exists")
                return
                
            direction = action.get('direction')
            player_pos = self.world.component_for_entity(self.player, Position)
            current_tile = self.tiles[player_pos.y][player_pos.x]
            
            logger.debug(f"Attempting to use stairs: direction={direction}, player_pos=({player_pos.x}, {player_pos.y})")
            
            if direction == 'down' and current_tile.tile_type == TileType.STAIRS_DOWN:
                # Go down stairs
                self.game_state.dungeon_level += 1
                logger.info(f"Player descended to level {self.game_state.dungeon_level}")
                self.game_state.add_message(
                    f"You descend deeper into the dungeon (Level {self.game_state.dungeon_level}).",
                    Colors.WHITE
                )
                self._change_level()
                
            elif direction == 'up' and current_tile.tile_type == TileType.STAIRS_UP:
                # Go up stairs
                if self.game_state.dungeon_level > 1:
                    self.game_state.dungeon_level -= 1
                    logger.info(f"Player ascended to level {self.game_state.dungeon_level}")
                    self.game_state.add_message(
                        f"You climb up the stairs (Level {self.game_state.dungeon_level}).",
                        Colors.WHITE
                    )
                    self._change_level()
                else:
                    logger.info("Player attempted to leave the dungeon")
                    if self.game_state.player_has_amulet:
                        # Victory!
                        self.game_state.add_message(
                            "You escaped the dungeon with the Amulet of Yendor! You win!",
                            Colors.YELLOW
                        )
                        logger.info("Player won the game!")
                        self.game_state.game_won = True
                        self.quit_game()
                    else:
                        self.game_state.add_message(
                            "You need the Amulet of Yendor to leave the dungeon!",
                            Colors.RED
                        )
            else:
                # No stairs here
                if direction == 'down':
                    self.game_state.add_message(
                        "There are no stairs down here.",
                        Colors.YELLOW
                    )
                else:
                    self.game_state.add_message(
                        "There are no stairs up here.",
                        Colors.YELLOW
                    )
                logger.debug(f"No {direction} stairs at current position")
        
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
            self.tiles, player_pos = self.dungeon_generator.generate(self.game_state.dungeon_level)
            
            # Create player at appropriate position
            self.player = create_player(self.world, *player_pos)
            
            # Populate new level
            populate_dungeon(self.world, self.dungeon_generator.rooms, self.game_state.dungeon_level)
            
            # Initialize FOV
            self._initialize_fov()
            
            logger.info("Level change completed")
        
        except Exception as e:
            logger.error(f"Error changing level: {str(e)}", exc_info=True)
            raise
    
    def handle_action(self, action: Dict[str, Any]) -> None:
        """Handle a game action."""
        try:
            action_type = action.get('action')
            logger.debug(f"Handling action: {action_type}")
            
            if action_type == 'move':
                self._handle_movement(action)
            elif action_type == 'use_stairs':
                self._handle_stairs(action)
            elif action_type == 'wait':
                logger.debug("Player waited")
                pass  # Do nothing, just pass the turn
            elif action_type == 'exit':
                if self.game_state.state in (GameStates.SAVE_GAME, GameStates.LOAD_GAME):
                    self.game_state.state = GameStates.PLAYERS_TURN
                    self.save_load_screen = None
                else:
                    logger.info("Player initiated game exit")
                    self.quit_game()
                    return
            elif action_type == 'save_game':
                self.game_state.state = GameStates.SAVE_GAME
                self.save_load_screen = SaveLoadScreen(self.root_console, is_save=True)
            elif action_type == 'load_game':
                self.game_state.state = GameStates.LOAD_GAME
                self.save_load_screen = SaveLoadScreen(self.root_console, is_save=False)
            elif action_type == 'select' and self.save_load_screen:
                if self.game_state.state == GameStates.SAVE_GAME:
                    self.save_game(self.save_load_screen.selected_slot)
                    self.game_state.add_message(
                        f"Game saved to slot {self.save_load_screen.selected_slot}",
                        Colors.GREEN
                    )
                    self.game_state.state = GameStates.PLAYERS_TURN
                    self.save_load_screen = None
                elif self.game_state.state == GameStates.LOAD_GAME:
                    if self.load_game(self.save_load_screen.selected_slot):
                        self.game_state.add_message(
                            f"Game loaded from slot {self.save_load_screen.selected_slot}",
                            Colors.GREEN
                        )
                        self.game_state.state = GameStates.PLAYERS_TURN
                        self.save_load_screen = None
                    else:
                        self.game_state.add_message(
                            "Failed to load game",
                            Colors.RED
                        )
            elif action_type == 'move_cursor' and self.save_load_screen:
                dy = action.get('dy', 0)
                if dy < 0:
                    self.save_load_screen.selected_slot = max(0, self.save_load_screen.selected_slot - 1)
                elif dy > 0:
                    self.save_load_screen.selected_slot = min(9, self.save_load_screen.selected_slot + 1)
            
            # Update FOV after any action
            self._recompute_fov()
        except Exception as e:
            logger.error(f"Error handling action {action}: {str(e)}", exc_info=True)
            raise
    
    def new_game(self) -> None:
        """Start a new game."""
        logger.info("Starting new game")
        
        # Generate first dungeon level
        self.tiles, player_pos = self.dungeon_generator.generate(self.game_state.dungeon_level)
        
        # Create player
        self.player = create_player(self.world, *player_pos)
        
        # Populate dungeon
        populate_dungeon(self.world, self.dungeon_generator.rooms, self.game_state.dungeon_level)
        
        # Initialize FOV
        self._initialize_fov()
        
        # Add welcome message
        self.game_state.add_message(
            "Welcome to the Roguelike! Prepare to die...",
            Colors.WHITE
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
                            
                            action = self.input_handler.handle_input(event)
                            logger.debug(f"Input event: {event}, resulting action: {action}")
                            
                            if action:
                                self.handle_action(action)
                                
                                if not self.running:
                                    break
                        except Exception as e:
                            logger.error(f"Error handling event {event}: {str(e)}", exc_info=True)
                            raise
                except Exception as e:
                    logger.error(f"Error in game loop iteration: {str(e)}", exc_info=True)
                    raise
        
        except Exception as e:
            logger.error(f"Fatal error in game loop: {str(e)}", exc_info=True)
            raise
        
        finally:
            logger.info("Cleaning up game resources")
            self.cleanup() 
    
    def render(self) -> None:
        """Render the game screen."""
        try:
            # Clear the console
            self.root_console.clear()
            
            if self.game_state.state in (GameStates.SAVE_GAME, GameStates.LOAD_GAME) and self.save_load_screen:
                # Render save/load screen
                self.save_load_screen.render()
            else:
                # Render normal game screen
                self._render_map()
                self._render_entities()
            
            # Present the console
            self.context.present(self.root_console)
            
        except Exception as e:
            logger.error(f"Error in render: {str(e)}", exc_info=True)
            raise 