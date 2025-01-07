from typing import Optional, List
import esper

from roguelike.world.entity.components import Item, Inventory, Equipment, Equippable, Fighter, Position, Stackable, Name
from roguelike.utils.logger import logger

class InventorySystem:
    """インベントリ管理システム"""
    
    def __init__(self, world: esper.World, engine=None):
        self.world = world
        self.engine = engine
    
    def add_item(self, owner: int, item: int) -> bool:
        """アイテムを拾う"""
        if not self.world.has_component(owner, Inventory):
            logger.warning(f"Entity {owner} has no inventory component")
            return False
            
        inventory = self.world.component_for_entity(owner, Inventory)
        name = self.world.component_for_entity(item, Name).name
        
        # 重ね置き可能なアイテムの場合
        if self.world.has_component(item, Item) and self.world.component_for_entity(item, Item).stackable:
            # 同じ種類のアイテムを探す
            for inv_item in inventory.items:
                if (self.world.has_component(inv_item, Item) and 
                    self.world.component_for_entity(inv_item, Item).stackable and
                    self.world.component_for_entity(inv_item, Name).name == name):
                    # 個数を加算
                    item_stack = self.world.component_for_entity(item, Stackable)
                    inv_stack = self.world.component_for_entity(inv_item, Stackable)
                    
                    # 最大数を超えない範囲で加算
                    transfer_count = min(
                        item_stack.count,
                        inv_stack.max_count - inv_stack.count
                    )
                    
                    if transfer_count > 0:
                        inv_stack.count += transfer_count
                        item_stack.count -= transfer_count
                        
                        # アイテムがすべて移動した場合
                        if item_stack.count == 0:
                            if self.world.has_component(item, Position):
                                self.world.remove_component(item, Position)
                            self.world.delete_entity(item)
                            logger.info(f"You pick up {transfer_count} {name}s.")
                            return True
                        # 一部のみ移動した場合
                        else:
                            logger.info(f"You pick up {transfer_count} {name}s.")
                            return True
        
        # 新しいスロットが必要な場合
        if len(inventory.items) >= inventory.capacity:
            logger.info("Your pack is full (26 items max).")
            return False
            
        inventory.items.append(item)
        # アイテムをマップから削除（Positionコンポーネントを削除）
        if self.world.has_component(item, Position):
            self.world.remove_component(item, Position)
        logger.info(f"You pick up {name}.")
        return True
    
    def remove_item(self, owner: int, item: int, count: int = None) -> bool:
        """アイテムを捨てる"""
        if not self.world.has_component(owner, Inventory):
            return False
            
        inventory = self.world.component_for_entity(owner, Inventory)
        name = self.world.component_for_entity(item, Name).name
        
        if item not in inventory.items:
            return False
        
        # 重ね置きアイテムの場合
        if (count is not None and 
            self.world.has_component(item, Item) and 
            self.world.component_for_entity(item, Item).stackable):
            stack = self.world.component_for_entity(item, Stackable)
            
            # 指定個数以上ある場合は分割
            if stack.count > count:
                stack.count -= count
                # 新しいアイテムを作成
                new_item = self.world.create_entity()
                # 元のアイテムのコンポーネントをコピー
                for component_type in self.world.components_for_entity(item):
                    if isinstance(component_type, Stackable):
                        self.world.add_component(new_item, Stackable(count=count))
                    else:
                        self.world.add_component(new_item, component_type)
                return new_item
            
            # スタックをすべて捨てる場合
            inventory.items.remove(item)
            return True
        
        # 通常のアイテム
        inventory.items.remove(item)
        return True
    
    def use_item(self, owner: int, item: int, target: Optional[int] = None) -> bool:
        """アイテムを使用する"""
        if not self.world.has_component(item, Item):
            return False
            
        item_component = self.world.component_for_entity(item, Item)
        name = self.world.component_for_entity(item, Name).name
        
        if item_component.use_function is None:
            # 装備品の場合は装備を試みる
            if self.world.has_component(item, Equipment):
                equipment = self.world.component_for_entity(item, Equipment)
                if equipment.is_equipped:
                    logger.info(f"You were wearing {name}.")
                else:
                    logger.info(f"You are wearing {name}.")
                return self.toggle_equipment(owner, item)
            logger.info(f"You can't use the {name}.")
            return False
            
        if item_component.targeting and target is None:
            logger.info("No target selected")
            return False
            
        # アイテムの効果を適用
        kwargs = {**item_component.function_kwargs}
        if target is not None:
            kwargs["target"] = target
            
        if item_component.use_function(self.world, owner, **kwargs):
            # 使用メッセージ
            if "amount" in item_component.function_kwargs:
                logger.info(f"You feel better.")  # 回復アイテム
            elif "damage" in item_component.function_kwargs:
                logger.info(f"Zap!")  # 攻撃アイテム
            elif "turns" in item_component.function_kwargs:
                if "confusion" in item_component.use_function.__name__:
                    logger.info(f"Your hands begin to glow red.")
                elif "paralyze" in item_component.use_function.__name__:
                    logger.info(f"Your hands begin to glow blue.")
            
            # 重ね置きアイテムの場合は個数を減らす
            if item_component.stackable:
                stack = self.world.component_for_entity(item, Stackable)
                stack.count -= 1
                # 個数が0になった場合のみアイテムを削除
                if stack.count <= 0:
                    self.remove_item(owner, item)
                    self.world.delete_entity(item)
            else:
                # 通常のアイテムは使用後に削除
                self.remove_item(owner, item)
                self.world.delete_entity(item)
            
            return True
        
        return False
    
    def toggle_equipment(self, owner: int, item: int) -> bool:
        """装備の着脱を行う"""
        if not self.world.has_component(item, Equipment):
            return False
            
        equipment = self.world.component_for_entity(item, Equipment)
        
        if equipment.is_equipped:
            # 装備解除
            self._unequip_item(owner, item)
        else:
            # 既存の装備を解除
            for ent, (inv_equipment,) in self.world.get_components(Equipment):
                if (ent in self.world.component_for_entity(owner, Inventory).items and 
                    inv_equipment.slot == equipment.slot and 
                    inv_equipment.is_equipped):
                    self._unequip_item(owner, ent)
            
            # 新しい装備を装着
            self._equip_item(owner, item)
            
        return True
    
    def _equip_item(self, owner: int, item: int) -> None:
        """アイテムを装備する"""
        equipment = self.world.component_for_entity(item, Equipment)
        fighter = self.world.component_for_entity(owner, Fighter)
        name = self.world.component_for_entity(item, Name).name
        
        equipment.is_equipped = True
        fighter.power += equipment.power_bonus
        fighter.defense += equipment.defense_bonus
        
        if equipment.slot == "weapon":
            self.engine.add_message(f"You are wielding {name}.")
        elif equipment.slot == "armor":
            self.engine.add_message(f"You are wearing {name}.")
        elif equipment.slot == "shield":
            self.engine.add_message(f"You are holding {name}.")
        elif equipment.slot == "ranged":
            self.engine.add_message(f"You are wielding {name}.")
        elif equipment.slot == "ammo":
            self.engine.add_message(f"You are quivering {name}.")
    
    def _unequip_item(self, owner: int, item: int) -> None:
        """装備を外す"""
        equipment = self.world.component_for_entity(item, Equipment)
        fighter = self.world.component_for_entity(owner, Fighter)
        name = self.world.component_for_entity(item, Name).name
        
        equipment.is_equipped = False
        fighter.power -= equipment.power_bonus
        fighter.defense -= equipment.defense_bonus
        
        if equipment.slot == "weapon":
            self.engine.add_message(f"You were wielding {name}.")
        elif equipment.slot == "armor":
            self.engine.add_message(f"You were wearing {name}.")
        elif equipment.slot == "shield":
            self.engine.add_message(f"You were holding {name}.")
        elif equipment.slot == "ranged":
            self.engine.add_message(f"You were wielding {name}.")
        elif equipment.slot == "ammo":
            self.engine.add_message(f"You were quivering {name}.")
    
    def split_item(self, owner: int, item: int, count: int) -> Optional[int]:
        """アイテムを指定した数量だけ分割する"""
        if not self.world.has_component(owner, Inventory):
            logger.warning(f"Entity {owner} has no inventory component")
            return None
            
        inventory = self.world.component_for_entity(owner, Inventory)
        
        if item not in inventory.items:
            logger.warning(f"Item {item} not in inventory of entity {owner}")
            return None
            
        if not (self.world.has_component(item, Item) and 
                self.world.component_for_entity(item, Item).stackable):
            logger.warning(f"Item {item} is not stackable")
            return None
            
        stack = self.world.component_for_entity(item, Stackable)
        
        if count >= stack.count:
            logger.warning(f"Cannot split more items than available")
            return None
            
        # 新しいアイテムエンティティを作成
        new_item = self.world.create_entity()
        
        # 元のアイテムのコンポーネントをコピー
        for component_type in self.world.components_for_entity(item):
            if isinstance(component_type, Stackable):
                # スタック数を調整
                self.world.add_component(new_item, Stackable(count=count))
                stack.count -= count
            else:
                # その他のコンポーネントはそのままコピー
                self.world.add_component(new_item, component_type)
                
        # 新しいアイテムをインベントリに追加
        inventory.items.append(new_item)
        
        logger.info(f"Split {count} items from {item} to new item {new_item}")
        return new_item 