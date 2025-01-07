from typing import Tuple
from tcod_ecs import World

from roguelike.world.entity.components import (
    Position,
    Renderable,
    Fighter,
    AI,
    Item,
    Inventory,
    Name,
)

class EntityFactory:
    """エンティティの生成を管理するファクトリクラス"""
    
    def __init__(self, world: World):
        self.world = world
    
    def create_player(self, x: int, y: int) -> int:
        """プレイヤーエンティティを作成"""
        entity = self.world.new_entity()
        self.world.add_component(entity, Position(x=x, y=y))
        self.world.add_component(entity, Renderable(
            char="@",
            fg_color=(255, 255, 255),
            bg_color=(0, 0, 0)
        ))
        self.world.add_component(entity, Fighter(
            max_hp=30,
            hp=30,
            defense=2,
            power=5
        ))
        self.world.add_component(entity, Inventory())
        self.world.add_component(entity, Name(name="Player"))
        return entity
    
    def create_monster(self, x: int, y: int, monster_type: str) -> int:
        """モンスターエンティティを作成"""
        entity = self.world.new_entity()
        self.world.add_component(entity, Position(x=x, y=y))
        
        if monster_type == "orc":
            self.world.add_component(entity, Renderable(
                char="o",
                fg_color=(63, 127, 63),
                bg_color=(0, 0, 0)
            ))
            self.world.add_component(entity, Fighter(
                max_hp=10,
                hp=10,
                defense=0,
                power=3
            ))
            self.world.add_component(entity, Name(name="Orc"))
        
        elif monster_type == "troll":
            self.world.add_component(entity, Renderable(
                char="T",
                fg_color=(0, 127, 0),
                bg_color=(0, 0, 0)
            ))
            self.world.add_component(entity, Fighter(
                max_hp=16,
                hp=16,
                defense=1,
                power=4
            ))
            self.world.add_component(entity, Name(name="Troll"))
        
        self.world.add_component(entity, AI())
        return entity
    
    def create_item(self, x: int, y: int, item_type: str) -> int:
        """アイテムエンティティを作成"""
        entity = self.world.new_entity()
        self.world.add_component(entity, Position(x=x, y=y))
        
        if item_type == "healing_potion":
            self.world.add_component(entity, Renderable(
                char="!",
                fg_color=(127, 0, 255),
                bg_color=(0, 0, 0)
            ))
            self.world.add_component(entity, Item(
                weight=0.1,
                value=50
            ))
            self.world.add_component(entity, Name(name="Healing Potion"))
        
        return entity 