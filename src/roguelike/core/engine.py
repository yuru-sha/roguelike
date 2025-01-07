import tcod
import numpy as np
import esper
from typing import Optional, Tuple, Union

from roguelike.world.map.dungeon import generate_dungeon
from roguelike.world.map.game_map import GameMap
from roguelike.world.entity.factory import EntityFactory
from roguelike.world.entity.systems import EntitySystem
from roguelike.world.entity.ai import AISystem
from roguelike.world.entity.components import (
    Position,
    Item,
    Name,
    Inventory,
    Fighter,
    Equipment,
)
from roguelike.utils.logger import logger
from roguelike.world.entity.inventory import InventorySystem
from roguelike.world.entity.item_functions import heal, cast_lightning, cast_fireball, cast_confusion

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
        self.inventory_system = InventorySystem(self.world)
        
        # プレイヤー
        self.player_entity = None
        
        # マップ
        self.game_map = None
        
        # FOV
        self.fov_recompute = True
        self.visible = None
        
        # キーム状態
        self.game_state = "player_turn"  # "player_turn" or "enemy_turn" or "targeting"
        self.targeting_item = None
        
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
            tcod.event.KeySym.g: "pickup",  # Get item
            tcod.event.KeySym.i: "inventory",  # Show inventory
            tcod.event.KeySym.d: "drop",  # Drop item
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
            world=self.world,
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
            # ターゲット選択中のマウスクリック
            if self.game_state == "targeting" and isinstance(event, tcod.event.MouseButtonDown):
                if event.button == tcod.event.MouseButton.LEFT:
                    x, y = event.tile
                    # マップ内かつ視界内の場合のみ
                    if (0 <= x < self.map_width and 0 <= y < self.map_height and 
                        self.visible[y, x]):
                        # ターゲット位置のエンティティを取得
                        target = None
                        for ent in self.entity_system.get_entities_at(x, y):
                            if self.world.has_component(ent, Fighter):
                                target = ent
                                break
                        
                        if target is not None:
                            self.inventory_system.use_item(self.player_entity, self.targeting_item, target)
                            self.game_state = "enemy_turn"
                    
                    self.targeting_item = None
                    self.game_state = "player_turn"
                    continue
            
            action = self.handle_action(event)
            
            if action is None:
                continue
            
            if action == "quit":
                logger.info("Quit action triggered")
                return False
            
            if self.game_state == "player_turn":
                if isinstance(action, tuple):
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
                
                elif action == "pickup":
                    # プレイヤーの位置にあるアイテムを拾う
                    player_pos = self.world.component_for_entity(self.player_entity, Position)
                    items = []
                    for ent in self.entity_system.get_entities_at(player_pos.x, player_pos.y):
                        if self.world.has_component(ent, Item):
                            items.append(ent)
                    
                    if not items:
                        self.add_message("There is nothing here to pick up.")
                        continue
                    
                    item = items[0]  # 最初のアイテムを拾う
                    if self.inventory_system.add_item(self.player_entity, item):
                        name = self.world.component_for_entity(item, Name)
                        self.add_message(f"You pick up the {name.name}!")
                        self.game_state = "enemy_turn"
                
                elif action == "inventory":
                    self.show_inventory()
                
                elif action == "drop":
                    self.show_inventory(drop=True)
        
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
        
        if key in self.ACTION_KEYS:
            return self.ACTION_KEYS[key]
        
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
    
    def show_inventory(self, drop: bool = False) -> None:
        """インベントリを表示"""
        if not self.world.has_component(self.player_entity, Inventory):
            return
            
        inventory = self.world.component_for_entity(self.player_entity, Inventory)
        
        if not inventory.items:
            self.add_message("Your inventory is empty.")
            return
        
        # インベントリウィンドウの設定
        window_width = 50  # 詳細情報を表示するために幅を広げる
        window_height = len(inventory.items) + 2
        window_x = self.screen_width // 2 - window_width // 2
        window_y = self.screen_height // 2 - window_height // 2
        
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
            name = self.world.component_for_entity(item, Name)
            key = chr(ord('a') + i)  # a, b, c, ...
            
            # アイテムの詳細情報を取得
            details = []
            
            # 装備品の場合
            if self.world.has_component(item, Equipment):
                equipment = self.world.component_for_entity(item, Equipment)
                if equipment.power_bonus != 0:
                    details.append(f"Power +{equipment.power_bonus}")
                if equipment.defense_bonus != 0:
                    details.append(f"Defense +{equipment.defense_bonus}")
                if equipment.is_equipped:
                    details.append("(equipped)")
            
            # 使用可能アイテムの場合
            if self.world.has_component(item, Item):
                item_component = self.world.component_for_entity(item, Item)
                if "amount" in item_component.function_kwargs:
                    details.append(f"Heals {item_component.function_kwargs['amount']} HP")
                elif "damage" in item_component.function_kwargs:
                    details.append(f"Deals {item_component.function_kwargs['damage']} damage")
            
            # 詳細情報を結合
            detail_text = ", ".join(details)
            if detail_text:
                text = f"{key}) {name.name:<15} - {detail_text}"
            else:
                text = f"{key}) {name.name}"
            
            window.print(x=1, y=i+1, string=text)
        
        # メインコンソールにウィンドウを合成
        window.blit(
            dest=self.console,
            dest_x=window_x,
            dest_y=window_y,
            src_x=0,
            src_y=0,
            width=window_width,
            height=window_height,
            fg_alpha=1.0,
            bg_alpha=0.7,
        )
        
        # 画面の更新
        self.context.present(self.console)
        
        # キー入力待ち
        while True:
            for event in tcod.event.wait():
                if not isinstance(event, tcod.event.KeyDown):
                    continue
                    
                # ESCキーでキャンセル
                if event.sym == tcod.event.KeySym.ESCAPE:
                    return
                
                # アイテムの選択（a-z）
                index = event.sym - tcod.event.KeySym.a
                if 0 <= index < len(inventory.items):
                    selected_item = inventory.items[index]
                    if drop:
                        if self.inventory_system.remove_item(self.player_entity, selected_item):
                            player_pos = self.world.component_for_entity(self.player_entity, Position)
                            # アイテムをプレイヤーの位置に戻す
                            self.world.add_component(selected_item, Position(x=player_pos.x, y=player_pos.y))
                            name = self.world.component_for_entity(selected_item, Name)
                            self.add_message(f"You dropped the {name.name}.")
                            self.game_state = "enemy_turn"
                    else:
                        item_component = self.world.component_for_entity(selected_item, Item)
                        if item_component.targeting:
                            self.targeting_item = selected_item
                            self.game_state = "targeting"
                            self.add_message(item_component.targeting_message or "Left-click a target tile.")
                        else:
                            if self.inventory_system.use_item(self.player_entity, selected_item):
                                self.game_state = "enemy_turn"
                    return 