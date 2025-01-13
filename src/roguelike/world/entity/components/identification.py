"""
Identification component for items.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, ClassVar, Set, Type, List
from enum import Enum, auto
import random

from roguelike.world.entity.components.serializable import SerializableComponent


class ItemType(Enum):
    """Item types that require identification."""
    SCROLL = auto()
    POTION = auto()
    RING = auto()
    WEAPON = auto()
    ARMOR = auto()
    AMULET = auto()
    WAND = auto()


@dataclass
class ItemAppearance:
    """Appearance data for unidentified items."""
    item_type: ItemType
    appearance: str
    is_used: bool = False


class AppearanceGenerator:
    """Generates and manages random appearances for items."""

    # Rogue-like appearances for different item types
    SCROLL_TITLES = [
        "ZELGO MER", "JUYED AWK YACC", "NR 9", "XIXAXA XOXAXA XUXAXA",
        "PRATYAVAYAH", "DAIYEN FOOELS", "LEP GEX VEN ZEA", "TEMOV",
        "GARVEN DEH", "YUM YUM", "VENZAR BORGAVVE", "THARR",
        "ANDOVA BEGARIN", "KIRJE", "VE FORBRYDERNE", "HACKEM MUCHE",
        "VELOX NEB", "READ ME", "FOOBIE BLETCH"
    ]

    POTION_COLORS = [
        "ruby red", "pink", "orange", "yellow", "emerald", "dark green",
        "sky blue", "cyan", "royal blue", "magenta", "purple", "brown",
        "grey", "white", "golden", "silver", "black", "plaid", "swirly",
        "bubbly", "smoky", "cloudy", "effervescent"
    ]

    RING_GEMS = [
        "diamond", "ruby", "sapphire", "emerald", "turquoise", "amethyst",
        "topaz", "opal", "garnet", "pearl", "jade", "agate", "onyx",
        "moonstone", "tiger eye", "jasper", "aquamarine"
    ]

    AMULET_MATERIALS = [
        "silver", "gold", "brass", "copper", "bronze", "platinum",
        "iron", "steel", "mithril", "glass", "wooden", "bone"
    ]

    WAND_MATERIALS = [
        "oak", "ebony", "maple", "pine", "balsa", "crystal", "brass",
        "copper", "silver", "iron", "steel", "bone", "zinc", "aluminum",
        "uranium", "tungsten", "iridium", "nickel", "cobalt", "tin"
    ]

    def __init__(self):
        """Initialize appearance lists."""
        self.scroll_appearances = [ItemAppearance(ItemType.SCROLL, title) for title in self.SCROLL_TITLES]
        self.potion_appearances = [ItemAppearance(ItemType.POTION, color) for color in self.POTION_COLORS]
        self.ring_appearances = [ItemAppearance(ItemType.RING, gem) for gem in self.RING_GEMS]
        self.amulet_appearances = [ItemAppearance(ItemType.AMULET, material) for material in self.AMULET_MATERIALS]
        self.wand_appearances = [ItemAppearance(ItemType.WAND, material) for material in self.WAND_MATERIALS]
        
        self.appearance_map = {
            ItemType.SCROLL: self.scroll_appearances,
            ItemType.POTION: self.potion_appearances,
            ItemType.RING: self.ring_appearances,
            ItemType.AMULET: self.amulet_appearances,
            ItemType.WAND: self.wand_appearances,
        }

    def get_appearance(self, item_type: ItemType) -> Optional[str]:
        """Get a random unused appearance for an item type."""
        if item_type not in self.appearance_map:
            return None

        available = [app for app in self.appearance_map[item_type] if not app.is_used]
        if not available:
            return None

        chosen = random.choice(available)
        chosen.is_used = True
        return chosen.appearance

    def reset(self) -> None:
        """Reset all appearance usage states."""
        for appearances in self.appearance_map.values():
            for app in appearances:
                app.is_used = False


@dataclass
class Identifiable(SerializableComponent):
    """Component for items that can be identified."""

    # Class variables to track identified types across game sessions
    identified_types: ClassVar[Dict[str, bool]] = {}
    appearance_generator: ClassVar[AppearanceGenerator] = AppearanceGenerator()

    # Instance variables
    item_type: ItemType  # The type of item (e.g., SCROLL, POTION)
    true_name: str  # The actual name of the item
    appearance: str  # Random appearance (e.g., "pink potion", "scroll labeled 'XYZZY'")
    is_identified: bool = False
    was_tried: bool = False  # Whether the item has been tried/used

    def __post_init__(self):
        """Validate identification properties."""
        if not self.true_name:
            raise ValueError("True name must not be empty")
        if not self.appearance:
            self.appearance = self.appearance_generator.get_appearance(self.item_type) or "unknown"
        
        # If this type is already identified globally, mark this item as identified
        type_key = f"{self.item_type.name}:{self.true_name}"
        if type_key in self.identified_types:
            self.is_identified = self.identified_types[type_key]

    def identify(self) -> None:
        """Identify this item and all items of the same type."""
        type_key = f"{self.item_type.name}:{self.true_name}"
        self.is_identified = True
        self.identified_types[type_key] = True

    def try_item(self) -> None:
        """Mark the item as tried/used."""
        self.was_tried = True

    def get_name(self) -> str:
        """Get the appropriate name based on identification status."""
        if self.is_identified:
            return self.true_name
        
        type_desc = {
            ItemType.SCROLL: f"scroll labeled '{self.appearance}'",
            ItemType.POTION: f"{self.appearance} potion",
            ItemType.RING: f"{self.appearance} ring",
            ItemType.AMULET: f"{self.appearance} amulet",
            ItemType.WAND: f"{self.appearance} wand",
            ItemType.WEAPON: "weapon",
            ItemType.ARMOR: "armor"
        }
        
        base_name = type_desc.get(self.item_type, "unknown item")
        if self.was_tried:
            base_name = f"tried {base_name}"
        return base_name

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "__type__": self.__class__.__name__,
            "__module__": self.__class__.__module__,
            "data": {
                "item_type": self.item_type.name,
                "true_name": self.true_name,
                "appearance": self.appearance,
                "is_identified": self.is_identified,
                "was_tried": self.was_tried,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Identifiable":
        """Create from dictionary after deserialization."""
        component_data = data.get("data", data)
        return cls(
            item_type=ItemType[component_data["item_type"]],
            true_name=component_data["true_name"],
            appearance=component_data["appearance"],
            is_identified=bool(component_data.get("is_identified", False)),
            was_tried=bool(component_data.get("was_tried", False))
        )

    @classmethod
    def reset_identification(cls) -> None:
        """Reset all identification status (typically called when starting a new game)."""
        cls.identified_types.clear()
        cls.appearance_generator.reset() 