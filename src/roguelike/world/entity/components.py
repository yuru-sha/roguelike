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
    def __init__(self, use_function=None, targeting=False, targeting_message=None, **kwargs):
        self.use_function = use_function  # アイテム使用時の効果
        self.targeting = targeting  # ターゲット選択が必要か
        self.targeting_message = targeting_message  # ターゲット選択時のメッセージ
        self.function_kwargs = kwargs  # 効果関数に渡す追加パラメータ

@dataclass
class Inventory:
    """インベントリコンポーネント"""
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.items = []  # 所持アイテムのリスト

@dataclass
class Name:
    """名前コンポーネント"""
    name: str 

class Equipment:
    """装備品コンポーネント"""
    def __init__(self, slot: str, power_bonus=0, defense_bonus=0):
        self.slot = slot  # 装備スロット（weapon/armor）
        self.power_bonus = power_bonus  # 攻撃力ボーナス
        self.defense_bonus = defense_bonus  # 防御力ボーナス
        self.is_equipped = False  # 装備中かどうか

class Equippable:
    """装備可能コンポーネント"""
    def __init__(self):
        self.equipped_by = None  # 装備しているエンティティ 