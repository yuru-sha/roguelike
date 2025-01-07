from typing import List, Tuple, Optional
from tcod_ecs import World

from roguelike.world.entity.components import Position, Renderable, Fighter, AI
from roguelike.utils.logger import logger

class EntitySystem:
    """エンティティの管理システム"""
    
    def __init__(self, world: World):
        self.world = world
    
    def get_blocking_entity_at_location(self, x: int, y: int) -> Optional[int]:
        """指定位置にいるエンティティを取得"""
        for entity, (pos,) in self.world.get_components((Position,)):
            if pos.x == x and pos.y == y:
                return entity
        return None
    
    def move_entity(self, entity: int, dx: int, dy: int) -> bool:
        """エンティティを移動"""
        if not self.world.has_component(entity, Position):
            return False
            
        pos = self.world.get_component(entity, Position)
        new_x = pos.x + dx
        new_y = pos.y + dy
        
        # 移動先に他のエンティティがいないか確認
        blocking_entity = self.get_blocking_entity_at_location(new_x, new_y)
        if blocking_entity is not None:
            logger.debug(f"Entity {entity} blocked by entity {blocking_entity} at ({new_x}, {new_y})")
            return False
        
        pos.x = new_x
        pos.y = new_y
        logger.debug(f"Entity {entity} moved to ({new_x}, {new_y})")
        return True
    
    def get_entities_at(self, x: int, y: int) -> List[int]:
        """指定位置にいるすべてのエンティティを取得"""
        entities = []
        for entity, (pos,) in self.world.get_components((Position,)):
            if pos.x == x and pos.y == y:
                entities.append(entity)
        return entities
    
    def get_renderable_data(self, entity: int) -> Optional[Tuple[str, Tuple[int, int, int], Tuple[int, int, int]]]:
        """エンティティの描画データを取得"""
        if not self.world.has_component(entity, Renderable):
            return None
            
        renderable = self.world.get_component(entity, Renderable)
        return (renderable.char, renderable.fg_color, renderable.bg_color)
    
    def get_fighter_data(self, entity: int) -> Optional[Fighter]:
        """エンティティの戦闘データを取得"""
        if not self.world.has_component(entity, Fighter):
            return None
            
        return self.world.get_component(entity, Fighter)
    
    def is_ai_controlled(self, entity: int) -> bool:
        """エンティティがAI制御かどうかを確認"""
        return self.world.has_component(entity, AI) 