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

# Colors
class Colors:
    """Color constants."""
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    PURPLE = (255, 0, 255)
    CYAN = (0, 255, 255)
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
    GRAY = (128, 128, 128)
    DARK_GRAY = (64, 64, 64)
    LIGHT_GRAY = (192, 192, 192)
    LIGHT_BLUE = (173, 216, 230)
    LIGHT_CYAN = (224, 255, 255)
    SILVER = (192, 192, 192)
    VIOLET = (238, 130, 238)
    LIGHT_VIOLET = (255, 182, 255)
    LIGHT_PINK = (255, 182, 193)
    GOLD = (255, 215, 0)
    
    # Game specific colors
    PLAYER = (255, 255, 255)
    DARK_WALL = (0, 0, 100)
    DARK_GROUND = (50, 50, 150)
    LIGHT_WALL = (130, 110, 50)
    LIGHT_GROUND = (200, 180, 50)
    
    # UI colors
    UI_BAR_1 = (0x9B, 0x30, 0xFF)
    UI_BAR_2 = (0x0C, 0x00, 0x80)
    UI_BAR_3 = (0xFF, 0x30, 0x9B)
    UI_BAR_4 = (0x80, 0x00, 0x0C)
    UI_BAR_TEXT = (0xFF, 0xFF, 0xFF)
    UI_BAR_TEXT_SHADOW = (0x00, 0x00, 0x00)
    
    # Message colors
    MSG_INFO = (0xFF, 0xFF, 0x99)
    MSG_WARN = (0xFF, 0x99, 0x00)
    MSG_ERROR = (0xFF, 0x00, 0x00)
    MSG_DEBUG = (0x99, 0x99, 0x99)

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
AUTO_SAVE_INTERVAL = 100  # Number of turns between auto-saves
MAX_BACKUP_FILES = 5      # Maximum number of backup files to keep
BACKUP_ENABLED = True     # Whether to create backups when saving 