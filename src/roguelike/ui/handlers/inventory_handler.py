import tcod
from typing import Optional, TYPE_CHECKING

from roguelike.ui.screens.inventory_screen import InventoryScreen
from roguelike.world.entity.inventory import InventorySystem

if TYPE_CHECKING:
    from roguelike.game.engine import Engine

class InventoryHandler:
    def __init__(self, engine: 'Engine', action_type: str = "use"):
        self.engine = engine
        self.action_type = action_type
        self.screen = InventoryScreen(
            console=engine.console,
            world=engine.world,
            player=engine.player,
            action_type=action_type
        )
        
    def handle_events(self, event: tcod.event.Event) -> Optional[dict]:
        """イベント処理"""
        result = self.screen.handle_input(event)
        
        if result:
            action, item, quantity = result
            
            if action == "exit":
                return {"pop": True}
                
            inventory_system = InventorySystem(self.world)
            
            if action == "use":
                if quantity and quantity > 1:
                    # アイテムを分割して使用
                    new_item = inventory_system.split_item(self.engine.player, item, quantity)
                    if new_item:
                        inventory_system.use_item(self.engine.player, new_item)
                else:
                    inventory_system.use_item(self.engine.player, item)
                    
            elif action == "drop":
                if quantity and quantity > 1:
                    # アイテムを分割して捨てる
                    new_item = inventory_system.split_item(self.engine.player, item, quantity)
                    if new_item:
                        inventory_system.remove_item(self.engine.player, new_item)
                else:
                    inventory_system.remove_item(self.engine.player, item)
                    
            elif action == "split":
                if quantity and quantity > 1:
                    inventory_system.split_item(self.engine.player, item, quantity)
                    
            return {"pop": True}
            
        return None
        
    def render(self) -> None:
        """画面描画"""
        self.screen.render() 