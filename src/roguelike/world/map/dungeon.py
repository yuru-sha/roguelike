from typing import Iterator, List, Tuple, Any
import random
import tcod
import numpy as np

from roguelike.world.map.game_map import GameMap
from roguelike.world.map.tile import floor, wall
from roguelike.utils.logger import logger
from roguelike.world.entity.factory import EntityFactory

class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        # 外壁を含む座標
        self.x1 = x
        self.y1 = y
        self.x2 = x + width - 1
        self.y2 = y + height - 1
        
        # 内部（床）の座標
        self.inner_x1 = x + 1
        self.inner_x2 = x + width - 2
        self.inner_y1 = y + 1
        self.inner_y2 = y + height - 2
        
        logger.debug(f"Created room at ({x}, {y}) with size {width}x{height}")
    
    @property
    def center(self) -> Tuple[int, int]:
        """部屋の中心座標を返す"""
        center_x = (self.inner_x1 + self.inner_x2) // 2
        center_y = (self.inner_y1 + self.inner_y2) // 2
        return center_x, center_y
    
    def intersects(self, other: "RectangularRoom") -> bool:
        """他の部屋と重なっているかどうかを返す"""
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )

def generate_dungeon(
    map_width: int,
    map_height: int,
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    world: Any,
) -> Tuple[GameMap, Tuple[int, int]]:
    """ダンジョンを生成する"""
    logger.info(f"Generating dungeon {map_width}x{map_height} with {max_rooms} rooms")
    logger.debug(f"Room size range: {room_min_size}-{room_max_size}")
    
    dungeon = GameMap(map_width, map_height)
    rooms: List[RectangularRoom] = []
    entity_factory = EntityFactory(world)
    
    for r in range(max_rooms):
        # ランダムな部屋を生成（Rogueライクな小さめの部屋）
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)
        
        x = random.randint(1, dungeon.width - room_width - 1)
        y = random.randint(1, dungeon.height - room_height - 1)
        
        new_room = RectangularRoom(x, y, room_width, room_height)
        
        # 他の部屋と重なっていないか確認
        if any(new_room.intersects(other_room) for other_room in rooms):
            logger.debug(f"Room {r+1} intersects with existing room, skipping")
            continue
        
        # 部屋の内部を床に、外周を壁にする
        for y in range(new_room.y1, new_room.y2 + 1):
            for x in range(new_room.x1, new_room.x2 + 1):
                if (x == new_room.x1 or x == new_room.x2 or 
                    y == new_room.y1 or y == new_room.y2):
                    # 外周は壁
                    dungeon.set_tile(x, y, wall)
                else:
                    # 内部は床
                    dungeon.set_tile(x, y, floor)
        
        logger.debug(f"Added room {r+1} at ({x}, {y})")
        
        if len(rooms) == 0:
            # 最初の部屋の中心をプレイヤーの初期位置とする
            player_start = new_room.center
            logger.info(f"Set player start position to {player_start}")
        else:
            # 既存の部屋とランダムに接続する（2-3個の部屋と接続）
            connect_count = min(len(rooms), random.randint(2, 3))
            # 接続する部屋をランダムに選択
            connect_rooms = random.sample(rooms, connect_count)
            
            for room in connect_rooms:
                # 通路を生成（壁付き）
                tunnel_tiles = list(tunnel_between(room.center, new_room.center))
                
                # まず通路を床にする
                for x, y in tunnel_tiles:
                    dungeon.set_tile(x, y, floor)
                
                # 通路の両側に壁を設置
                for x, y in tunnel_tiles:
                    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nx, ny = x + dx, y + dy
                        if dungeon.in_bounds(nx, ny) and dungeon.tiles[ny, nx] == wall:
                            continue  # 既に壁がある場合はスキップ
                        if dungeon.in_bounds(nx, ny) and not dungeon.walkable[ny, nx]:
                            dungeon.set_tile(nx, ny, wall)
        
        rooms.append(new_room)
    
    logger.info(f"Generated {len(rooms)} rooms")
    
    # モンスターの配置
    for room in rooms[1:]:
        if random.random() < 0.8:  # 80%の確率でモンスターを配置
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)
            
            if random.random() < 0.8:  # 80%の確率でオーク
                entity_factory.create_monster(x, y, "orc")
            else:  # 20%の確率でトロル
                entity_factory.create_monster(x, y, "troll")
    
    # アイテムの配置
    for room in rooms:
        if random.random() < 0.7:  # 70%の確率でアイテムを配置
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)
            
            item_chance = random.random()
            if item_chance < 0.4:  # 40%の確率で回復ポーション
                entity_factory.create_healing_potion(x, y)
            elif item_chance < 0.5:  # 10%の確率で剣
                entity_factory.create_sword(x, y)
            elif item_chance < 0.6:  # 10%の確率で盾
                entity_factory.create_shield(x, y)
            elif item_chance < 0.7:  # 10%の確率で雷の巻物
                entity_factory.create_lightning_scroll(x, y)
            elif item_chance < 0.8:  # 10%の確率でファイアーボールの巻物
                entity_factory.create_fireball_scroll(x, y)
            elif item_chance < 0.9:  # 10%の確率で混乱の巻物
                entity_factory.create_confusion_scroll(x, y)
            elif item_chance < 0.95:  # 5%の確率で麻痺の巻物
                entity_factory.create_paralyze_scroll(x, y)
            else:  # 5%の確率で狂戦士化のポーション
                entity_factory.create_berserk_potion(x, y)
    
    return dungeon, player_start

def tunnel_between(
    start: Tuple[int, int],
    end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """2点間を結ぶL字型の通路を生成する（1マス幅）"""
    x1, y1 = start
    x2, y2 = end
    logger.debug(f"Creating tunnel from {start} to {end}")
    
    # ランダムに縦→横か横→縦かを決める
    if random.random() < 0.5:
        corner_x, corner_y = x2, y1
        logger.debug("Tunnel pattern: horizontal then vertical")
    else:
        corner_x, corner_y = x1, y2
        logger.debug("Tunnel pattern: vertical then horizontal")
        
    # 通路の座標を生成（1マス幅）
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y 