import gzip
import json
import logging
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import esper
import numpy as np
import pytest

from roguelike.core.constants import MAP_HEIGHT, MAP_WIDTH, Colors
from roguelike.core.engine import Engine
from roguelike.world.entity.components.base import (Corpse, Equipment,
                                                    EquipmentSlot,
                                                    EquipmentSlots, Experience,
                                                    Fighter, Item, Position,
                                                    Renderable, RenderOrder,
                                                    Skills, StatusEffect,
                                                    StatusEffects, Vision,
                                                    WeaponType)
from roguelike.world.map.tiles import Tile, TileType

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
        engine.world.add_component(
            player,
            Renderable(
                char="@",
                color=Colors.WHITE,
                render_order=RenderOrder.ACTOR,
                name="Player",
            ),
        )
        engine.player = player  # プレイヤーIDを設定

        # テスト用のエンティティを作成
        test_entity = engine.world.create_entity()
        engine.world.add_component(test_entity, Position(x=10, y=20))
        engine.world.add_component(
            test_entity,
            Renderable(
                char="@",
                color=Colors.WHITE,
                render_order=RenderOrder.ACTOR,
                name="Test Entity",
            ),
        )

        # セーブ
        engine.save_game(slot=0)

        # 新しいEngineインスタンスを作成してロード
        new_engine = Engine(skip_lock_check=True)
        assert new_engine.load_game(slot=0)

        # エンティティが正しくロードされたか確認
        entities = list(new_engine.world.get_components(Position, Renderable))
        assert len(entities) == 2  # プレイヤーとテストエンティティ

        # プレイヤーエンティティの確認
        player_entities = [
            (eid, pos, render)
            for eid, (pos, render) in entities
            if eid == new_engine.player
        ]
        assert len(player_entities) == 1
        player_id, player_pos, player_render = player_entities[0]
        assert player_pos.x == 5 and player_pos.y == 5
        assert player_render.char == "@"
        assert player_render.name == "Player"

        # テストエンティティの確認
        test_entities = [
            (eid, pos, render)
            for eid, (pos, render) in entities
            if eid != new_engine.player
        ]
        assert len(test_entities) == 1
        entity_id, pos, render = test_entities[0]
        assert pos.x == 10 and pos.y == 20
        assert render.char == "@"
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
        engine.world.add_component(
            player,
            Renderable(
                char="@",
                color=Colors.WHITE,
                render_order=RenderOrder.ACTOR,
                name="Player",
            ),
        )
        engine.player = player  # プレイヤーIDを設定

        # 複雑なエンティティを作成（オークの死体など）
        corpse = engine.world.create_entity()
        engine.world.add_component(corpse, Position(x=5, y=15))
        engine.world.add_component(
            corpse,
            Renderable(
                char="%",
                color=Colors.RED,
                render_order=RenderOrder.CORPSE,
                name="remains of orc",
            ),
        )
        engine.world.add_component(corpse, Corpse("orc"))
        engine.world.add_component(corpse, Item(name="remains of orc"))

        # セーブ
        engine.save_game(slot=1)

        # 新しいEngineインスタンスを作成してロード
        new_engine = Engine(skip_lock_check=True)
        assert new_engine.load_game(slot=1)

        # プレイヤーエンティティの確認
        player_entities = list(new_engine.world.get_components(Position, Renderable))
        player_entities = [
            (eid, pos, render)
            for eid, (pos, render) in player_entities
            if eid == new_engine.player
        ]
        assert len(player_entities) == 1
        player_id, player_pos, player_render = player_entities[0]
        assert player_pos.x == 5 and player_pos.y == 5
        assert player_render.char == "@"
        assert player_render.name == "Player"

        # 死体エンティティの確認
        corpse_entities = list(
            new_engine.world.get_components(Position, Renderable, Corpse, Item)
        )
        assert len(corpse_entities) == 1
        entity_id, (pos, render, corpse, item) = corpse_entities[0]
        assert pos.x == 5 and pos.y == 15
        assert render.char == "%"
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
        engine.world.add_component(
            player,
            Renderable(
                char="@",
                color=Colors.WHITE,
                render_order=RenderOrder.ACTOR,
                name="Player",
            ),
        )
        engine.world.add_component(
            player, Fighter(max_hp=30, hp=30, defense=2, power=5)
        )
        engine.player = player  # プレイヤーIDを設定

        # オークの死体
        corpse = engine.world.create_entity()
        engine.world.add_component(corpse, Position(x=11, y=10))
        engine.world.add_component(
            corpse,
            Renderable(
                char="%",
                color=Colors.RED,
                render_order=RenderOrder.CORPSE,
                name="remains of orc",
            ),
        )
        engine.world.add_component(corpse, Corpse("orc"))
        engine.world.add_component(corpse, Item(name="remains of orc"))

        # セーブ
        engine.save_game(slot=2)

        # 新しいEngineインスタンスを作成してロード
        new_engine = Engine(skip_lock_check=True)
        assert new_engine.load_game(slot=2)

        # プレイヤーエンティティの確認
        player_entities = list(
            new_engine.world.get_components(Position, Renderable, Fighter)
        )
        player_entities = [
            (eid, pos, render, fighter)
            for eid, (pos, render, fighter) in player_entities
            if eid == new_engine.player
        ]
        assert len(player_entities) == 1
        player_id, player_pos, player_render, player_fighter = player_entities[0]
        assert player_pos.x == 10 and player_pos.y == 10
        assert player_render.char == "@"
        assert player_fighter.max_hp == 30

        # 死体エンティティの確認
        corpse_entities = list(
            new_engine.world.get_components(Position, Renderable, Corpse, Item)
        )
        assert len(corpse_entities) == 1
        corpse_id, (pos, render, corpse, item) = corpse_entities[0]
        assert pos.x == 11 and pos.y == 10
        assert render.char == "%"
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
        engine.world.add_component(
            player,
            Renderable(
                char="@",
                color=Colors.WHITE,
                render_order=RenderOrder.ACTOR,
                name="Player",
            ),
        )

        # 装備スロットを追加
        equipment_slots = EquipmentSlots()
        engine.world.add_component(player, equipment_slots)

        # 剣を作成
        sword = engine.world.create_entity()
        engine.world.add_component(sword, Position(x=11, y=10))
        engine.world.add_component(
            sword,
            Renderable(
                char="/",
                color=Colors.LIGHT_BLUE,
                render_order=RenderOrder.ITEM,
                name="Short Sword",
            ),
        )
        sword_equipment = Equipment(
            equipment_slot=EquipmentSlot.MAIN_HAND,
            power_bonus=2,
            weapon_type=WeaponType.ONE_HANDED,
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


def test_save_load_new_components():
    """新しいコンポーネントのセーブ・ロード機能をテストする"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # セーブディレクトリを一時ディレクトリに設定
        from roguelike.utils.serialization import SaveManager

        SaveManager.set_save_dir(temp_dir)

        engine = Engine(skip_lock_check=True)
        initialize_test_map(engine)

        # プレイヤーエンティティを作成
        player = engine.world.create_entity()
        engine.world.add_component(player, Position(x=10, y=10))
        engine.world.add_component(
            player,
            Renderable(
                char="@",
                color=Colors.WHITE,
                render_order=RenderOrder.ACTOR,
                name="Player",
            ),
        )
        engine.world.add_component(
            player, Fighter(max_hp=30, hp=30, defense=2, power=5)
        )

        # StatusEffectsコンポーネントを追加
        status_effects = StatusEffects()
        status_effects.add_effect(StatusEffect.POISONED, 3, 2)
        status_effects.add_effect(StatusEffect.BURNING, 2, 1)
        engine.world.add_component(player, status_effects)

        # Visionコンポーネントを追加
        vision = Vision(range=8, can_see_invisible=True, night_vision=True)
        engine.world.add_component(player, vision)

        # Skillsコンポーネントを追加
        skills = Skills()
        skills.add_skill("fireball", {"damage": 10, "range": 5})
        skills.add_skill("heal", {"amount": 5, "cooldown": 3})
        engine.world.add_component(player, skills)

        # Experienceコンポーネントを追加
        experience = Experience(level=5, current_xp=450, skill_points=2)
        engine.world.add_component(player, experience)

        engine.player = player  # プレイヤーIDを設定

        # セーブ
        engine.save_game(slot=4)

        # 新しいEngineインスタンスを作成してロード
        new_engine = Engine(skip_lock_check=True)
        assert new_engine.load_game(slot=4)

        # プレイヤーエンティティの確認
        player_components = list(
            new_engine.world.get_components(
                Position, Renderable, Fighter, StatusEffects, Vision, Skills, Experience
            )
        )
        assert len(player_components) == 1

        # コンポーネントの取り出し
        player_id, (
            pos,
            render,
            fighter,
            status,
            vision,
            skills,
            exp,
        ) = player_components[0]
        assert player_id == new_engine.player

        # StatusEffectsの確認
        assert StatusEffect.POISONED in status.effects
        assert status.effects[StatusEffect.POISONED].duration == 3
        assert status.effects[StatusEffect.POISONED].strength == 2
        assert StatusEffect.BURNING in status.effects
        assert status.effects[StatusEffect.BURNING].duration == 2
        assert status.effects[StatusEffect.BURNING].strength == 1

        # Visionの確認
        assert vision.range == 8
        assert vision.can_see_invisible is True
        assert vision.night_vision is True

        # Skillsの確認
        assert "fireball" in skills.available_skills
        assert skills.available_skills["fireball"]["damage"] == 10
        assert skills.available_skills["fireball"]["range"] == 5
        assert "heal" in skills.available_skills
        assert skills.available_skills["heal"]["amount"] == 5
        assert skills.available_skills["heal"]["cooldown"] == 3

        # Experienceの確認
        assert exp.level == 5
        assert exp.current_xp == 450
        assert exp.skill_points == 2
        assert exp.xp_to_next_level == exp.calculate_xp_for_level(6)


def test_save_validation_errors():
    """セーブデータの検証エラーをテストする"""
    with tempfile.TemporaryDirectory() as temp_dir:
        from roguelike.utils.serialization import (SaveManager,
                                                   SaveValidationError)

        SaveManager.set_save_dir(temp_dir)

        # 必須フィールドが欠けているデータ
        invalid_data = {"game_state": {}, "entities": []}

        with pytest.raises(SaveValidationError) as exc_info:
            SaveManager.save_game(invalid_data)

        assert "version" in exc_info.value.validation_errors
        assert "player_id" in exc_info.value.validation_errors


def test_save_file_not_found():
    """存在しないセーブファイルのロードをテストする"""
    with tempfile.TemporaryDirectory() as temp_dir:
        from roguelike.utils.serialization import (SaveFileNotFoundError,
                                                   SaveManager)

        SaveManager.set_save_dir(temp_dir)

        with pytest.raises(SaveFileNotFoundError):
            SaveManager.load_game(slot=999)


def test_save_file_corrupted():
    """破損したセーブファイルのロードをテストする"""
    with tempfile.TemporaryDirectory() as temp_dir:
        from roguelike.utils.serialization import (SaveFileCorruptedError,
                                                   SaveManager)

        SaveManager.set_save_dir(temp_dir)

        # 破損したデータを書き込む
        save_path = Path(temp_dir) / "save_0.sav"
        with save_path.open("wb") as f:
            f.write(b"corrupted data")

        with pytest.raises(SaveFileCorruptedError):
            SaveManager.load_game(slot=0)


def test_save_version_error():
    """互換性のないバージョンのセーブデータをテストする"""
    with tempfile.TemporaryDirectory() as temp_dir:
        from roguelike.utils.serialization import SaveManager, SaveVersionError

        SaveManager.set_save_dir(temp_dir)

        engine = Engine(skip_lock_check=True)
        initialize_test_map(engine)

        # プレイヤーエンティティを作成
        player = engine.world.create_entity()
        engine.world.add_component(player, Position(x=5, y=5))
        engine.player = player

        # 古いバージョンのデータを作成
        save_data = {
            "version": "0.0.1",  # 存在しないバージョン
            "game_state": {},
            "entities": [],
            "tiles": None,
            "player_id": player,
            "dungeon_level": 1,
        }

        with pytest.raises(SaveVersionError):
            SaveManager.save_game(save_data)


def test_save_compression_error():
    """圧縮エラーをテストする"""
    with tempfile.TemporaryDirectory() as temp_dir:
        from roguelike.utils.serialization import (SaveCompressionError,
                                                   SaveManager)

        SaveManager.set_save_dir(temp_dir)

        # 圧縮できないデータを作成
        class UncompressableObject:
            def __repr__(self):
                raise Exception("Compression test error")

        invalid_data = {
            "version": "1.1.0",
            "game_state": {"uncompressable": UncompressableObject()},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }

        with pytest.raises(SaveCompressionError):
            SaveManager.save_game(invalid_data)


def test_save_encryption_error():
    """暗号化エラーをテストする"""
    with tempfile.TemporaryDirectory() as temp_dir:
        from roguelike.utils.serialization import (SaveEncryptionError,
                                                   SaveManager)

        SaveManager.set_save_dir(temp_dir)

        # 暗号化キーファイルを破損させる
        key_file = Path(temp_dir) / ".key"
        with key_file.open("wb") as f:
            f.write(b"invalid key")

        valid_data = {
            "version": "1.1.0",
            "game_state": {},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }

        with pytest.raises(SaveEncryptionError):
            SaveManager.save_game(valid_data)


def test_backup_rotation():
    """バックアップのローテーション機能をテストする"""
    with tempfile.TemporaryDirectory() as temp_dir:
        from roguelike.utils.serialization import SaveManager

        SaveManager.set_save_dir(temp_dir)

        # テスト用のデータを作成
        valid_data = {
            "version": "1.1.0",
            "game_state": {},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }

        # 複数回セーブを実行してバックアップをローテーション
        for i in range(6):
            SaveManager.save_game(valid_data)

        # バックアップファイルを確認
        backups = SaveManager.list_backups(0)
        assert len(backups) == 5  # 最大5世代のバックアップ
        for i in range(1, 6):
            assert i in backups


def test_backup_restoration():
    """バックアップからの復元機能をテストする"""
    with tempfile.TemporaryDirectory() as temp_dir:
        from roguelike.utils.serialization import SaveManager

        SaveManager.set_save_dir(temp_dir)

        # オリジナルのセーブデータを作成
        original_data = {
            "version": "1.1.0",
            "game_state": {"value": "original"},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }
        SaveManager.save_game(original_data)

        # 破損したデータでセーブを上書き
        corrupted_data = {
            "version": "1.1.0",
            "game_state": {"value": "corrupted"},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }
        SaveManager.save_game(corrupted_data)

        # バックアップから復元
        assert SaveManager.restore_backup(0, 1)

        # 復元されたデータを確認
        restored_data = SaveManager.load_game(0)
        assert restored_data["game_state"]["value"] == "original"


def test_save_integrity_verification():
    """セーブデータの整合性検証機能をテストする"""
    with tempfile.TemporaryDirectory() as temp_dir:
        from roguelike.utils.serialization import SaveManager

        SaveManager.set_save_dir(temp_dir)

        # 有効なデータ
        valid_data = {
            "version": "1.1.0",
            "game_state": {},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }
        SaveManager.save_game(valid_data)

        # 整合性チェック
        is_valid, errors = SaveManager.verify_save_integrity(0)
        assert is_valid
        assert len(errors) == 0

        # 無効なデータ
        invalid_data = {
            "version": "1.1.0",
            "game_state": {},
            # entities が欠落
            "tiles": None,
            "player_id": "invalid",  # 不正な型
            "dungeon_level": 1,
        }
        SaveManager.save_game(invalid_data)

        # 整合性チェック
        is_valid, errors = SaveManager.verify_save_integrity(0)
        assert not is_valid
        assert len(errors) > 0
        assert any("entities" in error for error in errors)
        assert any("player ID" in error for error in errors)


def test_auto_repair():
    """自動修復機能をテストする"""
    with tempfile.TemporaryDirectory() as temp_dir:
        from roguelike.utils.serialization import SaveManager

        SaveManager.set_save_dir(temp_dir)

        # 有効なデータでセーブを作成
        valid_data = {
            "version": "1.1.0",
            "game_state": {"value": "original"},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }
        SaveManager.save_game(valid_data)

        # 破損したデータで上書き
        save_path = Path(temp_dir) / "save_0.sav"
        with save_path.open("wb") as f:
            f.write(b"corrupted data")

        # 自動修復を実行
        success, actions = SaveManager.auto_repair(0)
        assert success
        assert any("Restored from backup" in action for action in actions)
        assert any("verified successfully" in action for action in actions)

        # 修復されたデータを確認
        restored_data = SaveManager.load_game(0)
        assert restored_data["game_state"]["value"] == "original"


"""
セーブ/ロードシステムのテストケース
"""


@pytest.fixture
def temp_save_dir():
    """一時的なセーブディレクトリを作成する"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_save_dir = SaveManager.get_save_dir()
        SaveManager._save_dir = Path(temp_dir)
        yield Path(temp_dir)
        SaveManager._save_dir = original_save_dir


def create_test_save_data():
    """テスト用のセーブデータを作成する"""
    return {
        "version": "1.1.0",
        "game_state": {"auto_save_interval": 100, "backup_enabled": True},
        "entities": [
            {
                "id": 1,
                "components": {
                    "Position": {"x": 10, "y": 10},
                    "Fighter": {"hp": 100, "max_hp": 100},
                    "StatusEffects": {"effects": {}},
                    "Vision": {"range": 8},
                    "Skills": {"available_skills": {}},
                    "Experience": {"level": 1, "current_xp": 0},
                },
            }
        ],
        "player_id": 1,
        "dungeon_level": 1,
        "tiles": [[{"blocked": False} for _ in range(10)] for _ in range(10)],
    }


def test_save_and_load(temp_save_dir):
    """基本的なセーブとロードのテスト"""
    data = create_test_save_data()

    # セーブテスト
    assert SaveManager.save_game(data, slot=0)
    save_path = temp_save_dir / "save_0.sav"
    assert save_path.exists()

    # ロードテスト
    loaded_data = SaveManager.load_game(slot=0)
    assert loaded_data is not None
    assert loaded_data["version"] == data["version"]
    assert loaded_data["player_id"] == data["player_id"]
    assert len(loaded_data["entities"]) == len(data["entities"])


def test_backup_creation(temp_save_dir):
    """バックアップ作成のテスト"""
    data = create_test_save_data()

    # 複数回セーブしてバックアップを作成
    for i in range(3):
        SaveManager.save_game(data, slot=0)

    # バックアップファイルの確認
    backups = SaveManager.list_backups(0)
    assert len(backups) > 0

    # バックアップの圧縮を確認
    compressed_backups = [p for p in backups.values() if p.suffix == ".gz"]
    assert len(compressed_backups) > 0


def test_backup_restoration(temp_save_dir):
    """バックアップ復元のテスト"""
    data = create_test_save_data()

    # オリジナルのセーブを作成
    SaveManager.save_game(data, slot=0)

    # データを変更してセーブ（バックアップが作成される）
    modified_data = data.copy()
    modified_data["player_id"] = 2
    SaveManager.save_game(modified_data, slot=0)

    # バックアップから復元
    assert SaveManager.restore_backup(0, 1)

    # 復元されたデータを確認
    restored_data = SaveManager.load_game(slot=0)
    assert restored_data["player_id"] == data["player_id"]


def test_save_validation(temp_save_dir):
    """セーブデータの検証テスト"""
    data = create_test_save_data()

    # 正常なデータ
    assert SaveManager.save_game(data, slot=0)
    is_valid, errors = SaveManager.verify_save_integrity(0)
    assert is_valid
    assert not errors

    # 不正なデータ
    invalid_data = data.copy()
    del invalid_data["version"]
    with pytest.raises(SaveValidationError):
        SaveManager.save_game(invalid_data, slot=1)


def test_backup_cleanup(temp_save_dir):
    """バックアップのクリーンアップテスト"""
    data = create_test_save_data()

    # 複数のバックアップを作成
    for i in range(3):
        SaveManager.save_game(data, slot=0)

    # 古いバックアップを作成（ファイルの更新日時を変更）
    backups = SaveManager.list_backups(0)
    old_date = datetime.now() - timedelta(days=31)
    for path in backups.values():
        os.utime(path, (old_date.timestamp(), old_date.timestamp()))

    # クリーンアップを実行
    deleted = SaveManager.cleanup_old_backups(max_age_days=30)
    assert len(deleted) > 0


def test_compression(temp_save_dir):
    """圧縮機能のテスト"""
    data = create_test_save_data()

    # 圧縮ありでセーブ
    SaveManager.save_game(data, slot=0)

    # バックアップが圧縮されていることを確認
    backups = SaveManager.list_backups(0)
    compressed_backup = next((p for p in backups.values() if p.suffix == ".gz"), None)
    assert compressed_backup is not None

    # 圧縮ファイルを読み込んで内容を確認
    with gzip.open(compressed_backup, "rb") as f:
        content = f.read()
    assert content  # 中身があることを確認


def test_error_handling(temp_save_dir):
    """エラーハンドリングのテスト"""
    # 存在しないスロットからのロード
    with pytest.raises(SaveFileNotFoundError):
        SaveManager.load_game(slot=999)

    # 破損したセーブデータ
    save_path = temp_save_dir / "save_0.sav"
    save_path.write_text("invalid data")
    with pytest.raises(SaveFileCorruptedError):
        SaveManager.load_game(slot=0)

    # 存在しないバックアップの復元
    with pytest.raises(SaveFileNotFoundError):
        SaveManager.restore_backup(0, 999)


def test_auto_repair(temp_save_dir):
    """自動修復機能のテスト"""
    data = create_test_save_data()

    # 正常なセーブを作成（バックアップも作成される）
    SaveManager.save_game(data, slot=0)

    # セーブファイルを破損させる
    save_path = temp_save_dir / "save_0.sav"
    save_path.write_text("corrupted data")

    # 自動修復を実行
    success, actions = SaveManager.auto_repair(0)
    assert success
    assert len(actions) > 0

    # 修復後のデータを確認
    repaired_data = SaveManager.load_game(slot=0)
    assert repaired_data["version"] == data["version"]


def test_save_version_compatibility():
    """セーブデータのバージョン互換性テスト"""
    with tempfile.TemporaryDirectory() as temp_dir:
        from roguelike.utils.serialization import SaveManager, SaveVersionError

        SaveManager.set_save_dir(temp_dir)

        # 古いバージョンのデータを作成
        old_data = {
            "version": "1.0.0",  # 古いバージョン
            "game_state": {},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }

        # バージョンチェックを実行
        with pytest.raises(SaveVersionError):
            SaveManager.validate_version(old_data)

        # バージョン移行をテスト
        migrated_data = SaveManager.migrate_save_data(old_data)
        assert migrated_data["version"] == "1.1.0"  # 最新バージョン


def test_save_data_compression_ratio():
    """セーブデータの圧縮率テスト"""
    with tempfile.TemporaryDirectory() as temp_dir:
        from roguelike.utils.serialization import SaveManager

        SaveManager.set_save_dir(temp_dir)

        # 大きなデータを作成
        large_data = {
            "version": "1.1.0",
            "game_state": {"large_array": [i for i in range(1000)]},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }

        # 圧縮前のサイズを計算
        uncompressed_size = len(json.dumps(large_data).encode())

        # データを保存
        SaveManager.save_game(large_data)

        # 圧縮後のファイルサイズを取得
        save_path = Path(temp_dir) / "save_0.sav"
        compressed_size = save_path.stat().st_size

        # 圧縮率を確認
        compression_ratio = compressed_size / uncompressed_size
        assert compression_ratio < 0.5  # 50%以上の圧縮率を期待


def test_save_data_encryption():
    """セーブデータの暗号化テスト"""
    with tempfile.TemporaryDirectory() as temp_dir:
        from roguelike.utils.serialization import SaveManager

        SaveManager.set_save_dir(temp_dir)

        test_data = {
            "version": "1.1.0",
            "game_state": {"secret": "sensitive_data"},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }

        # データを保存
        SaveManager.save_game(test_data)

        # 保存されたファイルを直接読み込み
        save_path = Path(temp_dir) / "save_0.sav"
        with save_path.open("rb") as f:
            raw_data = f.read()

        # 生データに機密情報が平文で含まれていないことを確認
        assert b"sensitive_data" not in raw_data


def test_save_data_recovery_with_checksum():
    """チェックサムを使用したセーブデータの復旧テスト"""
    with tempfile.TemporaryDirectory() as temp_dir:
        from roguelike.utils.serialization import SaveManager

        SaveManager.set_save_dir(temp_dir)

        original_data = {
            "version": "1.1.0",
            "game_state": {"value": "important"},
            "entities": [],
            "tiles": None,
            "player_id": 1,
            "dungeon_level": 1,
        }

        # データを保存
        SaveManager.save_game(original_data)

        # ファイルを破損させる
        save_path = Path(temp_dir) / "save_0.sav"
        with save_path.open("rb+") as f:
            f.seek(-10, 2)  # ファイル末尾から10バイト前に移動
            f.write(b"corrupted")

        # チェックサムを使用して破損を検出
        is_valid, errors = SaveManager.verify_save_integrity(0)
        assert not is_valid
        assert any("checksum" in error for error in errors)

        # 最新のバックアップから復旧
        recovered = SaveManager.restore_latest_valid_backup(0)
        assert recovered

        # 復旧したデータを確認
        loaded_data = SaveManager.load_game(0)
        assert loaded_data["game_state"]["value"] == "important"


def test_save_data_concurrent_access():
    """セーブデータの並行アクセステスト"""
    with tempfile.TemporaryDirectory() as temp_dir:
        import threading

        from roguelike.utils.serialization import SaveManager

        SaveManager.set_save_dir(temp_dir)

        def save_operation(slot: int):
            data = {
                "version": "1.1.0",
                "game_state": {"thread_id": slot},
                "entities": [],
                "tiles": None,
                "player_id": 1,
                "dungeon_level": 1,
            }
            SaveManager.save_game(data, slot=slot)

        # 複数のスレッドで同時にセーブを実行
        threads = []
        for i in range(5):
            thread = threading.Thread(target=save_operation, args=(i,))
            threads.append(thread)
            thread.start()

        # すべてのスレッドの完了を待つ
        for thread in threads:
            thread.join()

        # 各スロットのデータが正しく保存されていることを確認
        for i in range(5):
            loaded_data = SaveManager.load_game(slot=i)
            assert loaded_data["game_state"]["thread_id"] == i
