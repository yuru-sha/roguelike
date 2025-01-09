"""
Map management system for handling map-related operations.
"""

import logging
import numpy as np
from typing import Any, Optional, Tuple

import tcod
from tcod import libtcodpy

from roguelike.core.constants import MAP_HEIGHT, MAP_WIDTH, TORCH_RADIUS, Colors
from roguelike.world.entity.components.base import Position
from roguelike.world.entity.prefabs.player import create_player
from roguelike.world.map.generator.dungeon_generator import DungeonGenerator
from roguelike.world.spawner.spawner import populate_dungeon

logger = logging.getLogger(__name__)

class MapManager:
    """Handles all map-related operations."""

    def __init__(self, world: Any, game_state: Any):
        """Initialize the map manager.
        
        Args:
            world: The game world
            game_state: The current game state
        """
        self.world = world
        self.game_state = game_state
        self.dungeon_generator = DungeonGenerator()
        self.tiles = None
        self.fov_map = None

    def initialize_new_game(self) -> None:
        """Initialize map for a new game."""
        # Generate first dungeon level
        self.tiles, player_pos = self.dungeon_generator.generate(
            self.game_state.dungeon_level
        )

        # Create player
        self.game_state.player = create_player(self.world, *player_pos)

        # Populate dungeon
        populate_dungeon(
            self.world, self.dungeon_generator.rooms, self.game_state.dungeon_level
        )

        # Initialize FOV
        self._initialize_fov()

    def change_level(self) -> None:
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
            self.game_state.player = create_player(self.world, *player_pos)

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

    def _initialize_fov(self) -> None:
        """Initialize the field of view map."""
        if not self.game_state.player:
            return

        player_pos = self.world.component_for_entity(self.game_state.player, Position)

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

    def recompute_fov(self) -> None:
        """Recompute the field of view."""
        if not self.game_state.player:
            return

        player_pos = self.world.component_for_entity(self.game_state.player, Position)

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