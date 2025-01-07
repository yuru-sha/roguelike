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
    Equipment,
)
from roguelike.world.entity.item_functions import heal, cast_lightning, cast_fireball, cast_confusion

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
            Inventory(capacity=26),
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
    
    def create_healing_potion(self, x: int, y: int) -> int:
        """回復ポーションを作成"""
        potion = self.world.create_entity()
        
        self.world.add_component(potion, Position(x=x, y=y))
        self.world.add_component(potion, Renderable(
            char="!",
            fg_color=(127, 0, 255),
            bg_color=(0, 0, 0)
        ))
        self.world.add_component(potion, Name(name="Healing Potion"))
        self.world.add_component(potion, Item(
            use_function=heal,
            targeting=False,
            amount=4
        ))
        
        return potion
    
    def create_lightning_scroll(self, x: int, y: int) -> int:
        """雷の巻物を作成"""
        scroll = self.world.create_entity()
        
        self.world.add_component(scroll, Position(x=x, y=y))
        self.world.add_component(scroll, Renderable(
            char="?",
            fg_color=(255, 255, 0),
            bg_color=(0, 0, 0)
        ))
        self.world.add_component(scroll, Name(name="Lightning Scroll"))
        self.world.add_component(scroll, Item(
            use_function=cast_lightning,
            targeting=True,
            targeting_message="Left-click an enemy to strike it with lightning",
            damage=20
        ))
        
        return scroll
    
    def create_sword(self, x: int, y: int) -> int:
        """剣を作成"""
        sword = self.world.create_entity()
        
        self.world.add_component(sword, Position(x=x, y=y))
        self.world.add_component(sword, Renderable(
            char="/",
            fg_color=(0, 191, 255),
            bg_color=(0, 0, 0)
        ))
        self.world.add_component(sword, Name(name="Sword"))
        self.world.add_component(sword, Item())
        self.world.add_component(sword, Equipment(
            slot="weapon",
            power_bonus=3
        ))
        
        return sword
    
    def create_shield(self, x: int, y: int) -> int:
        """盾を作成"""
        shield = self.world.create_entity()
        
        self.world.add_component(shield, Position(x=x, y=y))
        self.world.add_component(shield, Renderable(
            char="[",
            fg_color=(0, 191, 255),
            bg_color=(0, 0, 0)
        ))
        self.world.add_component(shield, Name(name="Shield"))
        self.world.add_component(shield, Item())
        self.world.add_component(shield, Equipment(
            slot="armor",
            defense_bonus=1
        ))
        
        return shield 
    
    def create_fireball_scroll(self, x: int, y: int) -> int:
        """ファイアーボールの巻物を作成"""
        scroll = self.world.create_entity()
        
        self.world.add_component(scroll, Position(x=x, y=y))
        self.world.add_component(scroll, Renderable(
            char="?",
            fg_color=(200, 0, 0),
            bg_color=(0, 0, 0)
        ))
        self.world.add_component(scroll, Name(name="Fireball Scroll"))
        self.world.add_component(scroll, Item(
            use_function=cast_fireball,
            targeting=True,
            targeting_message="Left-click a target tile to cast fireball",
            damage=12,
            radius=3
        ))
        
        return scroll
    
    def create_confusion_scroll(self, x: int, y: int) -> int:
        """混乱の巻物を作成"""
        scroll = self.world.create_entity()
        
        self.world.add_component(scroll, Position(x=x, y=y))
        self.world.add_component(scroll, Renderable(
            char="?",
            fg_color=(200, 200, 0),
            bg_color=(0, 0, 0)
        ))
        self.world.add_component(scroll, Name(name="Confusion Scroll"))
        self.world.add_component(scroll, Item(
            use_function=cast_confusion,
            targeting=True,
            targeting_message="Left-click an enemy to confuse it",
            turns=10
        ))
        
        return scroll
    
    def create_paralyze_scroll(self, x: int, y: int) -> int:
        """麻痺の巻物を作成"""
        scroll = self.world.create_entity()
        
        self.world.add_component(scroll, Position(x=x, y=y))
        self.world.add_component(scroll, Renderable(
            char="?",
            fg_color=(0, 200, 200),
            bg_color=(0, 0, 0)
        ))
        self.world.add_component(scroll, Name(name="Paralysis Scroll"))
        self.world.add_component(scroll, Item(
            use_function=cast_paralyze,
            targeting=True,
            targeting_message="Left-click an enemy to paralyze it",
            turns=5
        ))
        
        return scroll
    
    def create_berserk_potion(self, x: int, y: int) -> int:
        """狂戦士化のポーションを作成"""
        potion = self.world.create_entity()
        
        self.world.add_component(potion, Position(x=x, y=y))
        self.world.add_component(potion, Renderable(
            char="!",
            fg_color=(200, 0, 200),
            bg_color=(0, 0, 0)
        ))
        self.world.add_component(potion, Name(name="Berserk Potion"))
        self.world.add_component(potion, Item(
            use_function=cast_berserk,
            targeting=False,
            power_bonus=5,
            turns=20
        ))
        
        return potion 