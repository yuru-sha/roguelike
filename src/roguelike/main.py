#!/usr/bin/env python3
"""
Main entry point for the roguelike game.
"""

import sys
import traceback
from pathlib import Path

import tcod
import tcod.console
import tcod.context
import tcod.libtcodpy

from roguelike.core.engine import Engine
from roguelike.utils.logging import GameLogger

logger = GameLogger.get_instance()


def main() -> None:
    """Main entry point for the game."""
    try:
        # Initialize logging
        logger.info("Starting game")

        # Initialize game engine
        engine = Engine()

        # Run game loop
        engine.run()

    except KeyboardInterrupt:
        logger.info("Game interrupted by user")
    except SystemExit:
        logger.info("Game exited normally")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        traceback.print_exc()
    finally:
        logger.info("Game terminated")


if __name__ == "__main__":
    main()
