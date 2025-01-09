import pytest

from roguelike.core.constants import WIZARD_MODE_PASSWORD, Colors, GameStates
from roguelike.game.states.game_state import GameState, Message


def test_game_state_initialization():
    """Test GameState initialization."""
    state = GameState()
    assert state.state == GameStates.PLAYERS_TURN
    assert state.dungeon_level == 1
    assert len(state.game_messages) == 0
    assert state.targeting_item is None
    assert not state.wizard_mode


def test_add_message():
    """Test adding messages to the game state."""
    state = GameState()

    # Add a message
    state.add_message("Test message", Colors.WHITE)
    assert len(state.game_messages) == 1
    assert state.game_messages[0].text == "Test message"
    assert state.game_messages[0].color == Colors.WHITE

    # Add multiple messages
    state.add_message("Second message", Colors.RED)
    assert len(state.game_messages) == 2
    assert state.game_messages[1].text == "Second message"
    assert state.game_messages[1].color == Colors.RED


def test_targeting_mode():
    """Test targeting mode state changes."""
    state = GameState()

    # Enter targeting mode
    state.enter_targeting_mode(1)
    assert state.state == GameStates.TARGETING
    assert state.targeting_item == 1

    # Exit targeting mode
    state.exit_targeting_mode()
    assert state.state == GameStates.PLAYERS_TURN
    assert state.targeting_item is None


def test_next_level():
    """Test advancing to next dungeon level."""
    state = GameState()
    initial_level = state.dungeon_level

    state.next_level()
    assert state.dungeon_level == initial_level + 1


def test_wizard_mode():
    """Test wizard mode toggling."""
    state = GameState()

    # Test with incorrect password
    assert not state.toggle_wizard_mode("wrong_password")
    assert not state.wizard_mode

    # Test with correct password
    assert state.toggle_wizard_mode(WIZARD_MODE_PASSWORD)
    assert state.wizard_mode

    # Test toggling off
    assert state.toggle_wizard_mode(WIZARD_MODE_PASSWORD)
    assert not state.wizard_mode


def test_save_and_load_game():
    """Test game state serialization."""
    state = GameState()

    # Add some test data
    state.add_message("Test message", Colors.WHITE)
    state.next_level()
    state.toggle_wizard_mode(WIZARD_MODE_PASSWORD)

    # Save state
    saved_data = state.save_game()

    # Create new state from saved data
    loaded_state = GameState.load_game(saved_data)

    # Verify loaded state matches original
    assert loaded_state.state == state.state
    assert loaded_state.dungeon_level == state.dungeon_level
    assert loaded_state.wizard_mode == state.wizard_mode
    assert len(loaded_state.game_messages) == len(state.game_messages)

    # Check message content
    for orig_msg, loaded_msg in zip(state.game_messages, loaded_state.game_messages):
        assert loaded_msg.text == orig_msg.text
        assert loaded_msg.color == orig_msg.color
