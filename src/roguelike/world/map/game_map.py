import numpy as np
from typing import Optional, List, Tuple
import tcod
from tcod import libtcodpy

from roguelike.world.map.tile import Tile, floor, wall
from roguelike.utils.logger import logger

class GameMap:
    def __init__(self, width: int, height: int):
        logger.info(f"Creating new game map {width}x{height}")
        self.width = width
        self.height = height
        self.tiles = np.full((height, width), fill_value=wall, order="C")
        self.walkable = np.zeros((height, width), dtype=bool, order="C")
        self.transparent = np.zeros((height, width), dtype=bool, order="C")
        self.explored = np.zeros((height, width), dtype=bool, order="C")
        
        # 初期化時にwalkableとtransparent配列を更新
        for y in range(height):
            for x in range(width):
                self.walkable[y, x] = self.tiles[y, x].walkable
                self.transparent[y, x] = self.tiles[y, x].transparent
    
    def in_bounds(self, x: int, y: int) -> bool:
        """指定された座標がマップの範囲内かどうかを返す"""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        """指定された座標のタイルを返す"""
        if not self.in_bounds(x, y):
            logger.warning(f"Attempted to get tile at out-of-bounds coordinates ({x}, {y})")
            return None
        return self.tiles[y, x]
    
    def set_tile(self, x: int, y: int, tile: Tile) -> None:
        """指定された座標にタイルを設定する"""
        if not self.in_bounds(x, y):
            logger.warning(f"Attempted to set tile at out-of-bounds coordinates ({x}, {y})")
            return
        
        logger.debug(f"Setting tile at ({x}, {y}): walkable={tile.walkable}, transparent={tile.transparent}")
        self.tiles[y, x] = tile
        self.walkable[y, x] = tile.walkable
        self.transparent[y, x] = tile.transparent
    
    def compute_fov(self, x: int, y: int) -> np.ndarray:
        """FOVを計算する（TCODのFOV機能を使用）"""
        return tcod.map.compute_fov(
            transparency=self.transparent,
            pov=(y, x),
            radius=0,  # 0は無制限
            light_walls=True,
            algorithm=libtcodpy.FOV_RESTRICTIVE
        )
    
    def render(self, console: tcod.console.Console, visible: np.ndarray) -> None:
        """マップを描画する"""
        # マップの描画範囲を計算
        height = min(self.height, console.height)
        width = min(self.width, console.width)
        logger.debug(f"Rendering map area: {width}x{height}")
        
        # マップの描画
        for y in range(height):
            for x in range(width):
                if y >= console.height or x >= console.width:
                    continue
                
                tile = self.tiles[y, x]
                
                if visible[y, x]:
                    # 視界内のタイル
                    graphics = tile.light
                    self.explored[y, x] = True
                elif self.explored[y, x]:
                    # 探索済みのタイル
                    graphics = tile.dark
                else:
                    # 未探索のタイル
                    graphics = (ord(" "), (0, 0, 0), (0, 0, 0))
                
                # タイルの描画
                ch, fg, bg = graphics
                console.ch[y, x] = ch
                console.fg[y, x] = fg
                console.bg[y, x] = bg 