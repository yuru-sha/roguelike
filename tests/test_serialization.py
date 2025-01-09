import numpy as np
import pytest
import tempfile
from pathlib import Path
import esper
from roguelike.core.engine import Engine
from roguelike.world.entity.components.base import Position, Renderable, Fighter, Item, Corpse, RenderOrder, EquipmentSlots, Equipment, EquipmentSlot, WeaponType
from roguelike.core.constants import Colors, MAP_WIDTH, MAP_HEIGHT
from roguelike.world.map.tiles import Tile, TileType
import logging

logger = logging.getLogger(__name__)

def initialize_test_map(engine):
    """テスト用のマップを初期化する"""
    # マップの初期化
    engine.tiles = np.empty((MAP_HEIGHT, MAP_WIDTH), dtype=object)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            tile = Tile(TileType.FLOOR)
            engine.tiles[y][x] = tile
            logger.debug(f"Created tile at ({x}, {y}): {tile.tile_type}")
    
    # FOVマップの初期化
    engine._initialize_fov()
    logger.debug("FOV map initialized")

def test_save_load_basic_entity():
    """基本的なエンティティのセーブ・ロード機能をテストする"""
    # 一時ディレクトリを作成
    with tempfile.TemporaryDirectory() as temp_dir:
        # セーブディレクトリを一時ディレクトリに設定
        from roguelike.utils.serialization import SaveManager
        SaveManager.set_save_dir(temp_dir)
        
        # テスト用のEngineインスタンスを作成
        engine = Engine(skip_lock_check=True)
        initialize_test_map(engine)
        
        # プレイヤーエンティティを作成
        player = engine.world.create_entity()
        engine.world.add_component(player, Position(x=5, y=5))
        engine.world.add_component(player, Renderable(
            char='@',
            color=Colors.WHITE,
            render_order=RenderOrder.ACTOR,
            name="Player"
        ))
        engine.player = player  # プレイヤーIDを設定
        
        # テスト用のエンティティを作成
        test_entity = engine.world.create_entity()
        engine.world.add_component(test_entity, Position(x=10, y=20))
        engine.world.add_component(test_entity, Renderable(
            char='@',
            color=Colors.WHITE,
            render_order=RenderOrder.ACTOR,
            name="Test Entity"
        ))
        
        # セーブ
        engine.save_game(slot=0)
        
        # 新しいEngineインスタンスを作成してロード
        new_engine = Engine(skip_lock_check=True)
        assert new_engine.load_game(slot=0)
        
        # エンティティが正しくロードされたか確認
        entities = list(new_engine.world.get_components(Position, Renderable))
        assert len(entities) == 2  # プレイヤーとテストエンティティ
        
        # プレイヤーエンティティの確認
        player_entities = [(eid, pos, render) for eid, (pos, render) in entities if eid == new_engine.player]
        assert len(player_entities) == 1
        player_id, player_pos, player_render = player_entities[0]
        assert player_pos.x == 5 and player_pos.y == 5
        assert player_render.char == '@'
        assert player_render.name == "Player"
        
        # テストエンティティの確認
        test_entities = [(eid, pos, render) for eid, (pos, render) in entities if eid != new_engine.player]
        assert len(test_entities) == 1
        entity_id, pos, render = test_entities[0]
        assert pos.x == 10 and pos.y == 20
        assert render.char == '@'
        assert render.name == "Test Entity"

def test_save_load_complex_entity():
    """複雑なコンポーネントを持つエンティティのセーブ・ロード機能をテストする"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # セーブディレクトリを一時ディレクトリに設定
        from roguelike.utils.serialization import SaveManager
        SaveManager.set_save_dir(temp_dir)
        
        engine = Engine(skip_lock_check=True)
        initialize_test_map(engine)
        
        # プレイヤーエンティティを作成
        player = engine.world.create_entity()
        engine.world.add_component(player, Position(x=5, y=5))
        engine.world.add_component(player, Renderable(
            char='@',
            color=Colors.WHITE,
            render_order=RenderOrder.ACTOR,
            name="Player"
        ))
        engine.player = player  # プレイヤーIDを設定
        
        # 複雑なエンティティを作成（オークの死体など）
        corpse = engine.world.create_entity()
        engine.world.add_component(corpse, Position(x=5, y=15))
        engine.world.add_component(corpse, Renderable(
            char='%',
            color=Colors.RED,
            render_order=RenderOrder.CORPSE,
            name="remains of orc"
        ))
        engine.world.add_component(corpse, Corpse("orc"))
        engine.world.add_component(corpse, Item(name="remains of orc"))
        
        # セーブ
        engine.save_game(slot=1)
        
        # 新しいEngineインスタンスを作成してロード
        new_engine = Engine(skip_lock_check=True)
        assert new_engine.load_game(slot=1)
        
        # プレイヤーエンティティの確認
        player_entities = list(new_engine.world.get_components(Position, Renderable))
        player_entities = [(eid, pos, render) for eid, (pos, render) in player_entities if eid == new_engine.player]
        assert len(player_entities) == 1
        player_id, player_pos, player_render = player_entities[0]
        assert player_pos.x == 5 and player_pos.y == 5
        assert player_render.char == '@'
        assert player_render.name == "Player"
        
        # 死体エンティティの確認
        corpse_entities = list(new_engine.world.get_components(Position, Renderable, Corpse, Item))
        assert len(corpse_entities) == 1
        entity_id, (pos, render, corpse, item) = corpse_entities[0]
        assert pos.x == 5 and pos.y == 15
        assert render.char == '%'
        assert render.name == "remains of orc"
        assert corpse.original_name == "orc"
        assert item.name == "remains of orc"

def test_save_load_multiple_entities():
    """複数のエンティティのセーブ・ロード機能をテストする"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # セーブディレクトリを一時ディレクトリに設定
        from roguelike.utils.serialization import SaveManager
        SaveManager.set_save_dir(temp_dir)
        
        engine = Engine(skip_lock_check=True)
        initialize_test_map(engine)
        
        # プレイヤーエンティティ
        player = engine.world.create_entity()
        engine.world.add_component(player, Position(x=10, y=10))
        engine.world.add_component(player, Renderable(
            char='@',
            color=Colors.WHITE,
            render_order=RenderOrder.ACTOR,
            name="Player"
        ))
        engine.world.add_component(player, Fighter(
            max_hp=30,
            hp=30,
            defense=2,
            power=5
        ))
        engine.player = player  # プレイヤーIDを設定
        
        # オークの死体
        corpse = engine.world.create_entity()
        engine.world.add_component(corpse, Position(x=11, y=10))
        engine.world.add_component(corpse, Renderable(
            char='%',
            color=Colors.RED,
            render_order=RenderOrder.CORPSE,
            name="remains of orc"
        ))
        engine.world.add_component(corpse, Corpse("orc"))
        engine.world.add_component(corpse, Item(name="remains of orc"))
        
        # セーブ
        engine.save_game(slot=2)
        
        # 新しいEngineインスタンスを作成してロード
        new_engine = Engine(skip_lock_check=True)
        assert new_engine.load_game(slot=2)
        
        # プレイヤーエンティティの確認
        player_entities = list(new_engine.world.get_components(Position, Renderable, Fighter))
        player_entities = [(eid, pos, render, fighter) for eid, (pos, render, fighter) in player_entities if eid == new_engine.player]
        assert len(player_entities) == 1
        player_id, player_pos, player_render, player_fighter = player_entities[0]
        assert player_pos.x == 10 and player_pos.y == 10
        assert player_render.char == '@'
        assert player_fighter.max_hp == 30
        
        # 死体エンティティの確認
        corpse_entities = list(new_engine.world.get_components(Position, Renderable, Corpse, Item))
        assert len(corpse_entities) == 1
        corpse_id, (pos, render, corpse, item) = corpse_entities[0]
        assert pos.x == 11 and pos.y == 10
        assert render.char == '%'
        assert corpse.original_name == "orc"

def test_save_load_equipment():
    """装備品のセーブ・ロード機能をテストする"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # セーブディレクトリを一時ディレクトリに設定
        from roguelike.utils.serialization import SaveManager
        SaveManager.set_save_dir(temp_dir)
        
        engine = Engine(skip_lock_check=True)
        initialize_test_map(engine)
        
        # プレイヤーエンティティ
        player = engine.world.create_entity()
        engine.world.add_component(player, Position(x=10, y=10))
        engine.world.add_component(player, Renderable(
            char='@',
            color=Colors.WHITE,
            render_order=RenderOrder.ACTOR,
            name="Player"
        ))
        
        # 装備スロットを追加
        equipment_slots = EquipmentSlots()
        engine.world.add_component(player, equipment_slots)
        
        # 剣を作成
        sword = engine.world.create_entity()
        engine.world.add_component(sword, Position(x=11, y=10))
        engine.world.add_component(sword, Renderable(
            char='/',
            color=Colors.LIGHT_BLUE,
            render_order=RenderOrder.ITEM,
            name="Short Sword"
        ))
        sword_equipment = Equipment(
            equipment_slot=EquipmentSlot.MAIN_HAND,
            power_bonus=2,
            weapon_type=WeaponType.ONE_HANDED
        )
        engine.world.add_component(sword, sword_equipment)
        
        # セーブ前のデータを出力
        logger.debug("Before save:")
        logger.debug(f"Sword equipment: {sword_equipment.to_dict()}")
        
        # アイテムを装備
        equipment_slots.equip(EquipmentSlot.MAIN_HAND, sword, engine.world)
        
        engine.player = player  # プレイヤーIDを設定
        
        # セーブ
        engine.save_game(slot=3)
        
        # 新しいEngineインスタンスを作成してロード
        new_engine = Engine(skip_lock_check=True)
        assert new_engine.load_game(slot=3)
        
        # プレイヤーの装備スロットを確認
        player_equipment = list(new_engine.world.get_components(EquipmentSlots))
        assert len(player_equipment) == 1
        player_id, (equipment_slots,) = player_equipment[0]
        assert player_id == new_engine.player
        
        # 装備品の確認
        main_hand_id = equipment_slots.get_equipped(EquipmentSlot.MAIN_HAND)
        assert main_hand_id is not None
        main_hand = new_engine.world.component_for_entity(main_hand_id, Equipment)
        
        # ロード後のデータを出力
        logger.debug("After load:")
        logger.debug(f"Main hand equipment: {main_hand.to_dict()}")
        
        assert main_hand.slot == EquipmentSlot.MAIN_HAND
        assert main_hand.power_bonus == 2
        assert main_hand.weapon_type == WeaponType.ONE_HANDED 