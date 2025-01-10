"""
The main game engine class that coordinates all game systems.
"""

import os
import sys
import psutil
from pathlib import Path
from typing import Any, Dict, Optional

import esper
import tcod
import tcod.event

from roguelike.core.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, Colors
)
from roguelike.core.event import EventManager, Event, EventType
from roguelike.game.achievements import AchievementManager
from roguelike.ui.renderer import GameRenderer
from roguelike.ui.screen_manager import ScreenManager
from roguelike.game.states.game_state import GameState, GameStates
from roguelike.game.systems.combat import CombatSystem
from roguelike.game.actions.base import (
    MovementAction,
    ItemAction,
    UseItemAction,
    UseStairsAction,
    SearchAction,
    ReadAction,
    ThrowAction,
    ZapAction,
    IdentifyAction,
    DropAction,
    PickupAction,
)
from roguelike.world.map.map_manager import MapManager
from roguelike.data.save_manager import SaveManager
from roguelike.ui.handlers.input_handler import InputHandler
from roguelike.utils.game_logger import GameLogger
from roguelike.game.actions.handler import ActionHandler

logger = GameLogger.get_instance()

class Engine:
    """The main game engine class that coordinates all game systems."""

    def __init__(self, skip_lock_check: bool = False):
        """Initialize the game engine."""
        logger.info("Initializing game engine")

        # Check for existing game process
        if not skip_lock_check:
            current_process = psutil.Process()
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    if proc.pid != current_process.pid:
                        cmdline = proc.cmdline()
                        if len(cmdline) >= 2 and 'python' in cmdline[0] and 'roguelike' in cmdline[1]:
                            logger.error("Game is already running")
                            raise RuntimeError("Another instance of the game is already running")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

        # Get the project root directory
        project_root = Path(__file__).parents[3]
        assets_path = project_root / "data" / "assets" / "dejavu10x10_gs_tc.png"

        # Initialize event system
        self.event_manager = EventManager.get_instance()
        
        # Initialize achievement system
        self.achievement_manager = AchievementManager.get_instance()

        # Initialize TCOD
        self.root_console = tcod.console.Console(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.context = tcod.context.new(
            columns=SCREEN_WIDTH,
            rows=SCREEN_HEIGHT,
            title="Roguelike",
            tileset=tcod.tileset.load_tilesheet(
                str(assets_path), 32, 8, tcod.tileset.CHARMAP_TCOD
            ),
            vsync=True,
        )

        # Initialize game state
        self.game_state = GameState()
        
        # Initialize ECS world
        self.world = esper.World()

        # Initialize systems
        self.renderer = GameRenderer(self.root_console)
        self.screen_manager = ScreenManager(self.root_console, self.game_state)
        self.input_handler = InputHandler()
        self.combat_system = CombatSystem(self.world, self.game_state)
        self.map_manager = MapManager(self.world, self.game_state)
        self.action_handler = ActionHandler(self.world, self.game_state, self.combat_system, self.map_manager)
        self.save_manager = SaveManager(self.world, self.game_state, self.map_manager)

        # Game state flags
        self.running = True

    def new_game(self) -> None:
        """Start a new game."""
        logger.info("Starting new game")
        self.map_manager.initialize_new_game()
        self.event_manager.publish(Event(
            EventType.MESSAGE_LOG,
            {"message": "Welcome to the Roguelike! Prepare to die...", "color": Colors.WHITE}
        ))

    def quit_game(self) -> None:
        """Clean up and quit the game."""
        try:
            # Save event log
            self.event_manager.save_event_log()

            # Clean up
            self.cleanup()
            self.running = False
            logger.info("Game quit successfully")

        except Exception as e:
            logger.error(f"Error quitting game: {e}")
            raise

    def cleanup(self) -> None:
        """Clean up resources before exiting."""
        logger.info("Cleaning up resources")
        if self.context:
            self.context.close()

    def handle_action(self, action: Dict[str, Any]) -> None:
        """Handle a game action."""
        try:
            action_type = action.get("action")
            logger.debug(f"Handling action: {action_type}")

            if action_type == "move":
                dx = action.get("dx", 0)
                dy = action.get("dy", 0)
                movement = MovementAction(dx=dx, dy=dy)
                movement.perform(self)
                self.save_manager.check_auto_save()
            elif action_type == "pickup":
                pickup = PickupAction(item_id=0)  # Item ID will be determined in handler
                pickup.perform(self)
                self.save_manager.check_auto_save()
            elif action_type == "use_item":
                item_id = action.get("item_id")
                target_pos = action.get("target_pos")
                use_item = UseItemAction(item_id=item_id, target_pos=target_pos)
                use_item.perform(self)
                self.save_manager.check_auto_save()
            elif action_type == "use_stairs":
                stairs = UseStairsAction()
                stairs.perform(self)
                self.save_manager.check_auto_save()
            elif action_type == "save_game":
                self.screen_manager.switch_to_save_screen()
            elif action_type == "load_game":
                self.screen_manager.switch_to_load_screen()
            elif action_type == "achievements":
                self.screen_manager.switch_to_achievements_screen()
            elif action_type == "select":
                if self.game_state.state == GameStates.SAVE_GAME:
                    slot = self.screen_manager.current_screen.selected_slot
                    if self.save_manager.save_game(slot):
                        self.screen_manager.return_to_game()
                elif self.game_state.state == GameStates.LOAD_GAME:
                    slot = self.screen_manager.current_screen.selected_slot
                    if self.save_manager.load_game(slot):
                        self.event_manager.publish(Event(
                            EventType.MESSAGE_LOG,
                            {"message": f"Game loaded from slot {slot}", "color": Colors.GREEN}
                        ))
                        self.screen_manager.return_to_game()
                    else:
                        self.event_manager.publish(Event(
                            EventType.MESSAGE_LOG,
                            {"message": "Failed to load game", "color": Colors.RED}
                        ))
            elif action_type == "move_cursor":
                if self.screen_manager.current_screen:
                    self.screen_manager.current_screen.move_cursor(action.get("dy", 0))
            elif action_type == "exit":
                if self.game_state.state in (GameStates.SAVE_GAME, GameStates.LOAD_GAME, GameStates.ACHIEVEMENTS):
                    self.screen_manager.return_to_game()
                else:
                    self.quit_game()
                    return

            # Update FOV after any action
            self.map_manager.recompute_fov()

        except Exception as e:
            logger.error(f"Error handling action {action}: {str(e)}", exc_info=True)
            self.event_manager.publish(Event(
                EventType.MESSAGE_LOG,
                {"message": f"Error: {str(e)}", "color": Colors.RED}
            ))
            raise

    def run(self) -> None:
        """Run the game loop."""
        logger.info("Starting game loop")

        try:
            # Start new game
            self.new_game()

            while self.running:
                try:
                    # Render the current screen
                    self.screen_manager.render(self.world, self.map_manager, self.renderer)

                    # Present the console
                    self.context.present(self.root_console)

                    # Handle events
                    for event in tcod.event.wait():
                        try:
                            # Convert event coordinates
                            event = self.context.convert_event(event)

                            # Handle window close button
                            if isinstance(event, tcod.event.Quit):
                                logger.info("Window close event received")
                                self.quit_game()
                                break

                            # Handle input
                            action = self.input_handler.handle_input(
                                event, self.game_state.state
                            )
                            if action:
                                self.handle_action(action)

                            if not self.running:
                                break

                        except Exception as e:
                            logger.error(f"Error handling event: {str(e)}", exc_info=True)
                            raise

                except Exception as e:
                    logger.error(f"Error in game loop: {str(e)}", exc_info=True)
                    raise

        except Exception as e:
            logger.error(f"Fatal error in game loop: {str(e)}", exc_info=True)
            raise

        finally:
            self.cleanup()

    def load_game(self, slot: int) -> bool:
        """Load a saved game.
        
        Args:
            slot: The save slot to load from
            
        Returns:
            True if the game was loaded successfully, False otherwise
        """
        if self.save_manager.load_game(slot):
            # Load achievements
            save_dir = Path(__file__).parents[3] / "data" / "saves"
            self.achievement_manager.load_achievements(save_dir)
            return True
        return False
