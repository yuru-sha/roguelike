from typing import List, Tuple, Optional, Any
import esper

from roguelike.world.entity.components import Position, Renderable, Fighter, AI, Item
from roguelike.utils.logger import logger

class EntitySystem:
    """エンティティの管理システム"""
    
    def __init__(self, world: Any, game_map=None):
        self.world = world
        self.game_map = game_map
    
    def set_game_map(self, game_map):
        """ゲームマップの参照を設定"""
        self.game_map = game_map
    
    def get_blocking_entity_at_location(self, x: int, y: int) -> Optional[int]:
        """指定位置にいるエンティティを取得"""
        for ent, (pos,) in self.world.get_components(Position):
            if pos.x == x and pos.y == y:
                return ent
        return None
    
    def move_entity(self, entity: int, dx: int, dy: int) -> bool:
        """エンティティを移動する"""
        if not self.world.has_component(entity, Position):
            return False
            
        pos = self.world.component_for_entity(entity, Position)
        new_x = pos.x + dx
        new_y = pos.y + dy
        
        # マップ境界チェック
        if not self.game_map.in_bounds(new_x, new_y):
            return False
            
        # 壁チェック
        if not self.game_map.walkable[new_y, new_x]:
            return False
            
        # 他のエンティティとの衝突チェック
        for ent in self.get_entities_at(new_x, new_y):
            # アイテムは通過可能
            if self.world.has_component(ent, Item):
                continue
            # 戦闘可能なエンティティ同士は衝突
            if (self.world.has_component(entity, Fighter) and 
                self.world.has_component(ent, Fighter)):
                return False
        
        # 移動
        pos.x = new_x
        pos.y = new_y
        
        return True
    
    def get_entities_at(self, x: int, y: int) -> List[int]:
        """指定座標にあるエンティティのリストを返す"""
        entities = []
        for ent, (pos,) in self.world.get_components(Position):
            if pos.x == x and pos.y == y:
                entities.append(ent)
        # エンティティIDの小さい順（生成順）にソート
        return sorted(entities)
    
    def get_renderable_data(self, entity: int) -> Optional[Tuple[str, Tuple[int, int, int], Tuple[int, int, int]]]:
        """エンティティの描画データを取得"""
        if not self.world.has_component(entity, Renderable):
            return None
            
        renderable = self.world.component_for_entity(entity, Renderable)
        return (renderable.char, renderable.fg_color, renderable.bg_color)
    
    def get_fighter_data(self, entity: int) -> Optional[Fighter]:
        """エンティティの戦闘データを取得"""
        if not self.world.has_component(entity, Fighter):
            return None
            
        return self.world.component_for_entity(entity, Fighter)
    
    def is_ai_controlled(self, entity: int) -> bool:
        """エンティティがAI制御かどうかを確認"""
        return self.world.has_component(entity, AI) 