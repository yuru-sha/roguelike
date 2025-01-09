from dataclasses import dataclass, field
from enum import IntEnum, Enum, auto
from typing import Tuple, Optional, Dict, Any, Callable

from roguelike.world.entity.components.serializable import SerializableComponent
from roguelike.world.entity.components.equipment import Equipment, EquipmentSlots
from roguelike.core.constants import EquipmentSlot, WeaponType

class RenderOrder(IntEnum):
    """Render order for entities."""
    CORPSE = 1
    ITEM = 2
    ACTOR = 3

@dataclass
class Position(SerializableComponent):
    """Position component."""
    x: int
    y: int
    
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            '__type__': self.__class__.__name__,
            '__module__': self.__class__.__module__,
            'data': {
                'x': self.x,
                'y': self.y
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Position':
        """Create from dictionary after deserialization."""
        # Handle Position object
        if isinstance(data, Position):
            return cls(x=data.x, y=data.y)
        # Handle dictionary formats
        elif isinstance(data, dict):
            if 'data' in data:
                pos_data = data['data']
            else:
                pos_data = data
            return cls(
                x=pos_data['x'],
                y=pos_data['y']
            )
        # Handle tuple or list format
        elif isinstance(data, (tuple, list)) and len(data) == 2:
            return cls(x=data[0], y=data[1])
        else:
            raise ValueError(f"Invalid data format for Position: {data}")

@dataclass
class Renderable(SerializableComponent):
    """Renderable component."""
    char: str
    color: Tuple[int, int, int]
    render_order: RenderOrder
    name: str
    always_visible: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            '__type__': self.__class__.__name__,
            '__module__': self.__class__.__module__,
            'data': {
                'char': self.char,
                'color': list(self.color),
                'render_order': self.render_order.value,
                'name': self.name,
                'always_visible': self.always_visible
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any] | 'Renderable') -> 'Renderable':
        """Create from dictionary after deserialization."""
        # Renderableオブジェクトが直接渡された場合
        if isinstance(data, Renderable):
            return cls(
                char=data.char,
                color=tuple(data.color),
                render_order=data.render_order,
                name=data.name,
                always_visible=data.always_visible
            )
            
        # 辞書形式の場合
        if not isinstance(data, dict):
            raise ValueError(f"Invalid data format for Renderable: {data}")
            
        component_data = data.get('data', data)
        if not isinstance(component_data, dict):
            raise ValueError(f"Invalid component data format: {component_data}")
            
        # 必須フィールドの存在確認
        required_fields = ['char', 'color', 'render_order', 'name']
        for field in required_fields:
            if field not in component_data:
                raise ValueError(f"Missing required field '{field}' in Renderable data")
                
        # colorの処理
        color_data = component_data['color']
        if not isinstance(color_data, (list, tuple)) or len(color_data) != 3:
            raise ValueError(f"Invalid color format: {color_data}")
        color = tuple(int(c) for c in color_data)
        
        # render_orderの処理
        render_order_value = component_data['render_order']
        try:
            render_order = RenderOrder(render_order_value)
        except ValueError:
            raise ValueError(f"Invalid render_order value: {render_order_value}")
            
        return cls(
            char=str(component_data['char']),
            color=color,
            render_order=render_order,
            name=str(component_data['name']),
            always_visible=bool(component_data.get('always_visible', False))
        )

@dataclass
class Fighter(SerializableComponent):
    """Combat stats component."""
    max_hp: int
    hp: int
    defense: int
    power: int
    xp: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            '__type__': self.__class__.__name__,
            '__module__': self.__class__.__module__,
            'data': {
                'max_hp': self.max_hp,
                'hp': self.hp,
                'defense': self.defense,
                'power': self.power,
                'xp': self.xp
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any] | 'Fighter') -> 'Fighter':
        """Create from dictionary after deserialization."""
        # Fighterオブジェクトが直接渡された場合
        if isinstance(data, Fighter):
            return cls(
                max_hp=data.max_hp,
                hp=data.hp,
                defense=data.defense,
                power=data.power,
                xp=data.xp
            )
            
        # 辞書形式の場合
        if not isinstance(data, dict):
            raise ValueError(f"Invalid data format for Fighter: {data}")
            
        component_data = data.get('data', data)
        if not isinstance(component_data, dict):
            raise ValueError(f"Invalid component data format: {component_data}")
            
        return cls(
            max_hp=int(component_data['max_hp']),
            hp=int(component_data['hp']),
            defense=int(component_data['defense']),
            power=int(component_data['power']),
            xp=int(component_data.get('xp', 0))
        )
    
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