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
    Stackable,
    Renderable,
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
        self.entity_factory = EntityFactory(self.world, self)
        self.entity_system = EntitySystem(self.world)
        self.ai_system = AISystem(self.world, self.entity_system)
        self.inventory_system = InventorySystem(self.world, self)
        
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
            tcod.event.KeySym.s: "split",  # Split item
        }

    def initialize(self) -> None:
        """ゲームの初期化"""
        logger.info("Loading game assets")
        
        # フォントの設定
        tileset = tcod.tileset.load_tilesheet(
            "roguelike/assets/dejavu10x10_gs_tc.png",
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
            # マウスイベントの変換
            event = self.context.convert_event(event)
            
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
                    
                    item = items[-1]  # 最後のアイテム（一番上にあるもの）を拾う
                    if self.inventory_system.add_item(self.player_entity, item):
                        name = self.world.component_for_entity(item, Name)
                        self.add_message(f"You pick up the {name.name}!")
                        self.game_state = "enemy_turn"
                
                elif action == "inventory":
                    self.show_inventory()
                
                elif action == "drop":
                    self.show_inventory(drop=True)
                    
                elif action == "split":
                    self.show_inventory(split=True)
        
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
        
        # プレイヤー以外のエンティティを描画
        for ent, (pos,) in self.world.get_components(Position):
            if ent == self.player_entity:  # プレイヤーはスキップ
                continue
                
            if not self.visible[pos.y, pos.x]:
                continue
                
            render_data = self.entity_system.get_renderable_data(ent)
            if render_data:
                char, fg, bg = render_data
                self.console.ch[pos.y, pos.x] = ord(char)
                self.console.fg[pos.y, pos.x] = fg
                self.console.bg[pos.y, pos.x] = bg
        
        # プレイヤーを最後に描画
        player_pos = self.world.component_for_entity(self.player_entity, Position)
        render_data = self.entity_system.get_renderable_data(self.player_entity)
        if render_data:
            char, fg, bg = render_data
            self.console.ch[player_pos.y, player_pos.x] = ord(char)
            self.console.fg[player_pos.y, player_pos.x] = fg
            self.console.bg[player_pos.y, player_pos.x] = bg
        
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
    
    def show_inventory(self, drop: bool = False, split: bool = False) -> None:
        """インベントリを表示"""
        if not self.world.has_component(self.player_entity, Inventory):
            return
            
        inventory = self.world.component_for_entity(self.player_entity, Inventory)
        
        if not inventory.items:
            self.add_message("Your inventory is empty.")
            return
        
        # インベントリウィンドウの設定
        window_width = 50
        window_height = len(inventory.items) + 2
        window_x = self.screen_width // 2 - window_width // 2
        window_y = self.screen_height // 2 - window_height // 2
        
        # 選択中のアイテムインデックス
        selected_index = 0
        
        while True:
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
                key = chr(ord('a') + i)
                
                # アイテムの詳細情報を取得
                details = []
                
                # 重ね置き可能なアイテムの場合は個数を表示
                is_stackable = False
                if (self.world.has_component(item, Item) and 
                    self.world.component_for_entity(item, Item).stackable):
                    stack = self.world.component_for_entity(item, Stackable)
                    details.append(f"x{stack.count}")
                    is_stackable = True
                
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
                
                # 選択中のアイテムは強調表示
                # 分割モードでは、スタック可能なアイテムのみ強調表示
                if split and not is_stackable:
                    color = (64, 64, 64)  # 分割不可能なアイテムは暗く表示
                else:
                    color = (255, 255, 255) if i == selected_index else (128, 128, 128)
                window.print(x=1, y=i+1, string=text, fg=color)
            
            # 操作説明を表示
            action = "drop" if drop else "split" if split else "use"
            help_text = f"↑↓: Select  Enter: {action.capitalize()}  Esc: Cancel"
            window.print(x=1, y=window_height-1, string=help_text)
            
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
            for event in tcod.event.wait():
                if not isinstance(event, tcod.event.KeyDown):
                    continue
                    
                # ESCキーでキャンセル
                if event.sym == tcod.event.KeySym.ESCAPE:
                    return
                
                # 上下キーで選択移動
                elif event.sym == tcod.event.KeySym.UP:
                    selected_index = (selected_index - 1) % len(inventory.items)
                    break
                elif event.sym == tcod.event.KeySym.DOWN:
                    selected_index = (selected_index + 1) % len(inventory.items)
                    break
                
                # Enterキーでアイテム使用/ドロップ/分割
                elif event.sym == tcod.event.KeySym.RETURN:
                    selected_item = inventory.items[selected_index]
                    
                    # 分割モードの場合
                    if split:
                        if (self.world.has_component(selected_item, Item) and 
                            self.world.component_for_entity(selected_item, Item).stackable):
                            stack = self.world.component_for_entity(selected_item, Stackable)
                            name = self.world.component_for_entity(selected_item, Name).name
                            if stack.count > 1:
                                # 数量選択画面を表示
                                quantity = self.show_quantity_selector(
                                    title="Split Stack",
                                    max_quantity=stack.count - 1
                                )
                                if quantity:
                                    self.inventory_system.split_item(
                                        self.player_entity,
                                        selected_item,
                                        quantity
                                    )
                                    self.add_message(f"You split off {quantity} {name}s.")
                                    self.game_state = "enemy_turn"
                    # ドロップモードの場合
                    elif drop:
                        if (self.world.has_component(selected_item, Item) and 
                            self.world.component_for_entity(selected_item, Item).stackable):
                            stack = self.world.component_for_entity(selected_item, Stackable)
                            name = self.world.component_for_entity(selected_item, Name).name
                            if stack.count > 1:
                                # 数量選択画面を表示
                                quantity = self.show_quantity_selector(
                                    title="Drop How Many?",
                                    max_quantity=stack.count
                                )
                                if quantity:
                                    new_item = self.inventory_system.remove_item(self.player_entity, selected_item, quantity)
                                    if new_item:
                                        # ドロップしたアイテムをプレイヤーの位置に配置
                                        player_pos = self.world.component_for_entity(self.player_entity, Position)
                                        self.world.add_component(new_item, Position(x=player_pos.x, y=player_pos.y))
                                        self.add_message(f"You drop {quantity} {name}s.")
                                        self.game_state = "enemy_turn"
                            else:
                                if self.inventory_system.remove_item(self.player_entity, selected_item):
                                    # ドロップしたアイテムをプレイヤーの位置に配置
                                    player_pos = self.world.component_for_entity(self.player_entity, Position)
                                    self.world.add_component(selected_item, Position(x=player_pos.x, y=player_pos.y))
                                    self.add_message(f"You drop {name}.")
                                    self.game_state = "enemy_turn"
                        else:
                            name = self.world.component_for_entity(selected_item, Name).name
                            if self.inventory_system.remove_item(self.player_entity, selected_item):
                                # ドロップしたアイテムをプレイヤーの位置に配置
                                player_pos = self.world.component_for_entity(self.player_entity, Position)
                                self.world.add_component(selected_item, Position(x=player_pos.x, y=player_pos.y))
                                self.add_message(f"You drop {name}.")
                                self.game_state = "enemy_turn"
                    # 使用モードの場合
                    else:
                        item_component = self.world.component_for_entity(selected_item, Item)
                        if item_component.targeting:
                            self.targeting_item = selected_item
                            self.game_state = "targeting"
                            self.add_message(item_component.targeting_message or "Left-click a target tile.")
                        else:
                            if (item_component.stackable and 
                                self.world.component_for_entity(selected_item, Stackable).count > 1):
                                # 数量選択画面を表示
                                quantity = self.show_quantity_selector(
                                    title="Use How Many?",
                                    max_quantity=self.world.component_for_entity(selected_item, Stackable).count
                                )
                                if quantity:
                                    for _ in range(quantity):
                                        if not self.inventory_system.use_item(self.player_entity, selected_item):
                                            break
                            else:
                                if self.inventory_system.use_item(self.player_entity, selected_item):
                                    self.game_state = "enemy_turn"
                    return 
    
    def show_quantity_selector(self, title: str, max_quantity: int) -> Optional[int]:
        """数量選択画面を表示"""
        window_width = 30
        window_height = 5
        window_x = self.screen_width // 2 - window_width // 2
        window_y = self.screen_height // 2 - window_height // 2
        
        current_quantity = 1
        
        while True:
            # ウィンドウの描画
            window = tcod.console.Console(window_width, window_height, order="F")
            window.draw_frame(
                x=0,
                y=0,
                width=window_width,
                height=window_height,
                title=title,
                clear=True,
                fg=(255, 255, 255),
                bg=(0, 0, 0),
            )
            
            # 数量表示
            quantity_text = f"Quantity: {current_quantity}"
            x = window_width // 2 - len(quantity_text) // 2
            window.print(x=x, y=1, string=quantity_text)
            
            # 操作説明
            help_text = "↑↓: Adjust  Enter: OK  Esc: Cancel"
            x = window_width // 2 - len(help_text) // 2
            window.print(x=x, y=3, string=help_text)
            
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
            for event in tcod.event.wait():
                if not isinstance(event, tcod.event.KeyDown):
                    continue
                    
                # ESCキーでキャンセル
                if event.sym == tcod.event.KeySym.ESCAPE:
                    return None
                
                # 上下キーで数量調整
                elif event.sym == tcod.event.KeySym.UP:
                    current_quantity = min(current_quantity + 1, max_quantity)
                    break
                elif event.sym == tcod.event.KeySym.DOWN:
                    current_quantity = max(current_quantity - 1, 1)
                    break
                
                # Enterキーで決定
                elif event.sym == tcod.event.KeySym.RETURN:
                    return current_quantity 