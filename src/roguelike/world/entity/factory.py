from typing import Tuple, Any
import esper

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
    
    def __init__(self, world: Any):
        self.world = world
    
    def create_player(self, x: int, y: int) -> int:
        """プレイヤーエンティティを作成"""
        return self.world.create_entity(
            Position(x=x, y=y),
            Renderable(
                char="@",
                fg_color=(255, 255, 255),
                bg_color=(0, 0, 0)
            ),
            Fighter(
                max_hp=30,
                hp=30,
                defense=2,
                power=5
            ),
            Inventory(),
            Name(name="Player")
        )
    
    def create_monster(self, x: int, y: int, monster_type: str) -> int:
        """モンスターエンティティを作成"""
        components = [
            Position(x=x, y=y),
            AI()
        ]
        
        if monster_type == "orc":
            components.extend([
                Renderable(
                    char="o",
                    fg_color=(63, 127, 63),
                    bg_color=(0, 0, 0)
                ),
                Fighter(
                    max_hp=10,
                    hp=10,
                    defense=0,
                    power=3
                ),
                Name(name="Orc")
            ])
        
        elif monster_type == "troll":
            components.extend([
                Renderable(
                    char="T",
                    fg_color=(0, 127, 0),
                    bg_color=(0, 0, 0)
                ),
                Fighter(
                    max_hp=16,
                    hp=16,
                    defense=1,
                    power=4
                ),
                Name(name="Troll")
            ])
        
        return self.world.create_entity(*components)
    
    def create_item(self, x: int, y: int, item_type: str) -> int:
        """アイテムエンティティを作成"""
        components = [Position(x=x, y=y)]
        
        if item_type == "healing_potion":
            components.extend([
                Renderable(
                    char="!",
                    fg_color=(127, 0, 255),
                    bg_color=(0, 0, 0)
                ),
                Item(
                    weight=0.1,
                    value=50
                ),
                Name(name="Healing Potion")
            ])
        
        return self.world.create_entity(*components) 