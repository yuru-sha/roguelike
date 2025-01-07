import tcod
from typing import Optional, List, Tuple, Callable

from roguelike.world.entity.components import Item, Inventory, Stackable, Name
from roguelike.ui.screens.quantity_selector import QuantitySelector

class InventoryScreen:
    def __init__(
        self,
        console: tcod.Console,
        world: 'esper.World',
        player: int,
        action_type: str = "use"
    ):
        self.console = console
        self.world = world
        self.player = player
        self.action_type = action_type  # "use", "drop", "split"
        self.selected_index = 0
        self.quantity_selector: Optional[QuantitySelector] = None
        
    def render(self) -> None:
        """インベントリ画面を描画"""
        inventory = self.world.component_for_entity(self.player, Inventory)
        
        # ウィンドウの枠を描画
        self.console.draw_frame(
            x=0,
            y=0,
            width=50,
            height=43,
            title="インベントリ",
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )
        
        if len(inventory.items) == 0:
            self.console.print(x=2, y=2, string="インベントリは空です。")
            return
            
        # アイテム一覧を表示
        for i, item in enumerate(inventory.items):
            name = self.world.component_for_entity(item, Name).name
            if self.world.has_component(item, Stackable):
                stack = self.world.component_for_entity(item, Stackable)
                name = f"{name} (x{stack.count})"
                
            color = (255, 255, 255) if i == self.selected_index else (200, 200, 200)
            self.console.print(x=2, y=2 + i, string=f"{chr(ord('a') + i)}) {name}", fg=color)
            
        # 操作説明を表示
        action_text = {
            "use": "使用",
            "drop": "捨てる",
            "split": "分割"
        }[self.action_type]
        help_text = f"↑↓: 選択 Enter: {action_text} Esc: キャンセル"
        self.console.print(x=2, y=40, string=help_text)
        
        # 数量選択画面が表示されている場合は描画
        if self.quantity_selector:
            self.quantity_selector.render()
            
    def handle_input(self, event: tcod.event.Event) -> Optional[Tuple[str, int, Optional[int]]]:
        """入力処理"""
        # 数量選択画面が表示されている場合はそちらの入力を処理
        if self.quantity_selector:
            result = self.quantity_selector.handle_input(event)
            if result:
                action, quantity = result
                self.quantity_selector = None
                if action == "selected":
                    selected_item = self.world.component_for_entity(
                        self.player, Inventory
                    ).items[self.selected_index]
                    return (self.action_type, selected_item, quantity)
                return None
            return None
            
        inventory = self.world.component_for_entity(self.player, Inventory)
        
        if isinstance(event, tcod.event.KeyDown):
            if event.sym == tcod.event.K_ESCAPE:
                return ("exit", 0, None)
                
            elif event.sym == tcod.event.K_UP:
                self.selected_index = (self.selected_index - 1) % len(inventory.items)
                
            elif event.sym == tcod.event.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(inventory.items)
                
            elif event.sym == tcod.event.K_RETURN:
                if len(inventory.items) > 0:
                    selected_item = inventory.items[self.selected_index]
                    # スタック可能なアイテムの場合は数量選択画面を表示
                    if (self.world.has_component(selected_item, Item) and 
                        self.world.component_for_entity(selected_item, Item).stackable):
                        stack = self.world.component_for_entity(selected_item, Stackable)
                        self.quantity_selector = QuantitySelector(
                            console=self.console,
                            x=10,
                            y=10,
                            width=30,
                            height=10,
                            title="数量選択",
                            max_quantity=stack.count,
                            callback=lambda x: None
                        )
                        return None
                    else:
                        return (self.action_type, selected_item, 1)
                        
        return None 