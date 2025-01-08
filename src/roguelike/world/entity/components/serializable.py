"""
Base class for serializable components.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Type, TypeVar

T = TypeVar('T', bound='SerializableComponent')

@dataclass
class SerializableComponent:
    """Base class for components that can be serialized."""
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert component to dictionary.
        
        Returns:
            Dictionary representation of the component
        """
        return {
            '__type__': self.__class__.__name__,
            '__module__': self.__class__.__module__,
            'data': asdict(self)
        }
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create component from dictionary.
        
        Args:
            data: Dictionary containing component data
            
        Returns:
            New component instance
        """
        return cls(**data['data']) 