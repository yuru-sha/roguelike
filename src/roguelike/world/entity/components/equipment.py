from enum import Enum, auto
from typing import Optional, Dict, Any
from dataclasses import dataclass

class EquipmentSlot(Enum):
    """Equipment slot types."""
    # 防具スロット
    HEAD = auto()        # 頭部防具
    BODY = auto()        # 胴体防具
    ARMS = auto()        # 腕部防具
    LEGS = auto()        # 脚部防具
    FEET = auto()        # 足部防具
    CLOAK = auto()       # マント
    
    # 武器スロット
    MAIN_HAND = auto()   # 主手（武器）
    OFF_HAND = auto()    # 副手（盾など）
    
    # アクセサリースロット
    NECK = auto()        # 首飾り
    RING_LEFT = auto()   # 左手の指輪
    RING_RIGHT = auto()  # 右手の指輪
    
    # 特殊スロット
    AMULET = auto()      # イェンダーの魔除け（特殊アイテム）

class WeaponType(Enum):
    """Weapon types."""
    ONE_HANDED = auto()  # 片手武器
    TWO_HANDED = auto()  # 両手武器
    BOW = auto()         # 弓

@dataclass
class Equipment:
    """Component for items that can be equipped."""
    slot: EquipmentSlot
    defense_bonus: int = 0
    power_bonus: int = 0
    max_hp_bonus: int = 0
    weapon_type: Optional[WeaponType] = None  # 武器の場合のみ設定

@dataclass
class EquipmentSlots:
    """Component for entities that can equip items."""
    slots: Dict[EquipmentSlot, Optional[int]] = None  # slot -> equipped entity id
    
    def __post_init__(self):
        if self.slots is None:
            self.slots = {slot: None for slot in EquipmentSlot}
    
    def equip(self, slot: EquipmentSlot, item_id: int, world: Any) -> Optional[int]:
        """
        Equip an item to a slot.
        
        Args:
            slot: The slot to equip to
            item_id: The entity ID of the item
            world: The ECS world
            
        Returns:
            The entity ID of any previously equipped item, or None
        """
        # 両手武器やボウの場合、OFF_HANDを自動的に外す
        if slot == EquipmentSlot.MAIN_HAND:
            equipment = world.component_for_entity(item_id, Equipment)
            if equipment.weapon_type in [WeaponType.TWO_HANDED, WeaponType.BOW]:
                self.unequip(EquipmentSlot.OFF_HAND)
        
        old_item = self.slots[slot]
        self.slots[slot] = item_id
        return old_item
    
    def unequip(self, slot: EquipmentSlot) -> Optional[int]:
        """
        Unequip an item from a slot.
        
        Args:
            slot: The slot to unequip from
            
        Returns:
            The entity ID of the unequipped item, or None
        """
        old_item = self.slots[slot]
        self.slots[slot] = None
        return old_item
    
    def get_equipped(self, slot: EquipmentSlot) -> Optional[int]:
        """
        Get the item equipped in a slot.
        
        Args:
            slot: The slot to check
            
        Returns:
            The entity ID of the equipped item, or None
        """
        return self.slots[slot]
    
    def is_slot_empty(self, slot: EquipmentSlot) -> bool:
        """
        Check if a slot is empty.
        
        Args:
            slot: The slot to check
            
        Returns:
            True if the slot is empty, False otherwise
        """
        return self.slots[slot] is None
    
    def can_equip_to_slot(self, slot: EquipmentSlot, item_id: int, world: Any) -> bool:
        """
        Check if an item can be equipped to a slot.
        
        Args:
            slot: The slot to check
            item_id: The entity ID of the item
            world: The ECS world
            
        Returns:
            True if the item can be equipped, False otherwise
        """
        if slot == EquipmentSlot.OFF_HAND:
            # 両手武器やボウが装備されている場合、OFF_HANDには装備不可
            main_hand_id = self.get_equipped(EquipmentSlot.MAIN_HAND)
            if main_hand_id is not None:
                main_hand = world.component_for_entity(main_hand_id, Equipment)
                if main_hand.weapon_type in [WeaponType.TWO_HANDED, WeaponType.BOW]:
                    return False
        
        return True 