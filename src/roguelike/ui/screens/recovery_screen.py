"""
セーブデータの復旧プロセスを管理するUI画面
"""

from datetime import datetime
from typing import List, Optional, Tuple

import tcod

from roguelike.core.constants import SCREEN_HEIGHT, SCREEN_WIDTH, Colors
from roguelike.ui.screens.base_screen import Screen
from roguelike.utils.logging import GameLogger
from roguelike.utils.serialization import SaveManager

logger = GameLogger.get_instance()


class RecoveryScreen(Screen):
    def __init__(self):
        super().__init__()
        self.selected_index = 0
        self.backups = []
        self.messages: List[Tuple[str, Tuple[int, int, int]]] = []
        self.refresh_backups()

    def refresh_backups(self) -> None:
        """利用可能なバックアップの一覧を更新する"""
        self.backups = []
        for slot in range(5):  # 最大5つのセーブスロット
            backups = SaveManager.list_backups(slot)
            if backups:
                for number, path in backups.items():
                    mtime = datetime.fromtimestamp(path.stat().st_mtime)
                    size = path.stat().st_size
                    is_compressed = path.suffix == ".gz"
                    self.backups.append(
                        {
                            "slot": slot,
                            "number": number,
                            "path": path,
                            "mtime": mtime,
                            "size": size,
                            "compressed": is_compressed,
                        }
                    )

        # 日付の新しい順にソート
        self.backups.sort(key=lambda x: x["mtime"], reverse=True)

    def add_message(
        self, text: str, color: Tuple[int, int, int] = Colors.WHITE
    ) -> None:
        """メッセージを追加する"""
        self.messages.append((text, color))
        if len(self.messages) > 5:  # 最大5つのメッセージを保持
            self.messages.pop(0)

    def render(self, console: tcod.Console) -> None:
        """画面を描画する"""
        console.clear()

        # タイトルを描画
        title = "セーブデータ復旧"
        x = (SCREEN_WIDTH - len(title)) // 2
        console.print(x, 1, title, Colors.YELLOW)

        # バックアップ一覧を描画
        if not self.backups:
            console.print(2, 3, "利用可能なバックアップがありません", Colors.RED)
        else:
            for i, backup in enumerate(self.backups):
                color = Colors.WHITE if i != self.selected_index else Colors.YELLOW
                date_str = backup["mtime"].strftime("%Y-%m-%d %H:%M:%S")
                size_str = f"{backup['size'] / 1024:.1f}KB"
                compressed_str = "[圧縮済]" if backup["compressed"] else ""
                text = f"スロット{backup['slot']} - バックアップ{backup['number']} ({date_str}) {size_str} {compressed_str}"
                console.print(2, 3 + i, text, color)

        # メッセージを描画
        for i, (msg, color) in enumerate(self.messages):
            console.print(2, SCREEN_HEIGHT - 7 + i, msg, color)

        # 操作説明を描画
        console.print(
            2, SCREEN_HEIGHT - 1, "↑/↓:選択 R:復元 V:検証 C:クリーンアップ ESC:戻る", Colors.LIGHT_GRAY
        )

    def handle_input(self, event: tcod.event.Event) -> Optional[Screen]:
        """入力を処理する"""
        if isinstance(event, tcod.event.KeyDown):
            if event.sym == tcod.event.KeySym.ESCAPE:
                return None  # 前の画面に戻る

            if not self.backups:
                return self

            if event.sym == tcod.event.KeySym.UP:
                self.selected_index = (self.selected_index - 1) % len(self.backups)

            elif event.sym == tcod.event.KeySym.DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.backups)

            elif event.sym == tcod.event.KeySym.r:  # 復元
                backup = self.backups[self.selected_index]
                try:
                    if SaveManager.restore_backup(backup["slot"], backup["number"]):
                        self.add_message(
                            f"バックアップを復元しました: スロット{backup['slot']}", Colors.GREEN
                        )
                    else:
                        self.add_message("バックアップの復元に失敗しました", Colors.RED)
                except Exception as e:
                    self.add_message(f"エラー: {str(e)}", Colors.RED)

            elif event.sym == tcod.event.KeySym.v:  # 検証
                backup = self.backups[self.selected_index]
                is_valid, errors = SaveManager.verify_save_integrity(backup["slot"])
                if is_valid:
                    self.add_message("バックアップは正常です", Colors.GREEN)
                else:
                    self.add_message(f"バックアップに問題があります: {', '.join(errors)}", Colors.RED)

            elif event.sym == tcod.event.KeySym.c:  # クリーンアップ
                deleted = SaveManager.cleanup_old_backups()
                if deleted:
                    self.add_message(f"{len(deleted)}個の古いバックアップを削除しました", Colors.YELLOW)
                    self.refresh_backups()
                else:
                    self.add_message("削除対象のバックアップはありません", Colors.LIGHT_GRAY)

        return self
