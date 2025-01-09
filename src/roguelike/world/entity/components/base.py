"""
Base components for the game entities.
"""

from dataclasses import dataclass, field
from enum import IntEnum, Enum, auto
from typing import Tuple, Optional, Dict, Any, Callable, Set, Type, ClassVar, List, Union
import math

from roguelike.world.entity.components.serializable import (
    SerializableComponent,
    range_validator,
    custom_validator,
    length_validator
)
from roguelike.world.entity.components.equipment import Equipment, EquipmentSlots
from roguelike.core.constants import EquipmentSlot, WeaponType, MAP_WIDTH, MAP_HEIGHT

class ComponentDependency:
    """Manages component dependencies."""
    
    def __init__(self, *required_components: Type[SerializableComponent]):
        self.required_components = set(required_components)
    
    def __call__(self, cls: Type[SerializableComponent]) -> Type[SerializableComponent]:
        """Register dependencies for a component."""
        if not hasattr(cls, 'dependencies'):
            cls.dependencies: ClassVar[Set[Type[SerializableComponent]]] = set()
        cls.dependencies.update(self.required_components)
        
        # Add validate_dependencies method
        def validate_dependencies(entity_components: Set[Type[SerializableComponent]]) -> bool:
            """Validate that all required components are present."""
            return all(dep in entity_components for dep in cls.dependencies)
        
        cls.validate_dependencies = staticmethod(validate_dependencies)
        return cls

class AIBehavior(Enum):
    """Available AI behaviors."""
    BASIC = "basic"
    CONFUSED = "confused"
    AGGRESSIVE = "aggressive"
    COWARD = "coward"
    RANGED = "ranged"
    SUPPORT = "support"

class RenderOrder(IntEnum):
    """Render order for entities."""
    CORPSE = 1
    ITEM = 2
    ACTOR = 3

class StatusEffect(Enum):
    """Available status effects."""
    POISONED = "poisoned"
    BURNING = "burning"
    FROZEN = "frozen"
    STUNNED = "stunned"
    HASTED = "hasted"
    SLOWED = "slowed"
    INVISIBLE = "invisible"
    REGENERATING = "regenerating"

@dataclass
class StatusEffectData:
    """Data for a status effect."""
    type: StatusEffect
    duration: int
    strength: int
    source_entity: Optional[int] = None

@ComponentDependency()  # No dependencies
@dataclass
class Position(SerializableComponent):
    """Position component."""
    x: int = field(default_factory=lambda: custom_validator(
        lambda x: 0 <= x < MAP_WIDTH,
        f"X coordinate must be between 0 and {MAP_WIDTH-1}",
        0
    ))
    y: int = field(default_factory=lambda: custom_validator(
        lambda y: 0 <= y < MAP_HEIGHT,
        f"Y coordinate must be between 0 and {MAP_HEIGHT-1}",
        0
    ))
    
    def distance_to(self, other: 'Position') -> int:
        """Calculate distance to another position."""
        return max(abs(self.x - other.x), abs(self.y - other.y))
    
    def __hash__(self) -> int:
        """Make Position hashable."""
        return hash((self.x, self.y))
    
    def __eq__(self, other: object) -> bool:
        """Implement equality comparison."""
        if not isinstance(other, Position):
            return NotImplemented
        return self.x == other.x and self.y == other.y

@ComponentDependency(Position)  # Requires Position
@dataclass
class Fighter(SerializableComponent):
    """Component for entities that can fight."""
    max_hp: int = field(default_factory=lambda: range_validator(min_value=1, default=30))
    hp: int = field(default_factory=lambda: range_validator(min_value=0, default=30))
    defense: int = field(default_factory=lambda: range_validator(min_value=0, default=2))
    power: int = field(default_factory=lambda: range_validator(min_value=0, default=5))
    xp: int = field(default_factory=lambda: range_validator(min_value=0, default=0))

    def __post_init__(self):
        """Ensure hp doesn't exceed max_hp."""
        super().__post_init__()
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def take_damage(self, amount: int) -> int:
        """Take damage and return the amount of damage taken."""
        if self.hp <= 0:
            return 0
        self.hp = max(0, self.hp - amount)
        return amount

    def heal(self, amount: int) -> int:
        """Heal and return the amount of HP recovered."""
        if self.hp <= 0 or self.hp >= self.max_hp:
            return 0
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp

@ComponentDependency(Position)  # Requires Position
@dataclass
class Renderable(SerializableComponent):
    """Component for entities that can be rendered."""
    char: str = field(default_factory=lambda: length_validator(min_length=1, max_length=1, default='?'))
    color: Tuple[int, int, int] = field(default_factory=lambda: custom_validator(
        lambda c: isinstance(c, tuple) and len(c) == 3 and all(0 <= x <= 255 for x in c),
        "Color must be a tuple of 3 integers between 0 and 255",
        (255, 255, 255)
    ))
    render_order: RenderOrder = field(default=RenderOrder.ACTOR)
    name: str = field(default_factory=lambda: length_validator(min_length=1, max_length=50, default='Unknown'))
    always_visible: bool = field(default=False)

@ComponentDependency(Fighter)  # Requires Fighter
@dataclass
class StatusEffects(SerializableComponent):
    """Component for entities that can have status effects."""
    effects: Dict[StatusEffect, StatusEffectData] = field(default_factory=dict)
    
    def add_effect(self, effect: StatusEffect, duration: int, strength: int, source: Optional[int] = None) -> None:
        """Add or refresh a status effect."""
        self.effects[effect] = StatusEffectData(effect, duration, strength, source)
    
    def remove_effect(self, effect: StatusEffect) -> None:
        """Remove a status effect."""
        self.effects.pop(effect, None)
    
    def update(self) -> None:
        """Update status effects durations."""
        expired = [effect for effect, data in self.effects.items() if data.duration <= 0]
        for effect in expired:
            self.remove_effect(effect)
        
        for data in self.effects.values():
            data.duration -= 1

@ComponentDependency(Position)  # Requires Position
@dataclass
class Vision(SerializableComponent):
    """Component for entities that can see."""
    range: int = field(default_factory=lambda: range_validator(min_value=1, default=8))
    can_see_invisible: bool = field(default=False)
    night_vision: bool = field(default=False)
    
    def can_see(self, distance: float) -> bool:
        """Check if entity can see at given distance."""
        return distance <= self.range

@ComponentDependency(Position, Fighter)  # Requires Position and Fighter
@dataclass
class Skills(SerializableComponent):
    """Component for entities that can use skills."""
    available_skills: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    cooldowns: Dict[str, int] = field(default_factory=dict)
    
    def add_skill(self, skill_id: str, data: Dict[str, Any]) -> None:
        """Add a new skill."""
        self.available_skills[skill_id] = data
        self.cooldowns[skill_id] = 0
    
    def remove_skill(self, skill_id: str) -> None:
        """Remove a skill."""
        self.available_skills.pop(skill_id, None)
        self.cooldowns.pop(skill_id, None)
    
    def update_cooldowns(self) -> None:
        """Update skill cooldowns."""
        for skill_id in list(self.cooldowns.keys()):
            if self.cooldowns[skill_id] > 0:
                self.cooldowns[skill_id] -= 1

@ComponentDependency(Position)  # Requires Position
@dataclass
class Experience(SerializableComponent):
    """Component for entities that can gain experience."""
    level: int = field(default_factory=lambda: range_validator(min_value=1, default=1))
    current_xp: int = field(default_factory=lambda: range_validator(min_value=0, default=0))
    xp_to_next_level: int = field(init=False)
    skill_points: int = field(default_factory=lambda: range_validator(min_value=0, default=0))
    
    def __post_init__(self):
        """Calculate XP needed for next level."""
        super().__post_init__()
        self.xp_to_next_level = self.calculate_xp_for_level(self.level + 1)
    
    @staticmethod
    def calculate_xp_for_level(level: int) -> int:
        """Calculate XP needed for a given level."""
        return int(100 * (level - 1) * math.sqrt(level))
    
    def add_xp(self, amount: int) -> bool:
        """Add XP and return True if leveled up."""
        self.current_xp += amount
        if self.current_xp >= self.xp_to_next_level:
            self.level_up()
            return True
        return False
    
    def level_up(self) -> None:
        """Level up the entity."""
        self.level += 1
        self.current_xp -= self.xp_to_next_level
        self.xp_to_next_level = self.calculate_xp_for_level(self.level + 1)
        self.skill_points += 1

@ComponentDependency(Position, Fighter)  # Requires Position and Fighter
@dataclass
class AI(SerializableComponent):
    """AI behavior component."""
    behavior: AIBehavior = field(default_factory=lambda: custom_validator(
        lambda b: isinstance(b, AIBehavior) or b in [e.value for e in AIBehavior],
        f"Behavior must be one of: {', '.join(e.value for e in AIBehavior)}",
        AIBehavior.BASIC
    ))
    turns_confused: int = field(default_factory=lambda: range_validator(min_value=0, default=0))
    target_entity: Optional[int] = field(default=None)
    last_known_position: Optional[Position] = field(default=None)
    aggression_range: int = field(default_factory=lambda: range_validator(min_value=1, default=8))
    flee_threshold: float = field(default_factory=lambda: range_validator(min_value=0.0, max_value=1.0, default=0.3))

    def __post_init__(self):
        """Convert string behavior to enum and validate."""
        super().__post_init__()
        if isinstance(self.behavior, str):
            try:
                self.behavior = AIBehavior(self.behavior)
            except ValueError:
                raise ValueError(f"Invalid behavior: {self.behavior}")

    def is_confused(self) -> bool:
        """Check if the entity is confused."""
        return self.turns_confused > 0

    def update_confusion(self) -> None:
        """Update confusion status."""
        if self.turns_confused > 0:
            self.turns_confused -= 1

    def set_target(self, entity_id: int, position: Position) -> None:
        """Set target entity and its last known position."""
        self.target_entity = entity_id
        self.last_known_position = position

    def clear_target(self) -> None:
        """Clear target information."""
        self.target_entity = None
        self.last_known_position = None

@ComponentDependency(Position)  # Requires Position
@dataclass
class Inventory(SerializableComponent):
    """Component for entities that can carry items."""
    capacity: int = field(default_factory=lambda: range_validator(min_value=1, default=26))
    items: Dict[int, int] = field(default_factory=dict)  # item_id -> slot_index

    def __post_init__(self):
        """Validate inventory state."""
        super().__post_init__()
        # Ensure no duplicate slots
        used_slots = set()
        for item_id, slot in self.items.items():
            if slot in used_slots:
                raise ValueError(f"Duplicate slot index: {slot}")
            if slot >= self.capacity:
                raise ValueError(f"Slot index {slot} exceeds capacity {self.capacity}")
            used_slots.add(slot)

    def add_item(self, item_id: int) -> Optional[int]:
        """Add an item to the first available slot."""
        used_slots = set(self.items.values())
        for i in range(self.capacity):
            if i not in used_slots:
                self.items[item_id] = i
                return i
        return None

    def remove_item(self, item_id: int) -> Optional[int]:
        """Remove an item and return its slot number."""
        return self.items.pop(item_id, None)

    def is_full(self) -> bool:
        """Check if inventory is full."""
        return len(self.items) >= self.capacity

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            '__type__': self.__class__.__name__,
            '__module__': self.__class__.__module__,
            'data': {
                'capacity': self.capacity,
                'items': self.items if self.items is not None else []
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any] | 'Inventory') -> 'Inventory':
        """Create from dictionary after deserialization."""
        # Inventoryオブジェクトが直接渡された場合
        if isinstance(data, Inventory):
            return cls(
                capacity=data.capacity,
                items=data.items
            )
            
        # 辞書形式の場合
        if not isinstance(data, dict):
            raise ValueError(f"Invalid data format for Inventory: {data}")
            
        component_data = data.get('data', data)
        if not isinstance(component_data, dict):
            raise ValueError(f"Invalid component data format: {component_data}")
            
        return cls(
            capacity=int(component_data['capacity']),
            items=component_data.get('items', [])
        )

@dataclass
class Item(SerializableComponent):
    """Item component."""
    name: str
    use_function: Optional[Callable] = None
    use_args: Optional[Dict[str, Any]] = None
    targeting: bool = False
    targeting_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            '__type__': self.__class__.__name__,
            '__module__': self.__class__.__module__,
            'data': {
                'name': self.name,
                'use_function': f"{self.use_function.__module__}.{self.use_function.__name__}" if self.use_function else None,
                'use_args': self.use_args,
                'targeting': self.targeting,
                'targeting_message': self.targeting_message
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any] | 'Item') -> 'Item':
        """Create from dictionary after deserialization."""
        # Itemオブジェクトが直接渡された場合
        if isinstance(data, Item):
            return cls(
                name=data.name,
                use_function=data.use_function,
                use_args=data.use_args,
                targeting=data.targeting,
                targeting_message=data.targeting_message
            )
            
        # 辞書形式の場合
        if not isinstance(data, dict):
            raise ValueError(f"Invalid data format for Item: {data}")
            
        component_data = data.get('data', data)
        if not isinstance(component_data, dict):
            raise ValueError(f"Invalid component data format: {component_data}")
            
        # use_functionの処理
        use_function_path = component_data.get('use_function')
        use_function = None
        if use_function_path:
            try:
                module_name, function_name = use_function_path.rsplit('.', 1)
                module = __import__(module_name, fromlist=[function_name])
                use_function = getattr(module, function_name)
            except (ValueError, ImportError, AttributeError) as e:
                logger.warning(f"Failed to load use_function {use_function_path}: {e}")
                
        return cls(
            name=str(component_data['name']),
            use_function=use_function,
            use_args=component_data.get('use_args'),
            targeting=bool(component_data.get('targeting', False)),
            targeting_message=component_data.get('targeting_message')
        )

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
class Corpse(SerializableComponent):
    """Corpse component."""
    original_name: str 
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            '__type__': self.__class__.__name__,
            '__module__': self.__class__.__module__,
            'data': {
                'original_name': self.original_name
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any] | 'Corpse') -> 'Corpse':
        """Create from dictionary after deserialization."""
        # Corpseオブジェクトが直接渡された場合
        if isinstance(data, Corpse):
            return cls(original_name=data.original_name)
            
        # 辞書形式の場合
        if not isinstance(data, dict):
            raise ValueError(f"Invalid data format for Corpse: {data}")
            
        component_data = data.get('data', data)
        if not isinstance(component_data, dict):
            raise ValueError(f"Invalid component data format: {component_data}")
            
        return cls(
            original_name=str(component_data['original_name'])
        ) 