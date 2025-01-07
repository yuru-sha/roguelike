from typing import Optional
import esper

from roguelike.world.entity.components import Fighter
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

def cast_fireball(world: esper.World, user: int, damage: int, target: int) -> bool:
    """ファイアーボール"""
    if not world.has_component(target, Fighter):
        return False
        
    fighter = world.component_for_entity(target, Fighter)
    fighter.hp -= damage
    
    if fighter.hp <= 0:
        logger.info(f"The fireball explodes, burning the target to a crisp! The target is defeated!")
    else:
        logger.info(f"The fireball explodes, burning the target! The target takes {damage} damage")
    
    return True

def cast_confusion(world: esper.World, user: int, turns: int, target: int) -> bool:
    """混乱の魔法"""
    if not world.has_component(target, Fighter):
        return False
        
    # 混乱状態の実装は後で
    logger.info(f"The target's eyes look vacant, as it starts to stumble around!")
    return True 