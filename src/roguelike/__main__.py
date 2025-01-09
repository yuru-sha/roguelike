#!/usr/bin/env python3
"""
Roguelike Game Entry Point
"""
import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from roguelike.core.engine import Engine
from roguelike.utils.game_logger import setup_logging

def main():
    """Main entry point for the game."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Roguelike game...")

    try:
        # Create and run the game engine
        engine = Engine()
        engine.run()
    except Exception as e:
        logger.exception("An error occurred while running the game: %s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Game terminated by user.")
        sys.exit(0)

if __name__ == "__main__":
    main() 