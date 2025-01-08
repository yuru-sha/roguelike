from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass
class Position:
    """Component for entities that exist in the game world."""
    x: int
    y: int

@dataclass
class Renderable:
    """Component for entities that can be rendered."""
    char: str
    color: Tuple[int, int, int]
    render_order: int = 0

@dataclass
class Fighter:
    """Component for entities that can fight."""
    max_hp: int
    hp: int
    defense: int
    power: int
    xp: int = 0
    
    def take_damage(self, amount: int) -> int:
        """
        Deal damage to this fighter.
        
        Args:
            amount: Amount of damage to deal
            
        Returns:
            Amount of XP awarded for killing this fighter (0 if not killed)
        """
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            return self.xp
        return 0
    
    def heal(self, amount: int) -> None:
        """
        Heal this fighter.
        
        Args:
            amount: Amount of HP to restore
        """
        self.hp = min(self.max_hp, self.hp + amount)

@dataclass
class AI:
    """Component for entities that have AI behavior."""
    pass

@dataclass
class Inventory:
    """Component for entities that can carry items."""
    capacity: int
    items: list = None
    
    def __post_init__(self) -> None:
        if self.items is None:
            self.items = []

@dataclass
class Item:
    """Component for entities that can be picked up and used."""
    use_function: Optional[callable] = None
    targeting: bool = False
    targeting_message: Optional[str] = None
    consumable: bool = True

@dataclass
class Level:
    """Component for entities that can gain experience and level up."""
    current_level: int = 1
    current_xp: int = 0
    level_up_base: int = 0
    level_up_factor: int = 150
    
    @property
    def experience_to_next_level(self) -> int:
        """Returns the amount of experience needed to reach the next level."""
        return self.level_up_base + self.current_level * self.level_up_factor
    
    def add_xp(self, xp: int) -> bool:
        """
        Add experience points and handle leveling up.
        
        Args:
            xp: Amount of experience points to add
            
        Returns:
            True if the entity leveled up
        """
        self.current_xp += xp
        
        if self.current_xp >= self.experience_to_next_level:
            self.current_xp -= self.experience_to_next_level
            self.current_level += 1
            return True
            
        return False

@dataclass
class Corpse:
    """Component for entities that are dead and leave a corpse."""
    name: str 