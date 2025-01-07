#!/usr/bin/env python3
import traceback
from roguelike.core.engine import Engine

def main() -> None:
    engine = Engine()
    
    try:
        engine.initialize()
        
        # メインゲームループ
        while True:
            engine.render()
            
            if not engine.handle_events():
                break
                
            engine.update()
            
    except Exception:
        traceback.print_exc()
        
    finally:
        engine.cleanup()

if __name__ == "__main__":
    main() 