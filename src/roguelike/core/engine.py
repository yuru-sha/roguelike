import tcod
import numpy as np
import esper
from typing import Optional, Tuple, Union

from roguelike.world.map.dungeon import generate_dungeon
from roguelike.world.map.game_map import GameMap
from roguelike.world.entity.factory import EntityFactory
from roguelike.world.entity.systems import EntitySystem
from roguelike.world.entity.ai import AISystem
from roguelike.world.entity.components import Position
from roguelike.utils.logger import logger

class Engine:
    def __init__(self) -> None:
        logger.info("Initializing game engine")
        # 画面レイアウト
        self.screen_width = 80
        self.screen_height = 50
        
        # 各領域のサイズ
        self.map_width = 80
        self.map_height = 43
        self.status_height = 1
        self.message_height = 5
        
        # メッセージ管理
        self.messages = []
        self.max_messages = 5
        
        # ECS
        self.world = esper.World()
        self.entity_factory = EntityFactory(self.world)
        self.entity_system = EntitySystem(self.world)
        self.ai_system = AISystem(self.world, self.entity_system)
        
        # プレイヤー
        self.player_entity = None
        
        # マップ
        self.game_map = None
        
        # FOV
        self.fov_recompute = True
        self.visible = None
        
        # キーム状態
        self.game_state = "player_turn"  # "player_turn" or "enemy_turn"
        
        # キー設定
        self.MOVE_KEYS = {
            # Vi keys
            tcod.event.KeySym.h: (-1, 0),
            tcod.event.KeySym.j: (0, 1),
            tcod.event.KeySym.k: (0, -1),
            tcod.event.KeySym.l: (1, 0),
            tcod.event.KeySym.y: (-1, -1),
            tcod.event.KeySym.u: (1, -1),
            tcod.event.KeySym.b: (-1, 1),
            tcod.event.KeySym.n: (1, 1),
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
        
        # コンソールの初期化
        self.console = tcod.console.Console(self.screen_width, self.screen_height, order="C")
        self.context = tcod.context.new(
            columns=self.console.width,
            rows=self.console.height,
            tileset=tileset,
            title="Roguelike",
        )
        
        logger.info("Generating dungeon")
        # ダンジョンの生成
        self.game_map, (player_x, player_y) = generate_dungeon(
            map_width=80,
            map_height=43,
            max_rooms=20,
            room_min_size=6,
            room_max_size=10,
        )
        
        # EntitySystemにゲームマップを設定
        self.entity_system.set_game_map(self.game_map)
        
        # プレイヤーの作成
        self.player_entity = self.entity_factory.create_player(player_x, player_y)
        
        # テスト用モンスターの配置
        self.entity_factory.create_monster(player_x + 5, player_y, "orc")
        self.entity_factory.create_monster(player_x - 5, player_y, "troll")
        
        # FOVの初期化
        self.visible = np.zeros((self.game_map.height, self.game_map.width), dtype=bool)
        
        # Welcomeメッセージ
        self.add_message("Hello Stranger, welcome to the Dungeons of Doom!")
        self.add_message("Your quest is to retrieve the Amulet of Yendor.")
        self.add_message("Press '?' for help.")
    
    def update(self) -> None:
        """ゲームの状態更新"""
        if self.game_state == "enemy_turn":
            self.ai_system.update(self.game_map, self.player_entity)
            self.game_state = "player_turn"
    
    def handle_events(self) -> bool:
        """イベント処理"""
        for event in tcod.event.wait():
            action = self.handle_action(event)
            
            if action is None:
                continue
            
            if action == "quit":
                logger.info("Quit action triggered")
                return False
            
            if isinstance(action, tuple) and self.game_state == "player_turn":
                dx, dy = action
                player_pos = self.world.component_for_entity(self.player_entity, Position)
                new_x = player_pos.x + dx
                new_y = player_pos.y + dy
                
                # 移動先が歩行可能な場合のみ移動
                if 0 <= new_x < self.map_width and 0 <= new_y < self.map_height:
                    if self.game_map.walkable[new_y, new_x]:
                        if self.entity_system.move_entity(self.player_entity, dx, dy):
                            self.fov_recompute = True
                            self.game_state = "enemy_turn"
                        
        return True
    
    def handle_action(self, event) -> Optional[Union[str, Tuple[int, int]]]:
        """イベントからアクションを決定する"""
        if isinstance(event, tcod.event.Quit):
            return "quit"
        
        if not isinstance(event, tcod.event.KeyDown):
            return None
            
        # キーリピートを無視
        if event.repeat:
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
    
    def render(self) -> None:
        """画面の描画"""
        # FOVの再計算
        if self.fov_recompute:
            player_pos = self.world.component_for_entity(self.player_entity, Position)
            self.visible = self.game_map.compute_fov(player_pos.x, player_pos.y)
            self.fov_recompute = False
        
        # コンソールをクリア
        self.console.clear()
        
        # マップの描画
        self.game_map.render(self.console, self.visible)
        
        # エンティティの描画
        for ent, (pos,) in self.world.get_components(Position):
            if not self.visible[pos.y, pos.x]:
                continue
                
            render_data = self.entity_system.get_renderable_data(ent)
            if render_data:
                char, fg, bg = render_data
                self.console.ch[pos.y, pos.x] = ord(char)
                self.console.fg[pos.y, pos.x] = fg
                self.console.bg[pos.y, pos.x] = bg
        
        # ステータス情報の表示
        status_y = self.map_height
        fighter = self.entity_system.get_fighter_data(self.player_entity)
        status_text = f"HP: {fighter.hp}/{fighter.max_hp}  Floor: 1  Turn: 0"
        self.console.print(x=0, y=status_y, string=status_text, fg=(255, 255, 255))
        
        # メッセージの表示
        message_y = status_y + self.status_height
        for i, message in enumerate(self.messages[-self.message_height:]):
            self.console.print(x=0, y=message_y + i, string=message, fg=(255, 255, 255))
        
        # 画面の更新
        self.context.present(self.console) 