from typing import Any, Optional
import esper

from roguelike.world.entity.components import Fighter, AI, AIType, Item, Name, ItemState
from roguelike.utils.logger import logger

def heal(world: esper.World, user: int, amount: int) -> bool:
    """HPを回復する"""
    if not world.has_component(user, Fighter):
        return False
        
    fighter = world.component_for_entity(user, Fighter)
    
    if fighter.hp == fighter.max_hp:
        logger.info("Your health is already full")
        return False
        
    fighter.hp = min(fighter.hp + amount, fighter.max_hp)
    logger.info(f"Your wounds start to feel better! (+{amount} HP)")
    return True

def cast_lightning(world: esper.World, user: int, damage: int, target: int) -> bool:
    """雷の魔法"""
    if not world.has_component(target, Fighter):
        return False
        
    fighter = world.component_for_entity(target, Fighter)
    fighter.hp -= damage
    
    if fighter.hp <= 0:
        logger.info(f"The lightning bolt strikes the target with a loud thunder! The target is defeated!")
    else:
        logger.info(f"The lightning bolt strikes the target with a loud thunder! The target takes {damage} damage")
    
    return True

def cast_fireball(world: esper.World, user: int, damage: int, radius: int, x: int, y: int) -> bool:
    """ファイアーボール（範囲攻撃）"""
    targets_hit = 0
    
    # 範囲内のすべてのエンティティに対してダメージを与える
    for ent, (pos, fighter) in world.get_components(Position, Fighter):
        distance = ((pos.x - x) ** 2 + (pos.y - y) ** 2) ** 0.5
        if distance <= radius:
            fighter.hp -= damage
            targets_hit += 1
            
            if fighter.hp <= 0:
                name = world.component_for_entity(ent, Name)
                logger.info(f"{name.name} is burned to a crisp!")
    
    if targets_hit > 0:
        logger.info(f"The fireball explodes, burning {targets_hit} targets!")
    else:
        logger.info("The fireball explodes, but hits nothing.")
    
    return True

def cast_confusion(world: esper.World, user: int, turns: int, target: int) -> bool:
    """混乱の魔法"""
    if not world.has_component(target, Fighter) or not world.has_component(target, AI):
        return False
        
    ai = world.component_for_entity(target, AI)
    ai.ai_type = AIType.CONFUSED
    ai.turns_remaining = turns
    
    name = world.component_for_entity(target, Name)
    logger.info(f"{name.name}'s eyes look vacant, as it starts to stumble around!")
    return True

def cast_paralyze(world: esper.World, user: int, turns: int, target: int) -> bool:
    """麻痺の魔法"""
    if not world.has_component(target, Fighter) or not world.has_component(target, AI):
        return False
        
    ai = world.component_for_entity(target, AI)
    ai.ai_type = AIType.PARALYZED
    ai.turns_remaining = turns
    
    name = world.component_for_entity(target, Name)
    logger.info(f"{name.name} is paralyzed and cannot move!")
    return True

def cast_berserk(world: esper.World, user: int, power_bonus: int, turns: int) -> bool:
    """狂戦士化（一時的に攻撃力上昇）"""
    if not world.has_component(user, Fighter):
        return False
        
    fighter = world.component_for_entity(user, Fighter)
    fighter.power += power_bonus
    
    # 効果時間後に元に戻すための処理は後で実装
    logger.info(f"You feel your power surge! (+{power_bonus} power)")
    return True 

def identify_item(world: Any, entity: int, target: Optional[int] = None) -> bool:
    """アイテムを識別する"""
    if target is None:
        return False
        
    # 対象アイテムのコンポーネントを取得
    if not world.has_component(target, Item):
        return False
        
    item = world.component_for_entity(target, Item)
    name = world.component_for_entity(target, Name)
    
    # すでに識別済みの場合は効果なし
    if item.identified:
        return False
    
    # アイテムを識別
    item.identified = True
    
    # 本来の名前がある場合は変更
    if item.true_name:
        name.name = item.true_name
    
    return True 