import tcod
from typing import Tuple, Optional, Callable

class QuantitySelector:
    def __init__(
        self,
        console: tcod.Console,
        x: int,
        y: int,
        width: int,
        height: int,
        title: str,
        max_quantity: int,
        callback: Callable[[int], None]
    ):
        self.console = console
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.title = title
        self.max_quantity = max_quantity
        self.current_quantity = max_quantity
        self.callback = callback
        
    def render(self) -> None:
        """数量選択画面を描画"""
        # ウィンドウの枠を描画
        self.console.draw_frame(
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
            title=self.title,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )
        
        # 現在の数量を表示
        quantity_text = f"数量: {self.current_quantity}"
        x = self.x + (self.width - len(quantity_text)) // 2
        self.console.print(x=x, y=self.y + 2, string=quantity_text)
        
        # 操作説明を表示
        help_text = "↑↓: 数量変更 Enter: 決定 Esc: キャンセル"
        x = self.x + (self.width - len(help_text)) // 2
        self.console.print(x=x, y=self.y + self.height - 2, string=help_text)
        
    def handle_input(self, event: tcod.event.Event) -> Optional[Tuple[str, int]]:
        """入力処理"""
        if isinstance(event, tcod.event.KeyDown):
            if event.sym == tcod.event.K_ESCAPE:
                return ("cancelled", 0)
            elif event.sym == tcod.event.K_RETURN:
                self.callback(self.current_quantity)
                return ("selected", self.current_quantity)
            elif event.sym == tcod.event.K_UP:
                self.current_quantity = min(self.current_quantity + 1, self.max_quantity)
                return None
            elif event.sym == tcod.event.K_DOWN:
                self.current_quantity = max(self.current_quantity - 1, 1)
                return None
            
        return None 