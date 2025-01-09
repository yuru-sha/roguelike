from enum import Enum, auto
from typing import Optional, Dict, Any
from dataclasses import dataclass
from roguelike.world.entity.components.serializable import SerializableComponent
from roguelike.core.constants import EquipmentSlot, WeaponType

@dataclass
class Equipment(SerializableComponent):
    """Component for items that can be equipped."""
    slot: EquipmentSlot  # 後方互換性のために残す
    defense_bonus: int = 0
    power_bonus: int = 0
    max_hp_bonus: int = 0
    weapon_type: Optional[WeaponType] = None  # 武器の場合のみ設定

    def __init__(self, slot=None, equipment_slot=None, **kwargs):
        """Initialize Equipment component with either slot or equipment_slot."""
        if equipment_slot is not None:
            self.slot = equipment_slot
        elif slot is not None:
            self.slot = slot
        else:
            raise ValueError("Either slot or equipment_slot must be provided")
        
        self.defense_bonus = kwargs.get('defense_bonus', 0)
        self.power_bonus = kwargs.get('power_bonus', 0)
        self.max_hp_bonus = kwargs.get('max_hp_bonus', 0)
        self.weapon_type = kwargs.get('weapon_type', None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            '__type__': self.__class__.__name__,
            '__module__': self.__class__.__module__,
            'data': {
                'slot': str(self.slot.value),  # 値を文字列として保存
                'defense_bonus': self.defense_bonus,
                'power_bonus': self.power_bonus,
                'max_hp_bonus': self.max_hp_bonus,
                'weapon_type': self.weapon_type.name if self.weapon_type else None
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any] | 'Equipment') -> 'Equipment':
        """Create from dictionary after deserialization."""
        # Equipmentオブジェクトが直接渡された場合
        if isinstance(data, Equipment):
            return cls(
                slot=data.slot,
                defense_bonus=data.defense_bonus,
                power_bonus=data.power_bonus,
                max_hp_bonus=data.max_hp_bonus,
                weapon_type=data.weapon_type
            )
            
        # 辞書形式の場合
        if not isinstance(data, dict):
            raise ValueError(f"Invalid data format for Equipment: {data}")
            
        component_data = data.get('data', data)
        if not isinstance(component_data, dict):
            raise ValueError(f"Invalid component data format: {component_data}")
            
        # slotの復元
        try:
            slot = EquipmentSlot.from_value(int(component_data['slot']))  # 値から復元
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid equipment slot value: {component_data['slot']}")
            
        # weapon_typeの復元
        weapon_type = None
        if component_data.get('weapon_type'):
            try:
                weapon_type = WeaponType[component_data['weapon_type']]
            except KeyError:
                raise ValueError(f"Invalid weapon type name: {component_data['weapon_type']}")
                
        # インスタンスを作成
        instance = cls(
            slot=slot,
            defense_bonus=int(component_data.get('defense_bonus', 0)),
            power_bonus=int(component_data.get('power_bonus', 0)),
            max_hp_bonus=int(component_data.get('max_hp_bonus', 0)),
            weapon_type=weapon_type
        )
        return instance

@dataclass
class EquipmentSlots(SerializableComponent):
    """Component for entities that can equip items."""
    slots: Dict[EquipmentSlot, Optional[int]] = None  # slot -> equipped entity id
    
    def __post_init__(self):
        """Initialize items list."""
        # slotsが未設定の場合のみ初期化
        if self.slots is None:
            self.slots = {slot: None for slot in EquipmentSlot}
    
    def _check_weapon_compatibility(self, slot: EquipmentSlot, item: int, world: Any) -> bool:
        """
        Check if a weapon is compatible with current equipment.
        
        Args:
            slot: Equipment slot to check
            item: Item entity ID
            world: The ECS world
            
        Returns:
            True if weapon is compatible, False otherwise
        """
        if not world.has_component(item, Equipment):
            return False
            
        equipment = world.component_for_entity(item, Equipment)
        
        # 武器でない場合は互換性チェックをスキップ
        if equipment.weapon_type is None:
            return True
            
        # 両手武器の場合
        if equipment.weapon_type == WeaponType.TWO_HANDED:
            # メインハンドとオフハンドの両方が空いている必要がある
            # ただし、現在装備しようとしているスロットは除外
            main_hand = self.get_equipped(EquipmentSlot.MAIN_HAND)
            off_hand = self.get_equipped(EquipmentSlot.OFF_HAND)
            
            if slot == EquipmentSlot.MAIN_HAND:
                return off_hand is None
            elif slot == EquipmentSlot.OFF_HAND:
                return main_hand is None
            else:
                return main_hand is None and off_hand is None
                
        # 片手武器の場合
        elif equipment.weapon_type == WeaponType.ONE_HANDED:
            # 対応するスロットに両手武器が装備されていないことを確認
            other_slot = EquipmentSlot.OFF_HAND if slot == EquipmentSlot.MAIN_HAND else EquipmentSlot.MAIN_HAND
            other_item = self.get_equipped(other_slot)
            
            if other_item is not None and world.has_component(other_item, Equipment):
                other_equipment = world.component_for_entity(other_item, Equipment)
                return other_equipment.weapon_type != WeaponType.TWO_HANDED
            return True
            
        # 弓の場合
        elif equipment.weapon_type == WeaponType.BOW:
            # 弓は両手武器として扱う
            main_hand = self.get_equipped(EquipmentSlot.MAIN_HAND)
            off_hand = self.get_equipped(EquipmentSlot.OFF_HAND)
            
            if slot == EquipmentSlot.MAIN_HAND:
                return off_hand is None
            elif slot == EquipmentSlot.OFF_HAND:
                return main_hand is None
            else:
                return main_hand is None and off_hand is None
                
        return True
    
    def equip(self, slot: EquipmentSlot, item: int, world: Any) -> bool:
        """
        Equip an item to a slot.
        
        Args:
            slot: Equipment slot to equip to
            item: Item entity ID
            world: The ECS world
            
        Returns:
            True if item was equipped
        """
        # Check if item has Equipment component
        if not world.has_component(item, Equipment):
            return False
        
        equipment = world.component_for_entity(item, Equipment)
        
        # Check if item is compatible with slot
        if equipment.slot != slot:
            return False
        
        # Check weapon compatibility
        if not self._check_weapon_compatibility(slot, item, world):
            return False
        
        # 両手武器やボウを装備する場合、両手を空ける
        if equipment.weapon_type in [WeaponType.TWO_HANDED, WeaponType.BOW]:
            self.unequip(EquipmentSlot.MAIN_HAND)
            self.unequip(EquipmentSlot.OFF_HAND)
        
        # Unequip current item in slot if any
        current = self.get_equipped(slot)
        if current is not None:
            self.unequip(slot)
        
        # Equip new item
        self.slots[slot] = item
        return True
    
    def can_equip_to_slot(self, slot: EquipmentSlot, item: int, world: Any) -> bool:
        """
        Check if an item can be equipped to a slot.
        
        Args:
            slot: The slot to check
            item: Item entity ID
            world: The ECS world
            
        Returns:
            True if the item can be equipped, False otherwise
        """
        # 基本的な装備可能性チェック
        if not world.has_component(item, Equipment):
            return False
            
        equipment = world.component_for_entity(item, Equipment)
        
        # スロットの互換性チェック
        if equipment.slot != slot:
            return False
            
        # 武器の互換性チェック
        return self._check_weapon_compatibility(slot, item, world)
    
    def __getitem__(self, slot: EquipmentSlot) -> Optional[int]:
        """Get equipped entity id for slot."""
        return self.slots[slot]
    
    def __setitem__(self, slot: EquipmentSlot, entity_id: Optional[int]):
        """Set equipped entity id for slot."""
        self.slots[slot] = entity_id
        
    def __iter__(self):
        """Iterate over slots."""
        return iter(self.slots)
        
    def items(self):
        """Return items view of slots dictionary."""
        return self.slots.items()
    
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
    
    def is_empty(self, slot: EquipmentSlot) -> bool:
        """Check if slot is empty."""
        return self.slots[slot] is None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            '__type__': self.__class__.__name__,
            '__module__': self.__class__.__module__,
            'data': {
                'slots': {slot.name: entity_id for slot, entity_id in self.slots.items()}
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any] | 'EquipmentSlots') -> 'EquipmentSlots':
        """Create from dictionary after deserialization."""
        # EquipmentSlotsオブジェクトが直接渡された場合
        if isinstance(data, EquipmentSlots):
            instance = cls()
            instance.slots = data.slots.copy()  # スロットの状態をコピー
            return instance
            
        # 辞書形式の場合
        if not isinstance(data, dict):
            raise ValueError(f"Invalid data format for EquipmentSlots: {data}")
            
        component_data = data.get('data', data)
        if not isinstance(component_data, dict):
            raise ValueError(f"Invalid component data format: {component_data}")
            
        slots_data = component_data.get('slots', {})
        instance = cls()  # 全スロットをNoneで初期化
        
        # 全てのスロットを初期化
        instance.slots = {slot: None for slot in EquipmentSlot}
        
        # 保存されているスロットを復元
        for slot_name, entity_id in slots_data.items():
            try:
                # スロット名からEnumを取得
                slot = EquipmentSlot[slot_name]
                # entity_idがNoneまたは整数であることを確認
                if entity_id is not None and not isinstance(entity_id, int):
                    raise ValueError(f"Invalid entity ID for slot {slot_name}: {entity_id}")
                instance.slots[slot] = entity_id
            except KeyError:
                # エラーメッセージを詳細にする
                raise ValueError(f"Invalid equipment slot name: {slot_name}")
                
        return instance 