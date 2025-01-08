# TODO: Add more component types for advanced features
# TODO: Add component serialization for save/load
# FIXME: Equipment slots should handle two-handed weapons properly
# OPTIMIZE: Component access patterns could be improved
# WARNING: Some components might need better validation
# REVIEW: Consider if components should be more granular
# HACK: Some component fields could be more strongly typed

from dataclasses import dataclass, field
from enum import IntEnum, Enum, auto
from typing import Tuple, Optional, Dict, Any, Callable

from roguelike.world.entity.components.serializable import SerializableComponent

class RenderOrder(IntEnum):
    """Render order for entities."""
    CORPSE = 1
    ITEM = 2
    ACTOR = 3

class EquipmentSlot(Enum):
    HEAD = auto()
    NECK = auto()
    BODY = auto()
    CLOAK = auto()
    ARMS = auto()
    SHIELD = auto()
    RING_LEFT = auto()
    RING_RIGHT = auto()
    LEGS = auto()
    FEET = auto()
    MAIN_HAND = auto()
    OFF_HAND = auto()
    AMULET = auto()

class WeaponType(Enum):
    """Weapon type enum."""
    ONE_HANDED = auto()
    TWO_HANDED = auto()
    DUAL_WIELD = auto()
    BOW = auto()
    CROSSBOW = auto()
    THROWN = auto()

@dataclass
class Position(SerializableComponent):
    """Position component."""
    x: int
    y: int
    
    def distance_to(self, other: 'Position') -> int:
        """Calculate distance to another position."""
        return max(abs(self.x - other.x), abs(self.y - other.y))

@dataclass
class Renderable(SerializableComponent):
    """Renderable component."""
    char: str
    color: Tuple[int, int, int]
    render_order: RenderOrder
    name: str
    always_visible: bool = False

@dataclass
class Fighter(SerializableComponent):
    """Combat stats component."""
    max_hp: int
    hp: int
    defense: int
    power: int
    xp: int = 0
    
    def take_damage(self, amount: int) -> int:
        """
        Take damage and return XP if died.
        
        Args:
            amount: Amount of damage to take
            
        Returns:
            XP value if died, 0 otherwise
        """
        self.hp = max(0, self.hp - amount)
        if self.hp <= 0:
            return self.xp
        return 0
    
    def heal(self, amount: int) -> None:
        """
        Heal by the given amount.
        
        Args:
            amount: Amount to heal
        """
        self.hp = min(self.max_hp, self.hp + amount)

@dataclass
class AI(SerializableComponent):
    """AI behavior component."""
    behavior: str = "basic"
    turns_confused: int = 0

@dataclass
class Inventory(SerializableComponent):
    """Inventory component."""
    capacity: int
    items: list = None
    
    def __post_init__(self):
        """Initialize items list."""
        if self.items is None:
            self.items = []
    
    def add_item(self, item: int) -> bool:
        """
        Add an item to inventory.
        
        Args:
            item: Item entity ID
            
        Returns:
            True if item was added
        """
        if len(self.items) >= self.capacity:
            return False
        self.items.append(item)
        return True
    
    def remove_item(self, item: int) -> None:
        """
        Remove an item from inventory.
        
        Args:
            item: Item entity ID
        """
        self.items.remove(item)

@dataclass
class Item(SerializableComponent):
    """Item component."""
    name: str
    use_function: Optional[Callable] = None
    use_args: Optional[Dict[str, Any]] = None
    targeting: bool = False
    targeting_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Override to handle non-serializable use_function."""
        data = super().to_dict()
        if self.use_function is not None:
            data['data']['use_function'] = f"{self.use_function.__module__}.{self.use_function.__name__}"
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Item':
        """Override to handle non-serializable use_function."""
        use_function_path = data['data'].pop('use_function', None)
        instance = super().from_dict(data)
        
        if use_function_path:
            module_name, function_name = use_function_path.rsplit('.', 1)
            module = __import__(module_name, fromlist=[function_name])
            instance.use_function = getattr(module, function_name)
            
        return instance

@dataclass
class Level(SerializableComponent):
    """Level component."""
    current_level: int = 1
    current_xp: int = 0
    xp_to_next_level: int = 200
    
    def add_xp(self, xp: int) -> bool:
        """
        Add XP and check for level up.
        
        Args:
            xp: Amount of XP to add
            
        Returns:
            True if leveled up
        """
        self.current_xp += xp
        if self.current_xp >= self.xp_to_next_level:
            self.current_level += 1
            self.current_xp -= self.xp_to_next_level
            self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
            return True
        return False
    
    def requires_level_up(self) -> bool:
        """Check if ready to level up."""
        return self.current_xp >= self.xp_to_next_level

@dataclass
class EquipmentSlots(SerializableComponent):
    """Component for managing equipment slots."""
    slots: Dict[EquipmentSlot, Optional[int]] = field(default_factory=lambda: {slot: None for slot in EquipmentSlot})
    
    def equip(self, slot: EquipmentSlot, item: int, world: Any) -> Optional[str]:
        """
        Equip an item to a slot.
        
        Args:
            slot: The equipment slot
            item: The item entity ID
            world: The ECS world
            
        Returns:
            Error message if equip failed, None if successful
        """
        # 既に装備しているアイテムを外す
        if self.slots[slot] is not None:
            self.unequip(slot, world)
        
        # 二刀流のチェック
        if slot in [EquipmentSlot.MAIN_HAND, EquipmentSlot.OFF_HAND]:
            equipment = world.component_for_entity(item, Equipment)
            if equipment.weapon_type == WeaponType.TWO_HANDED:
                # 両手武器は片方のスロットしか使えない
                if slot == EquipmentSlot.OFF_HAND:
                    return "Two-handed weapons must be equipped in the main hand."
                # 両手武器を装備する場合、オフハンドを空ける
                if self.slots[EquipmentSlot.OFF_HAND] is not None:
                    self.unequip(EquipmentSlot.OFF_HAND, world)
            elif slot == EquipmentSlot.OFF_HAND:
                # オフハンドに武器を装備する場合、二刀流可能かチェック
                if not equipment.can_dual_wield():
                    return "This weapon cannot be dual wielded."
                # メインハンドの武器も二刀流可能かチェック
                main_hand = self.slots[EquipmentSlot.MAIN_HAND]
                if main_hand is not None:
                    main_equipment = world.component_for_entity(main_hand, Equipment)
                    if not main_equipment.can_dual_wield():
                        return "Cannot dual wield with current main hand weapon."
        
        self.slots[slot] = item
        return None
    
    def unequip(self, slot: EquipmentSlot, world: Any) -> None:
        """
        Unequip an item from a slot.
        
        Args:
            slot: The equipment slot
            world: The ECS world
        """
        # 両手武器を外す場合、オフハンドも空ける
        if slot == EquipmentSlot.MAIN_HAND and self.slots[slot] is not None:
            equipment = world.component_for_entity(self.slots[slot], Equipment)
            if equipment.weapon_type == WeaponType.TWO_HANDED:
                self.slots[EquipmentSlot.OFF_HAND] = None
        
        self.slots[slot] = None

@dataclass
class Equipment(SerializableComponent):
    """Equipment component."""
    equipment_slot: EquipmentSlot
    power_bonus: int = 0
    defense_bonus: int = 0
    weapon_type: Optional[WeaponType] = None
    
    def can_dual_wield(self) -> bool:
        """Check if this equipment can be dual wielded."""
        return self.weapon_type in [WeaponType.ONE_HANDED, WeaponType.DUAL_WIELD]

@dataclass
class Corpse(SerializableComponent):
    """Corpse component."""
    name: str 