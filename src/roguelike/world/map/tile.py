from dataclasses import dataclass
from typing import NamedTuple

class TileGraphics(NamedTuple):
    """タイルの見た目を定義するクラス"""
    ch: int  # Unicode文字コード
    fg: tuple[int, int, int]  # 前景色 (R, G, B)
    bg: tuple[int, int, int]  # 背景色 (R, G, B)

@dataclass
class Tile:
    """マップタイルを表すクラス"""
    walkable: bool
    transparent: bool
    dark: TileGraphics  # 未探索時の見た目
    light: TileGraphics  # 探索済みの見た目
    explored: bool = False  # 一度でも見たことがあるか

    def with_walkable(self, walkable: bool) -> "Tile":
        """歩行可能性を変更した新しいタイルを返す"""
        return Tile(
            walkable=walkable,
            transparent=self.transparent,
            dark=self.dark,
            light=self.light,
            explored=self.explored
        )

# タイルの種類を定義
floor = Tile(
    walkable=True,  # 歩行可能
    transparent=True,  # 視線が通る
    dark=TileGraphics(ord("."), (40, 40, 40), (0, 0, 0)),  # 暗い床
    light=TileGraphics(ord("."), (200, 200, 200), (0, 0, 0))  # 明るい床
)

wall = Tile(
    walkable=False,  # 歩行不可
    transparent=False,  # 視線が通らない
    dark=TileGraphics(ord("#"), (40, 40, 40), (0, 0, 0)),  # 暗い壁
    light=TileGraphics(ord("#"), (200, 200, 200), (0, 0, 0))  # 明るい壁
) 