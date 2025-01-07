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
    Stackable,
)
from roguelike.world.entity.item_functions import (
    heal,
    cast_lightning,
    cast_fireball,
    cast_confusion,
    cast_paralyze,
    cast_berserk,
)
from roguelike.world.entity.inventory import InventorySystem

class EntityFactory:
    """エンティティの生成を管理するファクトリクラス"""
    
    def __init__(self, world: Any, engine=None):
        self.world = world
        self.engine = engine
    
    def create_player(self, x: int, y: int) -> int:
        """プレイヤーエンティティを作成"""
        player = self.world.create_entity(
            Position(x=x, y=y),
            Renderable(
                char="@",
                fg_color=(255, 255, 255),
                bg_color=(0, 0, 0)
            ),
            Fighter(
                max_hp=12,  # Rogueの初期HP
                hp=12,
                defense=2,
                power=5
            ),
            Inventory(capacity=26),  # a-zの26文字分
            Name(name="Player")
        )
        
        # 初期装備の作成と装備
        dagger = self.create_dagger(x, y)
        leather_armor = self.create_leather_armor(x, y)
        bow = self.create_bow(x, y)
        arrows = self.create_arrows(x, y, count=25)  # 25-30本
        food = self.create_food(x, y, count=3)  # 3-6個
        
        # インベントリに追加
        inventory_system = InventorySystem(self.world, self.engine)
        inventory_system.add_item(player, dagger)
        inventory_system.add_item(player, leather_armor)
        inventory_system.add_item(player, bow)
        inventory_system.add_item(player, arrows)
        inventory_system.add_item(player, food)
        
        # 装備を装着
        inventory_system.toggle_equipment(player, dagger)
        inventory_system.toggle_equipment(player, leather_armor)
        
        return player
    
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
    
    def create_healing_potion(self, x: int, y: int, count: int = 1) -> int:
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
            stackable=True,
            amount=4,
            weight=0.2,
            value=20,
            description="A magical potion that restores 4 HP when consumed.",
            identified=False  # 未識別状態で開始
        ))
        self.world.add_component(potion, Stackable(count=count))
        
        return potion
    
    def create_lightning_scroll(self, x: int, y: int, count: int = 1) -> int:
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
            stackable=True,
            targeting_message="Left-click an enemy to strike it with lightning",
            damage=20
        ))
        self.world.add_component(scroll, Stackable(count=count))
        
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
            slot="shield",
            defense_bonus=1
        ))
        
        return shield 
    
    def create_fireball_scroll(self, x: int, y: int, count: int = 1) -> int:
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
            stackable=True,
            targeting_message="Left-click a target tile to cast fireball",
            damage=12,
            radius=3
        ))
        self.world.add_component(scroll, Stackable(count=count))
        
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
    
    def create_dagger(self, x: int, y: int) -> int:
        """短剣を作成（+1, +1）"""
        dagger = self.world.create_entity()
        
        self.world.add_component(dagger, Position(x=x, y=y))
        self.world.add_component(dagger, Renderable(
            char=")",
            fg_color=(170, 170, 170),
            bg_color=(0, 0, 0)
        ))
        self.world.add_component(dagger, Name(name="Dagger"))
        self.world.add_component(dagger, Item(
            weight=0.5,
            value=10,
            description="A small but sharp dagger. Easy to handle and quick to strike."
        ))
        self.world.add_component(dagger, Equipment(
            slot="weapon",
            power_bonus=1,
            defense_bonus=1
        ))
        
        return dagger
        
    def create_leather_armor(self, x: int, y: int) -> int:
        """革鎧を作成（+1, +1）"""
        armor = self.world.create_entity()
        
        self.world.add_component(armor, Position(x=x, y=y))
        self.world.add_component(armor, Renderable(
            char="[",
            fg_color=(139, 69, 19),
            bg_color=(0, 0, 0)
        ))
        self.world.add_component(armor, Name(name="Leather Armor"))
        self.world.add_component(armor, Item(
            weight=3.0,
            value=25,
            description="Light armor made of hardened leather. Offers basic protection without hindering movement."
        ))
        self.world.add_component(armor, Equipment(
            slot="armor",
            power_bonus=1,
            defense_bonus=1
        ))
        
        return armor
        
    def create_bow(self, x: int, y: int) -> int:
        """弓を作成"""
        bow = self.world.create_entity()
        
        self.world.add_component(bow, Position(x=x, y=y))
        self.world.add_component(bow, Renderable(
            char=")",
            fg_color=(139, 69, 19),
            bg_color=(0, 0, 0)
        ))
        self.world.add_component(bow, Name(name="Bow"))
        self.world.add_component(bow, Item(
            weight=1.0,
            value=30,
            description="A wooden shortbow. Effective for ranged combat when used with arrows."
        ))
        self.world.add_component(bow, Equipment(
            slot="ranged",
            power_bonus=1
        ))
        
        return bow
        
    def create_arrows(self, x: int, y: int, count: int = 25) -> int:
        """矢を作成"""
        arrows = self.world.create_entity()
        
        self.world.add_component(arrows, Position(x=x, y=y))
        self.world.add_component(arrows, Renderable(
            char="/",
            fg_color=(170, 170, 170),
            bg_color=(0, 0, 0)
        ))
        self.world.add_component(arrows, Name(name="Arrows"))
        self.world.add_component(arrows, Item(
            stackable=True,
            weight=0.1,
            value=1,
            description="Sharp arrows for use with a bow. Each arrow is carefully fletched for accuracy."
        ))
        self.world.add_component(arrows, Stackable(count=count))
        self.world.add_component(arrows, Equipment(
            slot="ammo",
            power_bonus=1
        ))
        
        return arrows
        
    def create_food(self, x: int, y: int, count: int = 1) -> int:
        """食料を作成"""
        food = self.world.create_entity()
        
        self.world.add_component(food, Position(x=x, y=y))
        self.world.add_component(food, Renderable(
            char="%",
            fg_color=(139, 69, 19),
            bg_color=(0, 0, 0)
        ))
        self.world.add_component(food, Name(name="Food Ration"))
        self.world.add_component(food, Item(
            use_function=lambda world, entity, **kwargs: True,  # 仮の実装
            stackable=True,
            weight=0.5,
            value=5,
            description="A preserved food ration. Not particularly tasty, but will keep you going."
        ))
        self.world.add_component(food, Stackable(count=count))
        
        return food 