"""
Base components for the game entities.
"""

import math
from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from typing import (Any, Callable, ClassVar, Dict, List, Optional, Set, Tuple,
                    Type, Union)

from roguelike.core.constants import (MAP_HEIGHT, MAP_WIDTH, EquipmentSlot,
                                      WeaponType, AIBehavior, RenderOrder,
                                      StatusEffect)
from roguelike.world.entity.components.equipment import (Equipment,
                                                         EquipmentSlots)
from roguelike.world.entity.components.serializable import (
    SerializableComponent, custom_validator, length_validator, range_validator)


class ComponentDependency:
    """Manages component dependencies."""

    def __init__(self, *required_components: Type[SerializableComponent]):
        self.required_components = set(required_components)

    def __call__(self, cls: Type[SerializableComponent]) -> Type[SerializableComponent]:
        """Register dependencies for a component."""
        if not hasattr(cls, "dependencies"):
            cls.dependencies: ClassVar[Set[Type[SerializableComponent]]] = set()
        cls.dependencies.update(self.required_components)

        # Add validate_dependencies method
        def validate_dependencies(
            entity_components: Set[Type[SerializableComponent]],
        ) -> bool:
            """Validate that all required components are present."""
            return all(dep in entity_components for dep in cls.dependencies)

        cls.validate_dependencies = staticmethod(validate_dependencies)
        return cls


@dataclass
class StatusEffectData:
    """Data for a status effect."""

    type: StatusEffect
    duration: int
    strength: int
    source_entity: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "__type__": self.__class__.__name__,
            "__module__": self.__class__.__module__,
            "data": {
                "type": self.type,
                "duration": self.duration,
                "strength": self.strength,
                "source_entity": self.source_entity,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatusEffectData":
        """Create from dictionary after deserialization."""
        type = StatusEffect(data["type"])
        duration = int(data["duration"])
        strength = int(data["strength"])
        source_entity = data.get("source_entity")
        return cls(
            type=type, duration=duration, strength=strength, source_entity=source_entity
        )


@ComponentDependency()  # No dependencies
@dataclass
class Position(SerializableComponent):
    """Position component."""

    x: int = 0
    y: int = 0

    def __post_init__(self):
        """Validate position."""
        if not (0 <= self.x < MAP_WIDTH):
            raise ValueError(f"X coordinate must be between 0 and {MAP_WIDTH-1}")
        if not (0 <= self.y < MAP_HEIGHT):
            raise ValueError(f"Y coordinate must be between 0 and {MAP_HEIGHT-1}")

    def distance_to(self, other: "Position") -> int:
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

    max_hp: int = 30
    hp: int = 30
    defense: int = 2
    power: int = 5
    xp: int = 0

    def __post_init__(self):
        """Validate fighter stats."""
        if self.max_hp < 1:
            raise ValueError("Maximum HP must be at least 1")
        if self.hp < 0:
            raise ValueError("HP cannot be negative")
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        if self.defense < 0:
            raise ValueError("Defense cannot be negative")
        if self.power < 0:
            raise ValueError("Power cannot be negative")
        if self.xp < 0:
            raise ValueError("XP cannot be negative")

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

    char: str = "?"
    color: Tuple[int, int, int] = (255, 255, 255)
    render_order: RenderOrder = RenderOrder.ACTOR
    name: str = "Unknown"
    always_visible: bool = False

    def __post_init__(self):
        """Validate renderable properties."""
        if len(self.char) != 1:
            raise ValueError("Character must be exactly one character long")
        if not isinstance(self.color, tuple) or len(self.color) != 3:
            raise ValueError("Color must be a tuple of 3 integers")
        if not all(0 <= x <= 255 for x in self.color):
            raise ValueError("Color values must be between 0 and 255")
        if not isinstance(self.name, str) or len(self.name) < 1:
            raise ValueError("Name must be a non-empty string")
        if len(self.name) > 50:
            raise ValueError("Name must not exceed 50 characters")


@ComponentDependency(Fighter)  # Requires Fighter
@dataclass
class StatusEffects(SerializableComponent):
    """Component for entities that can have status effects."""

    effects: Dict[StatusEffect, StatusEffectData] = field(default_factory=dict)

    def add_effect(
        self,
        effect: StatusEffect,
        duration: int,
        strength: int,
        source: Optional[int] = None,
    ) -> None:
        """Add or refresh a status effect."""
        if duration <= 0:
            raise ValueError("Duration must be positive")
        if strength < 0:
            raise ValueError("Strength cannot be negative")
        self.effects[effect] = StatusEffectData(effect, duration, strength, source)

    def remove_effect(self, effect: StatusEffect) -> None:
        """Remove a status effect."""
        self.effects.pop(effect, None)

    def update(self) -> None:
        """Update status effects durations."""
        expired = [
            effect for effect, data in self.effects.items() if data.duration <= 0
        ]
        for effect in expired:
            self.remove_effect(effect)

        for data in self.effects.values():
            data.duration -= 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "__type__": self.__class__.__name__,
            "__module__": self.__class__.__module__,
            "data": {
                "effects": {
                    effect.value: data.to_dict()
                    for effect, data in self.effects.items()
                }
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatusEffects":
        """Create from dictionary after deserialization."""
        effects_data = data.get("effects", {})
        effects = {}
        for effect_value, data_dict in effects_data.items():
            effect = StatusEffect(effect_value)
            effects[effect] = StatusEffectData.from_dict(data_dict)
        return cls(effects=effects)


@ComponentDependency(Position)  # Requires Position
@dataclass
class Vision(SerializableComponent):
    """Component for entities that can see."""

    range: int = 8
    can_see_invisible: bool = False
    night_vision: bool = False

    def __post_init__(self):
        """Validate vision properties."""
        if self.range < 1:
            raise ValueError("Vision range must be at least 1")

    def can_see(self, distance: float) -> bool:
        """Check if entity can see at given distance."""
        return distance <= self.range

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "__type__": self.__class__.__name__,
            "__module__": self.__class__.__module__,
            "data": {
                "range": self.range,
                "can_see_invisible": self.can_see_invisible,
                "night_vision": self.night_vision,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Vision":
        """Create from dictionary after deserialization."""
        return cls(
            range=int(data.get("range", 8)),
            can_see_invisible=bool(data.get("can_see_invisible", False)),
            night_vision=bool(data.get("night_vision", False)),
        )


@ComponentDependency(Position, Fighter)  # Requires Position and Fighter
@dataclass
class Skills(SerializableComponent):
    """Component for entities that can use skills."""

    available_skills: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    cooldowns: Dict[str, int] = field(default_factory=dict)

    def add_skill(self, skill_id: str, data: Dict[str, Any]) -> None:
        """Add a new skill."""
        if not skill_id:
            raise ValueError("Skill ID cannot be empty")
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "__type__": self.__class__.__name__,
            "__module__": self.__class__.__module__,
            "data": {
                "available_skills": self.available_skills,
                "cooldowns": self.cooldowns,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skills":
        """Create from dictionary after deserialization."""
        available_skills = data.get("available_skills", {})
        cooldowns = {
            skill_id: int(cooldown)
            for skill_id, cooldown in data.get("cooldowns", {}).items()
        }
        return cls(available_skills=available_skills, cooldowns=cooldowns)


@ComponentDependency(Position)  # Requires Position
@dataclass
class Experience(SerializableComponent):
    """Component for entities that can gain experience."""

    level: int = 1
    current_xp: int = 0
    xp_to_next_level: int = field(init=False)
    skill_points: int = 0

    def __post_init__(self):
        """Calculate XP needed for next level and validate."""
        if self.level < 1:
            raise ValueError("Level must be at least 1")
        if self.current_xp < 0:
            raise ValueError("Current XP cannot be negative")
        if self.skill_points < 0:
            raise ValueError("Skill points cannot be negative")
        self.xp_to_next_level = self.calculate_xp_for_level(self.level + 1)

    @staticmethod
    def calculate_xp_for_level(level: int) -> int:
        """Calculate XP needed for a given level."""
        return int(100 * (level - 1) * math.sqrt(level))

    def add_xp(self, amount: int) -> bool:
        """Add XP and return True if leveled up."""
        if amount < 0:
            raise ValueError("XP amount cannot be negative")
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "__type__": self.__class__.__name__,
            "__module__": self.__class__.__module__,
            "data": {
                "level": self.level,
                "current_xp": self.current_xp,
                "skill_points": self.skill_points,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Experience":
        """Create from dictionary after deserialization."""
        instance = cls(
            level=int(data.get("level", 1)),
            current_xp=int(data.get("current_xp", 0)),
            skill_points=int(data.get("skill_points", 0)),
        )
        instance.xp_to_next_level = instance.calculate_xp_for_level(instance.level + 1)
        return instance


@ComponentDependency(Position, Fighter)  # Requires Position and Fighter
@dataclass
class AI(SerializableComponent):
    """AI behavior component."""

    behavior: AIBehavior = AIBehavior.BASIC
    turns_confused: int = 0
    target_entity: Optional[int] = None
    last_known_position: Optional[Position] = None
    aggression_range: int = 8
    flee_threshold: float = 0.3

    def __post_init__(self):
        """Validate AI properties."""
        if isinstance(self.behavior, str):
            try:
                self.behavior = AIBehavior(self.behavior)
            except ValueError:
                raise ValueError(f"Invalid behavior: {self.behavior}")
        if self.turns_confused < 0:
            raise ValueError("Turns confused cannot be negative")
        if self.aggression_range < 1:
            raise ValueError("Aggression range must be at least 1")
        if not 0.0 <= self.flee_threshold <= 1.0:
            raise ValueError("Flee threshold must be between 0 and 1")

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

    capacity: int = 26  # Rogue uses a-z for inventory slots
    items: Dict[str, int] = field(default_factory=dict)  # slot_key -> item_id
    quick_slots: Dict[str, str] = field(default_factory=dict)  # key -> slot_key

    def __post_init__(self):
        """Validate inventory state."""
        if self.capacity < 1:
            raise ValueError("Inventory capacity must be at least 1")
        if self.capacity > 26:
            raise ValueError("Inventory capacity cannot exceed 26 slots")
        
        # Validate slot keys
        for slot in self.items.keys():
            if not self._is_valid_slot(slot):
                raise ValueError(f"Invalid slot key: {slot}")

    @staticmethod
    def _is_valid_slot(slot: str) -> bool:
        """Check if slot key is valid (a-z)."""
        return len(slot) == 1 and 'a' <= slot <= 'z'

    @staticmethod
    def _get_slot_key(index: int) -> str:
        """Convert numeric index to slot key (0 -> 'a', 1 -> 'b', etc.)."""
        if not 0 <= index < 26:
            raise ValueError("Slot index must be between 0 and 25")
        return chr(ord('a') + index)

    def add_item(self, item_id: int) -> Optional[str]:
        """Add an item to the first available slot and return the slot key."""
        used_slots = set(self.items.keys())
        for i in range(self.capacity):
            slot = self._get_slot_key(i)
            if slot not in used_slots:
                self.items[slot] = item_id
                return slot
        return None

    def remove_item(self, slot: str) -> Optional[int]:
        """Remove an item from a specific slot and return its ID."""
        if not self._is_valid_slot(slot):
            raise ValueError(f"Invalid slot key: {slot}")
        return self.items.pop(slot, None)

    def get_item(self, slot: str) -> Optional[int]:
        """Get the item ID in a specific slot."""
        if not self._is_valid_slot(slot):
            raise ValueError(f"Invalid slot key: {slot}")
        return self.items.get(slot)

    def is_full(self) -> bool:
        """Check if inventory is full."""
        return len(self.items) >= self.capacity

    def get_items(self) -> Dict[str, int]:
        """Get all items in the inventory."""
        return dict(self.items)

    def clear(self) -> None:
        """Remove all items from inventory."""
        self.items.clear()
        self.quick_slots.clear()

    def set_quick_slot(self, key: str, slot: str) -> bool:
        """Assign a quick slot key to an inventory slot."""
        if not self._is_valid_slot(slot):
            return False
        if slot not in self.items:
            return False
        self.quick_slots[key] = slot
        return True

    def get_quick_slot(self, key: str) -> Optional[str]:
        """Get the inventory slot assigned to a quick slot key."""
        return self.quick_slots.get(key)

    def clear_quick_slot(self, key: str) -> None:
        """Remove a quick slot assignment."""
        self.quick_slots.pop(key, None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "__type__": self.__class__.__name__,
            "__module__": self.__class__.__module__,
            "data": {
                "capacity": self.capacity,
                "items": self.items,
                "quick_slots": self.quick_slots,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any] | "Inventory") -> "Inventory":
        """Create from dictionary after deserialization."""
        if isinstance(data, Inventory):
            return cls(
                capacity=data.capacity,
                items=data.items,
                quick_slots=data.quick_slots,
            )

        component_data = data.get("data", data)
        return cls(
            capacity=int(component_data["capacity"]),
            items=component_data.get("items", {}),
            quick_slots=component_data.get("quick_slots", {}),
        )


@dataclass
class Item(SerializableComponent):
    """Item component."""

    name: str
    description: str = ""
    use_function: Optional[Callable] = None
    use_args: Optional[Dict[str, Any]] = None
    targeting: bool = False
    targeting_message: Optional[str] = None
    stackable: bool = False
    stack_count: int = 1

    def __post_init__(self):
        """Validate item properties."""
        if not self.name:
            raise ValueError("Item name must not be empty")
        if self.stack_count < 1:
            raise ValueError("Stack count must be at least 1")
        if self.stackable and self.stack_count < 1:
            raise ValueError("Stackable items must have a positive stack count")

    def get_full_name(self) -> str:
        """Get the full name of the item, including stack count if applicable."""
        base_name = self.name
        if self.stackable and self.stack_count > 1:
            return f"{base_name} (x{self.stack_count})"
        return base_name

    def split_stack(self, count: int) -> None:
        """Split the stack and return a new item with the specified count."""
        if not self.stackable:
            raise ValueError("Cannot split non-stackable items")
        if count >= self.stack_count:
            raise ValueError("Split count must be less than current stack count")
        if count < 1:
            raise ValueError("Split count must be positive")
        
        self.stack_count -= count

    def merge_stack(self, other: "Item") -> bool:
        """Merge another stack into this one. Returns True if successful."""
        if not self.stackable or not other.stackable:
            return False
        if self.name != other.name:
            return False
            
        self.stack_count += other.stack_count
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "__type__": self.__class__.__name__,
            "__module__": self.__class__.__module__,
            "data": {
                "name": self.name,
                "description": self.description,
                "use_function": f"{self.use_function.__module__}.{self.use_function.__name__}"
                if self.use_function else None,
                "use_args": self.use_args,
                "targeting": self.targeting,
                "targeting_message": self.targeting_message,
                "stackable": self.stackable,
                "stack_count": self.stack_count,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any] | "Item") -> "Item":
        """Create from dictionary after deserialization."""
        # Handle direct Item object
        if isinstance(data, Item):
            return cls(
                name=data.name,
                description=data.description,
                use_function=data.use_function,
                use_args=data.use_args,
                targeting=data.targeting,
                targeting_message=data.targeting_message,
                stackable=data.stackable,
                stack_count=data.stack_count,
            )

        # Handle dictionary
        component_data = data.get("data", data)
        
        # Handle use_function
        use_function_path = component_data.get("use_function")
        use_function = None
        if use_function_path:
            try:
                module_name, function_name = use_function_path.rsplit(".", 1)
                module = __import__(module_name, fromlist=[function_name])
                use_function = getattr(module, function_name)
            except (ValueError, ImportError, AttributeError) as e:
                logger.warning(f"Failed to load use_function {use_function_path}: {e}")

        return cls(
            name=str(component_data["name"]),
            description=str(component_data.get("description", "")),
            use_function=use_function,
            use_args=component_data.get("use_args"),
            targeting=bool(component_data.get("targeting", False)),
            targeting_message=component_data.get("targeting_message"),
            stackable=bool(component_data.get("stackable", False)),
            stack_count=int(component_data.get("stack_count", 1)),
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
            "__type__": self.__class__.__name__,
            "__module__": self.__class__.__module__,
            "data": {"original_name": self.original_name},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any] | "Corpse") -> "Corpse":
        """Create from dictionary after deserialization."""
        # Corpseオブジェクトが直接渡された場合
        if isinstance(data, Corpse):
            return cls(original_name=data.original_name)

        # 辞書形式の場合
        if not isinstance(data, dict):
            raise ValueError(f"Invalid data format for Corpse: {data}")

        component_data = data.get("data", data)
        if not isinstance(component_data, dict):
            raise ValueError(f"Invalid component data format: {component_data}")

        return cls(original_name=str(component_data["original_name"]))


@ComponentDependency(Position)  # Requires Position
@dataclass
class Consumable(SerializableComponent):
    """Component for items that can be consumed."""

    use_function: Optional[Callable] = None
    use_args: Optional[Dict[str, Any]] = None
    targeting: bool = False
    targeting_message: Optional[str] = None
    number_of_uses: int = 1
    auto_identify: bool = True  # Whether using the item identifies it

    def __post_init__(self):
        """Validate consumable properties."""
        if self.number_of_uses < 1:
            raise ValueError("Number of uses must be at least 1")

    def use(self, entity_id: int, world: Any, *args, **kwargs) -> bool:
        """
        Use the item and return True if successful.
        
        Args:
            entity_id: The ID of the item entity
            world: The game world
            *args: Additional arguments for the use function
            **kwargs: Additional keyword arguments for the use function
        """
        if self.use_function is None:
            return False
        
        if self.number_of_uses <= 0:
            return False

        # Try to get the Identifiable component if it exists
        identifiable = None
        if world.has_component(entity_id, Identifiable):
            identifiable = world.component_for_entity(entity_id, Identifiable)
            identifiable.try_item()  # Mark as tried before use

        result = self.use_function(*args, **kwargs)
        if result:
            self.number_of_uses -= 1
            # Auto-identify the item if successful and auto_identify is True
            if identifiable and self.auto_identify:
                identifiable.identify()
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "__type__": self.__class__.__name__,
            "__module__": self.__class__.__module__,
            "data": {
                "use_function": f"{self.use_function.__module__}.{self.use_function.__name__}"
                if self.use_function else None,
                "use_args": self.use_args,
                "targeting": self.targeting,
                "targeting_message": self.targeting_message,
                "number_of_uses": self.number_of_uses,
                "auto_identify": self.auto_identify,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Consumable":
        """Create from dictionary after deserialization."""
        component_data = data.get("data", data)
        
        # Handle use_function
        use_function_path = component_data.get("use_function")
        use_function = None
        if use_function_path:
            try:
                module_name, function_name = use_function_path.rsplit(".", 1)
                module = __import__(module_name, fromlist=[function_name])
                use_function = getattr(module, function_name)
            except (ValueError, ImportError, AttributeError) as e:
                logger.warning(f"Failed to load use_function {use_function_path}: {e}")

        return cls(
            use_function=use_function,
            use_args=component_data.get("use_args"),
            targeting=bool(component_data.get("targeting", False)),
            targeting_message=component_data.get("targeting_message"),
            number_of_uses=int(component_data.get("number_of_uses", 1)),
            auto_identify=bool(component_data.get("auto_identify", True))
        )
