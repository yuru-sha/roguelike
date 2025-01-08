import pytest
import tcod
from tcod.event import KeyDown, MouseButtonDown, Event

from roguelike.ui.handlers.input_handler import InputHandler
from roguelike.core.constants import GameStates

class MockEvent:
    """Mock event class for testing."""
    def __init__(self, event_type: str, **kwargs):
        self.type = event_type
        for key, value in kwargs.items():
            setattr(self, key, value)

def test_input_handler_initialization():
    """Test InputHandler initialization."""
    handler = InputHandler()
    assert handler.key_actions is not None
    assert len(handler.key_actions) > 0

def test_movement_keys():
    """Test movement key handling."""
    handler = InputHandler()
    
    # Test arrow keys
    result = handler._handle_player_turn_keys(tcod.event.K_UP)
    assert result == {'action': 'move_north'}
    
    result = handler._handle_player_turn_keys(tcod.event.K_DOWN)
    assert result == {'action': 'move_south'}
    
    result = handler._handle_player_turn_keys(tcod.event.K_LEFT)
    assert result == {'action': 'move_west'}
    
    result = handler._handle_player_turn_keys(tcod.event.K_RIGHT)
    assert result == {'action': 'move_east'}
    
    # Test vi keys
    result = handler._handle_player_turn_keys(tcod.event.K_k)
    assert result == {'action': 'move_north'}
    
    result = handler._handle_player_turn_keys(tcod.event.K_j)
    assert result == {'action': 'move_south'}
    
    result = handler._handle_player_turn_keys(tcod.event.K_h)
    assert result == {'action': 'move_west'}
    
    result = handler._handle_player_turn_keys(tcod.event.K_l)
    assert result == {'action': 'move_east'}

def test_action_keys():
    """Test action key handling."""
    handler = InputHandler()
    
    # Test pickup
    result = handler._handle_player_turn_keys(tcod.event.K_g)
    assert result == {'action': 'pickup'}
    
    # Test inventory
    result = handler._handle_player_turn_keys(tcod.event.K_i)
    assert result == {'action': 'show_inventory'}
    
    # Test drop
    result = handler._handle_player_turn_keys(tcod.event.K_d)
    assert result == {'action': 'drop_inventory'}

def test_inventory_keys():
    """Test inventory screen key handling."""
    handler = InputHandler()
    
    # Test item selection (a-z)
    for i in range(26):
        key = tcod.event.K_a + i
        result = handler._handle_inventory_keys(key)
        assert result == {'action': 'inventory_index', 'inventory_index': i}
    
    # Test escape
    result = handler._handle_inventory_keys(tcod.event.K_ESCAPE)
    assert result == {'action': 'exit'}

def test_targeting_keys():
    """Test targeting mode key handling."""
    handler = InputHandler()
    
    # Test escape
    result = handler._handle_targeting_keys(tcod.event.K_ESCAPE)
    assert result == {'action': 'exit'}

def test_mouse_handling():
    """Test mouse input handling."""
    handler = InputHandler()
    
    # Test left click in targeting mode
    event = MockEvent('MOUSEBUTTONDOWN', button=tcod.event.BUTTON_LEFT, tile=type('Tile', (), {'x': 10, 'y': 10}))
    result = handler._handle_mouse(event, GameStates.TARGETING)
    assert result == {'action': 'left_click', 'position': (10, 10)}
    
    # Test right click in targeting mode
    event = MockEvent('MOUSEBUTTONDOWN', button=tcod.event.BUTTON_RIGHT)
    result = handler._handle_mouse(event, GameStates.TARGETING)
    assert result == {'action': 'right_click'}
    
    # Test mouse input in other game states
    event = MockEvent('MOUSEBUTTONDOWN', button=tcod.event.BUTTON_LEFT)
    result = handler._handle_mouse(event, GameStates.PLAYERS_TURN)
    assert result is None 