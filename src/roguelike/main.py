import sys
import traceback
from pathlib import Path

import tcod

from roguelike.core.engine import Engine
from roguelike.utils.logging import GameLogger

logger = GameLogger.get_instance()

def main() -> None:
    """Main entry point for the game."""
    try:
        logger.info("Starting game")
        
        # Create data directories if they don't exist
        data_dir = Path("data")
        for subdir in ["fonts", "saves"]:
            (data_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        # Copy font file if it doesn't exist
        font_file = data_dir / "fonts" / "dejavu10x10_gs_tc.png"
        if not font_file.exists():
            import shutil
            import pkg_resources
            
            font_source = pkg_resources.resource_filename(
                "roguelike",
                "assets/dejavu10x10_gs_tc.png"
            )
            shutil.copy(font_source, font_file)
        
        # Initialize and run the game
        engine = Engine()
        engine.new_game()
        
        while True:
            engine.render()
            engine.update()
            
    except KeyboardInterrupt:
        logger.info("Game terminated by user")
        sys.exit(0)
        
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}")
        logger.critical(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 