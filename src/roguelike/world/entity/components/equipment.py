"""
Equipment components for the game.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, Optional, Tuple
import random

from roguelike.core.constants import EquipmentSlot, WeaponType
from roguelike.world.entity.components.serializable import SerializableComponent
from roguelike.world.entity.components.identification import Identifiable, ItemType


@dataclass
class Equipment(SerializableComponent):
    """Component for items that can be equipped."""

    slot: EquipmentSlot
    defense_bonus: int = 0
    power_bonus: int = 0
    max_hp_bonus: int = 0
    weapon_type: Optional[WeaponType] = None
    cursed: bool = False  # 呪われた装備品は外せない
    enchantment: int = 0  # 武器の場合は攻撃力、防具の場合は防御力の修正値
    hits_to_identify: int = 10  # 武器を識別するために必要な命中回数
    tried: bool = False  # 装備を試したかどうか（Rogueの仕様）
    hit_count: int = 0  # 命中回数のカウント（武器用）
    damage_dice: Tuple[int, int] = (1, 4)  # (dice_count, dice_sides)
    hit_bonus: int = 0  # 命中修正値
    hits_taken: int = 0  # 被弾回数のカウント（防具用）

    def __init__(self, slot=None, equipment_slot=None, **kwargs):
        """Initialize Equipment component with either slot or equipment_slot."""
        if equipment_slot is not None:
            self.slot = equipment_slot
        elif slot is not None:
            self.slot = slot
        else:
            raise ValueError("Either slot or equipment_slot must be provided")

        self.defense_bonus = kwargs.get("defense_bonus", 0)
        self.power_bonus = kwargs.get("power_bonus", 0)
        self.max_hp_bonus = kwargs.get("max_hp_bonus", 0)
        self.weapon_type = kwargs.get("weapon_type", None)
        self.cursed = kwargs.get("cursed", False)
        self.enchantment = kwargs.get("enchantment", 0)
        self.hits_to_identify = kwargs.get("hits_to_identify", 10)
        self.tried = kwargs.get("tried", False)
        self.hit_count = kwargs.get("hit_count", 0)
        self.damage_dice = kwargs.get("damage_dice", (1, 4))
        self.hit_bonus = kwargs.get("hit_bonus", 0)
        self.hits_taken = kwargs.get("hits_taken", 0)

    def on_equip(self, item_id: int, world: Any) -> None:
        """Called when the item is equipped."""
        # 装備時には識別されないが、試したことになる（Rogueの仕様）
        self.tried = True
        if world.has_component(item_id, Identifiable):
            identifiable = world.component_for_entity(item_id, Identifiable)
            identifiable.try_item()

    def on_hit(self, item_id: int, world: Any) -> None:
        """Called when a weapon hits an enemy."""
        if not self.weapon_type:
            return

        if world.has_component(item_id, Identifiable):
            identifiable = world.component_for_entity(item_id, Identifiable)
            if not identifiable.is_identified:
                self.hit_count += 1
                # Rogueの仕様：8-12回の命中で識別
                if self.hit_count >= self.hits_to_identify:
                    identifiable.identify()

    def on_take_damage(self, item_id: int, world: Any) -> None:
        """Called when the wearer takes damage."""
        if self.weapon_type:
            return

        if world.has_component(item_id, Identifiable):
            identifiable = world.component_for_entity(item_id, Identifiable)
            if not identifiable.is_identified:
                self.hits_taken += 1
                # Rogueの仕様：防具は被弾時に20%の確率で識別
                if random.random() < 0.20:
                    identifiable.identify()

    def can_unequip(self) -> bool:
        """Check if the item can be unequipped."""
        return not self.cursed

    def get_total_bonus(self) -> Tuple[int, int, int]:
        """Get total bonuses (power, defense, max_hp) including enchantment."""
        power = self.power_bonus + (self.enchantment if self.weapon_type else 0)
        defense = self.defense_bonus + (self.enchantment if not self.weapon_type else 0)
        return power, defense, self.max_hp_bonus

    def roll_damage(self) -> int:
        """Roll damage for this weapon."""
        if not self.weapon_type:
            return 0
        dice_count, dice_sides = self.damage_dice
        base_damage = sum(random.randint(1, dice_sides) for _ in range(dice_count))
        return base_damage + self.enchantment  # エンチャント値を加算

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "__type__": self.__class__.__name__,
            "__module__": self.__class__.__module__,
            "data": {
                "slot": str(self.slot.value),
                "defense_bonus": self.defense_bonus,
                "power_bonus": self.power_bonus,
                "max_hp_bonus": self.max_hp_bonus,
                "weapon_type": self.weapon_type.name if self.weapon_type else None,
                "cursed": self.cursed,
                "enchantment": self.enchantment,
                "hits_to_identify": self.hits_to_identify,
                "tried": self.tried,
                "hit_count": self.hit_count,
                "damage_dice": self.damage_dice,
                "hit_bonus": self.hit_bonus,
                "hits_taken": self.hits_taken,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any] | "Equipment") -> "Equipment":
        """Create from dictionary after deserialization."""
        if isinstance(data, Equipment):
            return cls(
                slot=data.slot,
                defense_bonus=data.defense_bonus,
                power_bonus=data.power_bonus,
                max_hp_bonus=data.max_hp_bonus,
                weapon_type=data.weapon_type,
                cursed=data.cursed,
                enchantment=data.enchantment,
                hits_to_identify=data.hits_to_identify,
                tried=data.tried,
                hit_count=data.hit_count,
                damage_dice=data.damage_dice,
                hit_bonus=data.hit_bonus,
                hits_taken=data.hits_taken,
            )

        component_data = data.get("data", data)

        # Handle slot
        slot_value = component_data.get("slot")
        if isinstance(slot_value, str):
            try:
                slot = EquipmentSlot(slot_value)
            except ValueError:
                slot = EquipmentSlot.MAIN_HAND  # Default to main hand if invalid
        else:
            slot = EquipmentSlot.MAIN_HAND

        # Handle weapon type
        weapon_type_name = component_data.get("weapon_type")
        weapon_type = None
        if weapon_type_name:
            try:
                weapon_type = WeaponType[weapon_type_name]
            except KeyError:
                pass

        # Handle damage dice
        damage_dice = component_data.get("damage_dice", (1, 4))
        if not isinstance(damage_dice, tuple) or len(damage_dice) != 2:
            damage_dice = (1, 4)  # Default to 1d4

        return cls(
            slot=slot,
            defense_bonus=int(component_data.get("defense_bonus", 0)),
            power_bonus=int(component_data.get("power_bonus", 0)),
            max_hp_bonus=int(component_data.get("max_hp_bonus", 0)),
            weapon_type=weapon_type,
            cursed=bool(component_data.get("cursed", False)),
            enchantment=int(component_data.get("enchantment", 0)),
            hits_to_identify=int(component_data.get("hits_to_identify", 10)),
            tried=bool(component_data.get("tried", False)),
            hit_count=int(component_data.get("hit_count", 0)),
            damage_dice=damage_dice,
            hit_bonus=int(component_data.get("hit_bonus", 0)),
            hits_taken=int(component_data.get("hits_taken", 0)),
        )


@dataclass
class EquipmentSlots(SerializableComponent):
    """Component for entities that can equip items."""

    slots: Dict[EquipmentSlot, Optional[int]] = None  # slot -> equipped entity id

    def __post_init__(self):
        """Initialize slots dictionary."""
        if self.slots is None:
            self.slots = {slot: None for slot in EquipmentSlot}

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
            self.unequip(EquipmentSlot.MAIN_HAND, world)
            self.unequip(EquipmentSlot.OFF_HAND, world)

        # Unequip current item in slot if any
        current = self.get_equipped(slot)
        if current is not None:
            if not self.can_unequip(current, world):
                return False
            self.unequip(slot, world)

        # Equip new item
        self.slots[slot] = item
        equipment.on_equip(item, world)
        return True

    def unequip(self, slot: EquipmentSlot, world: Any) -> Optional[int]:
        """
        Unequip an item from a slot.

        Args:
            slot: The slot to unequip from
            world: The ECS world

        Returns:
            The entity ID of the unequipped item, or None
        """
        item = self.slots[slot]
        if item is None:
            return None

        if not self.can_unequip(item, world):
            return None

        self.slots[slot] = None
        return item

    def get_equipped(self, slot: EquipmentSlot) -> Optional[int]:
        """Get the item equipped in a slot."""
        return self.slots.get(slot)

    def can_unequip(self, item: int, world: Any) -> bool:
        """Check if an item can be unequipped."""
        if not world.has_component(item, Equipment):
            return True

        equipment = world.component_for_entity(item, Equipment)
        return not equipment.cursed

    def _check_weapon_compatibility(self, slot: EquipmentSlot, item: int, world: Any) -> bool:
        """Check if a weapon can be equipped to a slot."""
        if not world.has_component(item, Equipment):
            return False

        equipment = world.component_for_entity(item, Equipment)
        if not equipment.weapon_type:
            return True

        # 両手武器は両手が空いている必要がある
        if equipment.weapon_type in [WeaponType.TWO_HANDED, WeaponType.BOW]:
            main_hand = self.get_equipped(EquipmentSlot.MAIN_HAND)
            off_hand = self.get_equipped(EquipmentSlot.OFF_HAND)
            if main_hand is not None and not self.can_unequip(main_hand, world):
                return False
            if off_hand is not None and not self.can_unequip(off_hand, world):
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "__type__": self.__class__.__name__,
            "__module__": self.__class__.__module__,
            "data": {
                "slots": {str(k.value): v for k, v in self.slots.items()},
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any] | "EquipmentSlots") -> "EquipmentSlots":
        """Create from dictionary after deserialization."""
        if isinstance(data, EquipmentSlots):
            return cls(slots=data.slots)

        component_data = data.get("data", data)
        slots_data = component_data.get("slots", {})
        slots = {}
        for k, v in slots_data.items():
            try:
                slot = EquipmentSlot(k)
                slots[slot] = v
            except ValueError:
                continue

        return cls(slots=slots)
