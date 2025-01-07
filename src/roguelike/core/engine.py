import tcod
import numpy as np
from typing import Optional, Tuple, Union

from roguelike.world.map.dungeon import generate_dungeon
from roguelike.world.map.game_map import GameMap
from roguelike.utils.logger import logger

class Engine:
    def __init__(self) -> None:
        logger.info("Initializing game engine")
        # 画面レイアウト
        self.screen_width = 80
        self.screen_height = 50  # 標準的なサイズ
        
        # 各領域のサイズ
        self.map_width = 80
        self.map_height = 43  # マップ領域
        self.status_height = 1  # ステータス表示領域
        self.message_height = 5  # メッセージ表示領域
        
        # メッセージ管理
        self.messages = []
        self.max_messages = 5  # 最大5件のメッセージを保持
        
        # プレイヤーの位置
        self.player_x = 0
        self.player_y = 0
        
        # マップ
        self.game_map = None
        
        # FOV
        self.fov_recompute = True
        self.visible = None
        
        # キー設定
        self.MOVE_KEYS = {
            # Vi keys
            tcod.event.KeySym.h: (-1, 0),  # 左
            tcod.event.KeySym.j: (0, 1),   # 下
            tcod.event.KeySym.k: (0, -1),  # 上
            tcod.event.KeySym.l: (1, 0),   # 右
            tcod.event.KeySym.y: (-1, -1), # 左上
            tcod.event.KeySym.u: (1, -1),  # 右上
            tcod.event.KeySym.b: (-1, 1),  # 左下
            tcod.event.KeySym.n: (1, 1),   # 右下
            # Arrow keys
            tcod.event.KeySym.LEFT: (-1, 0),
            tcod.event.KeySym.RIGHT: (1, 0),
            tcod.event.KeySym.UP: (0, -1),
            tcod.event.KeySym.DOWN: (0, 1),
        }
        
        self.ACTION_KEYS = {
            tcod.event.KeySym.ESCAPE: "quit",
        }
    
    def initialize(self) -> None:
        """ゲームの初期化"""
        logger.info("Loading game assets")
        
        # フォントの設定
        tileset = tcod.tileset.load_tilesheet(
            "src/roguelike/assets/dejavu10x10_gs_tc.png",
            32, 8, tcod.tileset.CHARMAP_TCOD,
        )
        
        # コンソールの初期化（C-orderに変更）
        self.console = tcod.console.Console(self.screen_width, self.screen_height, order="C")
        self.context = tcod.context.new(
            columns=self.console.width,
            rows=self.console.height,
            tileset=tileset,
            title="Roguelike",
        )
        
        logger.info("Generating dungeon")
        # ダンジョンの生成
        self.game_map, (self.player_x, self.player_y) = generate_dungeon(
            map_width=80,
            map_height=43,
            max_rooms=20,
            room_min_size=6,
            room_max_size=10,
        )
        
        # FOVの初期化
        self.visible = np.zeros((self.game_map.height, self.game_map.width), dtype=bool)
        
        # Welcomeメッセージ
        self.add_message("Hello Stranger, welcome to the Dungeons of Doom!")
        self.add_message("Your quest is to retrieve the Amulet of Yendor.")
        self.add_message("Press '?' for help.")
    
    def render(self) -> None:
        """画面の描画"""
        # FOVの再計算
        if self.fov_recompute:
            self.visible = self.game_map.compute_fov(self.player_x, self.player_y)
            self.fov_recompute = False
        
        # コンソールをクリア
        self.console.clear()
        
        # マップの描画（上部）
        self.game_map.render(self.console, self.visible)
        
        # プレイヤーの描画
        self.console.ch[self.player_y, self.player_x] = ord("@")
        self.console.fg[self.player_y, self.player_x] = (255, 255, 255)
        
        # ステータス情報の表示（枠なし）
        status_y = self.map_height
        status_text = f"HP: 100/100  Floor: 1  Turn: 0"
        self.console.print(x=0, y=status_y, string=status_text, fg=(255, 255, 255))
        
        # メッセージの表示（枠なし、最新5件）
        message_y = status_y + self.status_height
        for i, message in enumerate(self.messages[-self.message_height:]):
            self.console.print(x=0, y=message_y + i, string=message, fg=(255, 255, 255))
        
        # 画面の更新
        self.context.present(self.console)
    
    def update(self) -> None:
        """ゲームの状態更新"""
        pass
    
    def handle_events(self) -> bool:
        """イベント処理"""
        for event in tcod.event.wait():
            action = self.handle_action(event)
            
            if action is None:
                continue
            
            if action == "quit":
                logger.info("Quit action triggered")
                return False
            
            if isinstance(action, tuple):
                dx, dy = action
                new_x = self.player_x + dx
                new_y = self.player_y + dy
                
                # 移動先が歩行可能な場合のみ移動
                if 0 <= new_x < self.map_width and 0 <= new_y < self.map_height:
                    if self.game_map.walkable[new_y, new_x]:
                        logger.debug(f"Player moving from ({self.player_x}, {self.player_y}) to ({new_x}, {new_y})")
                        self.player_x = new_x
                        self.player_y = new_y
                        self.fov_recompute = True
                        
        return True
    
    def handle_action(self, event) -> Optional[Union[str, Tuple[int, int]]]:
        """イベントからアクションを決定する"""
        if isinstance(event, tcod.event.Quit):
            return "quit"
        
        if not isinstance(event, tcod.event.KeyDown):
            return None
        
        key = event.sym
        
        if key in self.MOVE_KEYS:
            return self.MOVE_KEYS[key]
        
        if key == tcod.event.KeySym.ESCAPE:
            return "quit"
        
        return None
    
    def cleanup(self) -> None:
        """終了処理"""
        logger.info("Cleaning up game resources")
        self.context.close()
    
    def add_message(self, text: str) -> None:
        """メッセージを追加する"""
        self.messages.append(text)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
        logger.debug(f"Added message: {text}") 