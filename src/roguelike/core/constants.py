"""
Game constants.
"""

from enum import Enum, auto

# Screen dimensions
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

# Map dimensions
MAP_WIDTH = 80
MAP_HEIGHT = 50

# Room generation
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

# Field of view
TORCH_RADIUS = 10

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

# Colors
class Colors:
    """Color constants."""
    # Map colors
    DARK_WALL = (0, 0, 100)
    DARK_GROUND = (50, 50, 150)
    LIGHT_WALL = (130, 110, 50)
    LIGHT_GROUND = (200, 180, 50)
    
    # Entity colors
    PLAYER = (255, 255, 255)  # White
    ORC = (63, 127, 63)       # Green
    TROLL = (0, 127, 0)       # Darker green
    
    # UI colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    MAGENTA = (255, 0, 255)
    CYAN = (0, 255, 255)
    LIGHT_CYAN = (128, 255, 255)  # For item messages

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

# Inventory
INVENTORY_WIDTH = 50
INVENTORY_HEIGHT = 3

# Wizard mode
WIZARD_MODE_PASSWORD = "wizard" 