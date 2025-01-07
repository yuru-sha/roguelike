from dataclasses import dataclass
from typing import Tuple, Optional
from enum import Enum, auto

class AIType(Enum):
    """AI行動タイプ"""
    HOSTILE = auto()  # 敵対的（プレイヤーを追跡して攻撃）
    CONFUSED = auto() # 混乱（ランダムに移動）

@dataclass
class Position:
    """位置コンポーネント"""
    x: int
    y: int

@dataclass
class Renderable:
    """描画コンポーネント"""
    char: str  # 表示文字
    fg_color: Tuple[int, int, int]  # 前景色
    bg_color: Tuple[int, int, int]  # 背景色

@dataclass
class Fighter:
    """戦闘コンポーネント"""
    max_hp: int
    hp: int
    defense: int
    power: int

@dataclass
class AI:
    """AI行動コンポーネント"""
    ai_type: AIType = AIType.HOSTILE
    turns_remaining: Optional[int] = None  # 特殊状態の残りターン数（Noneは無制限）

@dataclass
class Item:
    """アイテムコンポーネント"""
    weight: float = 0.0
    value: int = 0

@dataclass
class Inventory:
    """インベントリコンポーネント"""
    capacity: int = 10  # 最大所持数
    items: list = None

    def __post_init__(self):
        if self.items is None:
            self.items = []

@dataclass
class Name:
    """名前コンポーネント"""
    name: str 