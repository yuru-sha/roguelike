import os
import sys
from pathlib import Path

import pytest

# プロジェクトルートディレクトリをPYTHONPATHに追加
project_root = Path(__file__).parents[1]
sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path):
    """テスト環境のセットアップ"""
    # 一時的なセーブディレクトリを作成
    save_dir = tmp_path / "data" / "save"
    save_dir.mkdir(parents=True)

    # 一時的なログディレクトリを作成
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True)

    # 環境変数を設定
    os.environ["ROGUELIKE_SAVE_DIR"] = str(save_dir)
    os.environ["ROGUELIKE_LOG_DIR"] = str(log_dir)

    yield

    # クリーンアップ
    os.environ.pop("ROGUELIKE_SAVE_DIR", None)
    os.environ.pop("ROGUELIKE_LOG_DIR", None)
