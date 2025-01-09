"""
Game constants.
"""

from enum import Enum, auto

# Screen dimensions
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

# Map dimensions
MAP_WIDTH = 80
MAP_HEIGHT = 43

# Room generation
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

# Field of View
FOV_ALGORITHM = 0  # Default FOV algorithm
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

# Message log
MESSAGE_X = 21
MESSAGE_WIDTH = 40
MESSAGE_HEIGHT = 5

# Panel
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

# Inventory
INVENTORY_WIDTH = 50

# Level up
LEVEL_SCREEN_WIDTH = 40
CHARACTER_SCREEN_WIDTH = 30


# Game states
class GameStates(Enum):
    PLAYERS_TURN = auto()
    ENEMY_TURN = auto()
    PLAYER_DEAD = auto()
    SHOW_INVENTORY = auto()
    DROP_INVENTORY = auto()
    TARGETING = auto()
    LEVEL_UP = auto()
    CHARACTER_SCREEN = auto()


# Equipment slots
class EquipmentSlot(Enum):
    """Equipment slot types."""

    # Armor slots
    HEAD = 1  # Head armor
    BODY = 2  # Body armor
    ARMS = 3  # Arm armor
    LEGS = 4  # Leg armor
    FEET = 5  # Foot armor
    CLOAK = 6  # Cloak

    # Weapon slots
    MAIN_HAND = 11  # Main hand (weapon)
    OFF_HAND = 12  # Off hand (shield etc.)

    # Accessory slots
    NECK = 21  # Necklace
    RING_LEFT = 22  # Left hand ring
    RING_RIGHT = 23  # Right hand ring

    # Special slots
    AMULET = 31  # Amulet of Yendor (special item)

    @classmethod
    def from_value(cls, value: int) -> "EquipmentSlot":
        """Get EquipmentSlot from integer value."""
        for slot in cls:
            if slot.value == value:
                return slot
        raise ValueError(f"No EquipmentSlot with value {value}")

    @classmethod
    def from_str(cls, value: str) -> "EquipmentSlot":
        """Get EquipmentSlot from string value."""
        try:
            # Try to parse as integer first
            slot_value = int(value)
            return cls.from_value(slot_value)
        except ValueError:
            # If not an integer, try as enum name
            try:
                return cls[value]
            except KeyError:
                raise ValueError(f"Invalid EquipmentSlot value: {value}")

    @classmethod
    def from_name(cls, name: str) -> "EquipmentSlot":
        """Get EquipmentSlot from name string.

        Args:
            name: The name of the equipment slot (e.g. 'HEAD', 'BODY')

        Returns:
            The corresponding EquipmentSlot enum value

        Raises:
            ValueError: If the name is not a valid equipment slot name
        """
        try:
            return cls[name]
        except KeyError:
            raise ValueError(f"Invalid equipment slot name: {name}")


# Weapon types
class WeaponType(Enum):
    """Weapon types."""

    ONE_HANDED = 1  # One-handed weapon
    TWO_HANDED = 2  # Two-handed weapon
    BOW = 3  # Bow


# Colors
class Colors:
    """Color constants."""

    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    VIOLET = (127, 0, 255)
    LIGHT_BLUE = (0, 191, 255)
    LIGHT_CYAN = (224, 255, 255)
    LIGHT_GRAY = (192, 192, 192)
    LIGHT_PINK = (255, 182, 193)
    GRAY = (128, 128, 128)
    DARK_GRAY = (64, 64, 64)
    ORANGE = (255, 128, 0)
    BROWN = (165, 42, 42)
    DARK_RED = (128, 0, 0)
    DARK_GREEN = (0, 128, 0)
    DARK_BLUE = (0, 0, 128)
    DARK_YELLOW = (128, 128, 0)
    DARK_PURPLE = (128, 0, 128)
    DARK_CYAN = (0, 128, 128)
    DARK_ORANGE = (128, 64, 0)
    DARK_BROWN = (82, 21, 21)
    PURPLE = (255, 0, 255)
    CYAN = (0, 255, 255)
    SILVER = (192, 192, 192)
    GOLD = (255, 215, 0)

    # Combat colors
    PLAYER_ATK = (255, 255, 0)  # Yellow
    ENEMY_ATK = (255, 128, 0)  # Orange
    ENEMY_DIE = (255, 64, 64)  # Light red
    PLAYER_DIE = (255, 0, 0)  # Red

    # UI colors
    UI_BORDER = (128, 128, 128)
    UI_BG = (0, 0, 0)
    UI_TEXT = (255, 255, 255)
    UI_TEXT_DISABLED = (128, 128, 128)
    UI_BAR_TEXT = (255, 255, 255)
    UI_BAR_FILLED = (0, 255, 0)
    UI_BAR_EMPTY = (128, 0, 0)

    # Map colors
    WELCOME_TEXT = (128, 128, 255)
    WALL_FG = (128, 128, 128)
    WALL_BG = (0, 0, 100)
    GROUND_FG = (64, 64, 64)
    GROUND_BG = (0, 0, 0)
    STAIRS_FG = (255, 255, 0)
    STAIRS_BG = (0, 0, 0)

    # Map lighting
    LIGHT_WALL = (130, 110, 50)
    LIGHT_GROUND = (200, 180, 50)
    DARK_WALL = (0, 0, 100)
    DARK_GROUND = (50, 50, 150)


# Entity settings
MAX_MONSTERS_PER_ROOM = 3
MAX_ITEMS_PER_ROOM = 2

# Player initial stats
PLAYER_HP = 30
PLAYER_DEFENSE = 2
PLAYER_POWER = 5
PLAYER_XP = 0
PLAYER_INVENTORY_CAPACITY = 26

# Experience and level-up
LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150

# Wizard mode
WIZARD_MODE_PASSWORD = "wizard"

# Save settings
SAVE_VERSION = "1.0.0"
AUTO_SAVE_INTERVAL = 100
MAX_BACKUP_FILES = 5
BACKUP_ENABLED = True
