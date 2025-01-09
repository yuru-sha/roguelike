"""
Game renderer class that handles all rendering operations.
"""

import logging
import numpy as np
import tcod
from typing import Optional, List, Tuple

from roguelike.core.constants import (
    MAP_HEIGHT, MAP_WIDTH, SCREEN_HEIGHT, SCREEN_WIDTH,
    Colors
)
from roguelike.world.entity.components.base import (
    Position, Renderable, Corpse, RenderOrder
)
from roguelike.world.map.tiles import TileType

logger = logging.getLogger(__name__)

class GameRenderer:
    """Handles all game rendering operations."""

    def __init__(self, root_console: tcod.console.Console):
        """Initialize the renderer.
        
        Args:
            root_console: The root console to render to
        """
        self.root_console = root_console

    def render_map(self, tiles: np.ndarray, fov_map: Optional[np.ndarray]) -> None:
        """Render the game map.
        
        Args:
            tiles: The game map tiles
            fov_map: The field of view map
        """
        if fov_map is None:
            return

        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = fov_map[y, x]
                if visible:
                    # Tile is visible
                    if tiles[y][x].tile_type == TileType.WALL:
                        # Wall
                        self.root_console.rgb[y, x]["ch"] = ord("#")
                        self.root_console.rgb[y, x]["fg"] = Colors.LIGHT_WALL
                    elif tiles[y][x].tile_type == TileType.STAIRS_DOWN:
                        # Down stairs
                        self.root_console.rgb[y, x]["ch"] = ord(">")
                        self.root_console.rgb[y, x]["fg"] = Colors.WHITE
                    elif tiles[y][x].tile_type == TileType.STAIRS_UP:
                        # Up stairs
                        self.root_console.rgb[y, x]["ch"] = ord("<")
                        self.root_console.rgb[y, x]["fg"] = Colors.WHITE
                    else:
                        # Floor
                        self.root_console.rgb[y, x]["ch"] = ord(".")
                        self.root_console.rgb[y, x]["fg"] = Colors.LIGHT_GROUND
                    self.root_console.rgb[y, x]["bg"] = (0, 0, 0)
                    tiles[y][x].explored = True
                elif tiles[y][x].explored:
                    # Tile has been explored but is not visible
                    if tiles[y][x].tile_type == TileType.WALL:
                        # Wall
                        self.root_console.rgb[y, x]["ch"] = ord("#")
                        self.root_console.rgb[y, x]["fg"] = Colors.DARK_WALL
                    elif tiles[y][x].tile_type == TileType.STAIRS_DOWN:
                        # Down stairs
                        self.root_console.rgb[y, x]["ch"] = ord(">")
                        self.root_console.rgb[y, x]["fg"] = Colors.DARK_GROUND
                    elif tiles[y][x].tile_type == TileType.STAIRS_UP:
                        # Up stairs
                        self.root_console.rgb[y, x]["ch"] = ord("<")
                        self.root_console.rgb[y, x]["fg"] = Colors.DARK_GROUND
                    else:
                        # Floor
                        self.root_console.rgb[y, x]["ch"] = ord(".")
                        self.root_console.rgb[y, x]["fg"] = Colors.DARK_GROUND
                    self.root_console.rgb[y, x]["bg"] = (0, 0, 0)

    def render_entities(self, world, tiles: np.ndarray, fov_map: Optional[np.ndarray]) -> None:
        """Render all entities.
        
        Args:
            world: The game world
            tiles: The game map tiles
            fov_map: The field of view map
        """
        # Sort entities by render order
        entities_in_render_order = sorted(
            world.get_components(Position, Renderable),
            key=lambda x: x[1][1].render_order,
        )

        logger.debug(f"Rendering {len(entities_in_render_order)} entities")

        for ent, (pos, render) in entities_in_render_order:
            # 死体は探索済みの領域では常に表示
            is_corpse = world.has_component(ent, Corpse)
            if is_corpse:
                logger.debug(f"Found corpse at ({pos.x}, {pos.y}): {render.name}")

            # 視界内か、死体かつ探索済みの場合に表示
            visible = fov_map[pos.y, pos.x] if fov_map is not None else False
            explored = tiles[pos.y][pos.x].explored if tiles is not None else False

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

    def render_messages(self, game_messages: List[Tuple[str, Tuple[int, int, int]]]) -> None:
        """Render message log.
        
        Args:
            game_messages: List of game messages with their colors
        """
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
            messages = game_messages[-message_height:]
            for i, message in enumerate(messages):
                self.root_console.print(
                    x=message_x, y=message_y + i, string=message.text, fg=message.color
                )

        except Exception as e:
            logger.error(f"Error rendering messages: {str(e)}", exc_info=True)
            raise

    def clear(self) -> None:
        """Clear the console."""
        self.root_console.clear() 