import tcod
from typing import Optional

from roguelike.world.entity.components import Item, Inventory, Stackable, Name, Equipment

class InventoryScreen:
    def __init__(self, engine):
        self.engine = engine
        self.selected_index = 0
        self.show_details = False  # 詳細表示モードのフラグ
    
    def render(self, console: tcod.console.Console) -> None:
        """インベントリ画面を描画"""
        inventory = self.engine.world.component_for_entity(self.engine.player_entity, Inventory)
        
        if not inventory.items:
            self.engine.add_message("Your inventory is empty.")
            return
        
        # インベントリウィンドウの設定
        window_width = 50
        window_height = len(inventory.items) + 4  # 説明用に行を追加
        window_x = self.engine.screen_width // 2 - window_width // 2
        window_y = self.engine.screen_height // 2 - window_height // 2
        
        # ウィンドウの描画
        window = tcod.console.Console(window_width, window_height, order="F")
        window.draw_frame(
            x=0,
            y=0,
            width=window_width,
            height=window_height,
            title="Inventory",
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )
        
        # アイテム一覧の表示
        for i, item in enumerate(inventory.items):
            name = self.engine.world.component_for_entity(item, Name)
            key = chr(ord('a') + i)
            
            # アイテムの詳細情報を取得
            details = []
            
            # 重ね置き可能なアイテムの場合は個数を表示
            if (self.engine.world.has_component(item, Item) and 
                self.engine.world.component_for_entity(item, Item).stackable):
                stack = self.engine.world.component_for_entity(item, Stackable)
                details.append(f"x{stack.count}")
            
            # アイテムの状態を取得
            item_component = self.engine.world.component_for_entity(item, Item)
            
            # 未識別の場合は基本情報のみ表示
            if not item_component.identified:
                details.append("(unidentified)")
            else:
                # 装備品の場合
                if self.engine.world.has_component(item, Equipment):
                    equipment = self.engine.world.component_for_entity(item, Equipment)
                    if equipment.power_bonus != 0:
                        details.append(f"Power +{equipment.power_bonus}")
                    if equipment.defense_bonus != 0:
                        details.append(f"Defense +{equipment.defense_bonus}")
                    if equipment.is_equipped:
                        details.append("(equipped)")
                
                # 識別済みの場合は詳細情報を表示
                if item_component.weight > 0:
                    details.append(f"{item_component.weight:.1f}kg")
                if item_component.value > 0:
                    details.append(f"{item_component.value}G")
                
                # 祝福/呪いの状態を表示
                if item_component.state != ItemState.NORMAL:
                    state_text = {
                        ItemState.BLESSED: "(blessed)",
                        ItemState.CURSED: "(cursed)"
                    }[item_component.state]
                    details.append(state_text)
            
            # 詳細情報を結合
            detail_text = ", ".join(details)
            if detail_text:
                text = f"{key}) {name.name:<15} - {detail_text}"
            else:
                text = f"{key}) {name.name}"
            
            # 選択中のアイテムは強調表示
            color = (255, 255, 255) if i == self.selected_index else (128, 128, 128)
            window.print(x=1, y=i+1, string=text, fg=color)
        
        # 選択中のアイテムの説明文を表示
        if self.show_details and inventory.items:
            selected_item = inventory.items[self.selected_index]
            item_component = self.engine.world.component_for_entity(selected_item, Item)
            if item_component.identified and item_component.description:
                description = item_component.description
                # 説明文を折り返して表示
                y = len(inventory.items) + 2
                for line in self._wrap_text(description, window_width - 2):
                    window.print(x=1, y=y, string=line, fg=(200, 200, 200))
                    y += 1
        
        # 操作説明を表示
        help_text = "↑↓: Select  Enter: Use  Tab: Details  Esc: Cancel"
        window.print(x=1, y=window_height-1, string=help_text)
        
        # メインコンソールにウィンドウを合成
        window.blit(
            dest=console,
            dest_x=window_x,
            dest_y=window_y,
            src_x=0,
            src_y=0,
            width=window_width,
            height=window_height,
            fg_alpha=1.0,
            bg_alpha=0.7,
        )
    
    def handle_input(self, event: tcod.event.KeyDown) -> Optional[str]:
        """キー入力の処理"""
        inventory = self.engine.world.component_for_entity(self.engine.player_entity, Inventory)
        
        if not inventory.items:
            return None
        
        if event.sym == tcod.event.KeySym.ESCAPE:
            return "exit"
        
        elif event.sym == tcod.event.KeySym.UP:
            self.selected_index = (self.selected_index - 1) % len(inventory.items)
        
        elif event.sym == tcod.event.KeySym.DOWN:
            self.selected_index = (self.selected_index + 1) % len(inventory.items)
        
        elif event.sym == tcod.event.KeySym.TAB:
            self.show_details = not self.show_details
        
        elif event.sym == tcod.event.KeySym.RETURN:
            selected_item = inventory.items[self.selected_index]
            return f"use_{selected_item}"
        
        return None
    
    def _wrap_text(self, text: str, width: int) -> list[str]:
        """テキストを指定幅で折り返す"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            if current_length + word_length + 1 <= width:
                current_line.append(word)
                current_length += word_length + 1
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_length = word_length + 1
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines 