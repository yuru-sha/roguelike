from enum import Enum, auto
from typing import Final

# Screen dimensions
SCREEN_WIDTH: Final[int] = 80
SCREEN_HEIGHT: Final[int] = 50

# Map dimensions
MAP_WIDTH: Final[int] = 80
MAP_HEIGHT: Final[int] = 43

# Panel dimensions
PANEL_HEIGHT: Final[int] = 7
PANEL_Y: Final[int] = SCREEN_HEIGHT - PANEL_HEIGHT

# Message log
MSG_X: Final[int] = 1
MSG_WIDTH: Final[int] = MAP_WIDTH - 2
MSG_HEIGHT: Final[int] = PANEL_HEIGHT - 1

# Room generation
ROOM_MAX_SIZE: Final[int] = 10
ROOM_MIN_SIZE: Final[int] = 6
MAX_ROOMS: Final[int] = 30

# FOV settings
FOV_ALGORITHM: Final[int] = 0  # TCOD's default algorithm
FOV_LIGHT_WALLS: Final[bool] = True
FOV_RADIUS: Final[int] = 10

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
    WHITE: Final = (255, 255, 255)
    BLACK: Final = (0, 0, 0)
    RED: Final = (255, 0, 0)
    GREEN: Final = (0, 255, 0)
    YELLOW: Final = (255, 255, 0)
    BLUE: Final = (0, 0, 255)
    
    PLAYER: Final = (255, 255, 255)
    CORPSE: Final = (191, 0, 0)
    
    DARK_WALL: Final = (0, 0, 100)
    DARK_GROUND: Final = (50, 50, 150)
    LIGHT_WALL: Final = (130, 110, 50)
    LIGHT_GROUND: Final = (200, 180, 50)

# Entity settings
MAX_MONSTERS_PER_ROOM: Final[int] = 3
MAX_ITEMS_PER_ROOM: Final[int] = 2

# Experience and level-up
LEVEL_UP_BASE: Final[int] = 200
LEVEL_UP_FACTOR: Final[int] = 150

# Inventory
INVENTORY_WIDTH: Final[int] = 50
INVENTORY_HEIGHT: Final[int] = 50

# Debug/Wizard mode
WIZARD_MODE_PASSWORD: Final[str] = "wizard"  # Rogueと同じパスワード 