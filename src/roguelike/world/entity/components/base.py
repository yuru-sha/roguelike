from dataclasses import dataclass
from enum import IntEnum
from typing import Tuple, Optional, Dict, Any, Callable

class RenderOrder(IntEnum):
    """Render order for entities."""
    CORPSE = 1
    ITEM = 2
    ACTOR = 3

@dataclass
class Position:
    """Position component."""
    x: int
    y: int
    
    def distance_to(self, other: 'Position') -> int:
        """Calculate distance to another position."""
        return max(abs(self.x - other.x), abs(self.y - other.y))

@dataclass
class Renderable:
    """Renderable component."""
    char: str
    color: Tuple[int, int, int]
    render_order: RenderOrder
    name: str
    always_visible: bool = False

@dataclass
class Fighter:
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
class AI:
    """AI behavior component."""
    behavior: str = "basic"
    turns_confused: int = 0

@dataclass
class Inventory:
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
class Item:
    """Item component."""
    name: str
    use_function: Optional[Callable] = None
    use_args: Optional[Dict[str, Any]] = None
    targeting: bool = False
    targeting_message: Optional[str] = None

@dataclass
class Level:
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
class Corpse:
    """Corpse component."""
    name: str 