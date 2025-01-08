"""
Game constants.
"""

from enum import Enum, auto

# TODO: Add configuration file support
# TODO: Add difficulty level settings
# FIXME: Some constants should be calculated based on screen size
# OPTIMIZE: Color definitions could be cached
# WARNING: Some game balance constants might need adjustment
# REVIEW: Consider if more constants should be configurable
# HACK: Some magic numbers should be explained or renamed

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
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    MAGENTA = (255, 0, 255)
    CYAN = (0, 255, 255)
    
    # Light colors
    LIGHT_RED = (255, 127, 127)
    LIGHT_GREEN = (127, 255, 127)
    LIGHT_BLUE = (127, 127, 255)
    LIGHT_YELLOW = (255, 255, 127)
    LIGHT_MAGENTA = (255, 127, 255)
    LIGHT_CYAN = (127, 255, 255)
    LIGHT_GRAY = (192, 192, 192)
    
    # Dark colors
    DARK_RED = (127, 0, 0)
    DARK_GREEN = (0, 127, 0)
    DARK_BLUE = (0, 0, 127)
    DARK_YELLOW = (127, 127, 0)
    DARK_MAGENTA = (127, 0, 127)
    DARK_CYAN = (0, 127, 127)
    DARK_GRAY = (64, 64, 64)
    
    # Browns
    BROWN = (165, 42, 42)
    LIGHT_BROWN = (210, 105, 30)
    DARK_BROWN = (101, 67, 33)
    
    # Game specific colors
    PLAYER = WHITE
    DARK_WALL = DARK_GRAY
    LIGHT_WALL = LIGHT_GRAY
    DARK_GROUND = (50, 50, 150)
    LIGHT_GROUND = (200, 180, 50)
    VIOLET = (238, 130, 238)

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