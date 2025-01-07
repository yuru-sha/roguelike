from dataclasses import dataclass
from typing import Tuple, Optional
from enum import Enum, auto

class AIType(Enum):
    """AI行動タイプ"""
    HOSTILE = auto()  # 敵対的（プレイヤーを追跡して攻撃）
    CONFUSED = auto() # 混乱（ランダムに移動）
    PARALYZED = auto()  # 麻痺（行動不能）
    FLEEING = auto()    # 逃走（プレイヤーから離れる）

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
class Stackable:
    """重ね置き可能なアイテムのコンポーネント"""
    def __init__(self, count: int = 1, max_count: int = 99):
        self.count = count  # 現在の個数
        self.max_count = max_count  # 最大重ね置き数

@dataclass
class ItemDetails:
    """アイテムの詳細情報コンポーネント"""
    def __init__(self, description: str = "", weight: float = 0.0, value: int = 0, identified: bool = False):
        self.description = description  # アイテムの説明文
        self.weight = weight  # 重量（kg）
        self.value = value  # 価値（ゴールド）
        self.identified = identified  # 識別状態
        self.true_name = None  # 識別後の本当の名前（未識別の場合のみ使用）

@dataclass
class Item:
    """アイテムコンポーネント"""
    def __init__(self, use_function=None, targeting=False, targeting_message=None, stackable=False, 
                 weight: float = 0.0, value: int = 0, description: str = "", identified: bool = True, **kwargs):
        self.use_function = use_function  # アイテム使用時の効果
        self.targeting = targeting  # ターゲット選択が必要か
        self.targeting_message = targeting_message  # ターゲット選択時のメッセージ
        self.function_kwargs = kwargs  # 効果関数に渡す追加パラメータ
        self.stackable = stackable  # 重ね置き可能か
        self.weight = weight  # 重量（kg）
        self.value = value  # 価値（ゴールド）
        self.description = description  # アイテムの説明文
        self.identified = identified  # 識別状態

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