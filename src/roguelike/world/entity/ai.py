import random
import numpy as np
import tcod
import esper
from typing import Tuple, List, Optional, Any

from roguelike.world.entity.components import Position, AI, AIType, Fighter
from roguelike.world.map.game_map import GameMap
from roguelike.utils.logger import logger

class AISystem:
    """AI行動を制御するシステム"""
    
    def __init__(self, world: Any, entity_system):
        self.world = world
        self.entity_system = entity_system
    
    def update(self, game_map: GameMap, player_entity: int) -> None:
        """すべてのAI制御エンティティの行動を更新"""
        # プレイヤーの位置を取得
        if not self.world.has_component(player_entity, Position):
            return
        player_pos = self.world.component_for_entity(player_entity, Position)
        
        # AI持ちのエンティティを処理
        for entity, (ai, pos) in self.world.get_components(AI, Position):
            if ai.turns_remaining is not None:
                ai.turns_remaining -= 1
                if ai.turns_remaining <= 0:
                    # 特殊状態が終了したら通常状態に戻す
                    ai.ai_type = AIType.HOSTILE
                    ai.turns_remaining = None
                    logger.info(f"Entity {entity} returned to normal state")
            
            if ai.ai_type == AIType.HOSTILE:
                self._handle_hostile_ai(entity, pos, player_pos, game_map)
            elif ai.ai_type == AIType.CONFUSED:
                self._handle_confused_ai(entity, pos, game_map)
    
    def _handle_hostile_ai(
        self,
        entity: int,
        pos: Position,
        player_pos: Position,
        game_map: GameMap
    ) -> None:
        """敵対的AIの行動を処理"""
        # プレイヤーまでの経路を計算
        cost = np.array(game_map.walkable, dtype=np.int8)
        
        # 他のエンティティの位置をコストに反映
        for other_entity, (other_pos,) in self.world.get_components(Position):
            if other_entity != entity:
                cost[other_pos.y, other_pos.x] += 10
        
        # プレイヤーに隣接しているか確認
        distance = abs(pos.x - player_pos.x) + abs(pos.y - player_pos.y)
        
        if distance <= 1:
            # 攻撃
            logger.info(f"Entity {entity} attacks player")
            self._attack(entity, player_pos.x, player_pos.y)
        else:
            # ダイクストラ法で経路探索
            try:
                # コストマップの作成
                cost = np.array(game_map.walkable, dtype=np.int8)
                
                # 他のエンティティの位置をコストに反映
                for other_entity, (other_pos,) in self.world.get_components(Position):
                    if other_entity != entity:
                        cost[other_pos.y, other_pos.x] += 10
                
                # ゴール位置のマップを作成
                goals = np.zeros_like(cost, dtype=bool)
                goals[player_pos.y, player_pos.x] = True
                
                # ダイクストラ法でパスを計算
                path_map = tcod.path.dijkstra2d(
                    cost,
                    goals,
                    diagonal=0
                )
                
                # 次の移動位置を決定
                min_val = float('inf')
                dx, dy = 0, 0
                
                # 周囲8マスの中で最もコストの低い方向を選択
                for test_dx, test_dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                    new_x = pos.x + test_dx
                    new_y = pos.y + test_dy
                    
                    if (0 <= new_x < game_map.width and 
                        0 <= new_y < game_map.height and 
                        game_map.walkable[new_y, new_x]):
                        val = path_map[new_y, new_x]
                        if val < min_val:
                            min_val = val
                            dx, dy = test_dx, test_dy
                
                # 移動
                if dx != 0 or dy != 0:
                    self.entity_system.move_entity(entity, dx, dy)
            except Exception as e:
                logger.error(f"Pathfinding error: {e}")
                # エラーが発生した場合はランダムに移動
                dx = random.randint(-1, 1)
                dy = random.randint(-1, 1)
                new_x = pos.x + dx
                new_y = pos.y + dy
                if (0 <= new_x < game_map.width and 
                    0 <= new_y < game_map.height and 
                    game_map.walkable[new_y, new_x]):
                    self.entity_system.move_entity(entity, dx, dy)
    
    def _handle_confused_ai(
        self,
        entity: int,
        pos: Position,
        game_map: GameMap
    ) -> None:
        """混乱状態のAIの行動を処理"""
        # ランダムな方向に移動
        dx = random.randint(-1, 1)
        dy = random.randint(-1, 1)
        
        new_x = pos.x + dx
        new_y = pos.y + dy
        
        # マップ内かつ移動可能な場合のみ移動
        if (0 <= new_x < game_map.width and 
            0 <= new_y < game_map.height and 
            game_map.walkable[new_y, new_x]):
            self.entity_system.move_entity(entity, dx, dy)
    
    def _attack(self, attacker: int, target_x: int, target_y: int) -> None:
        """攻撃処理"""
        # 攻撃対象を取得
        target = self.entity_system.get_blocking_entity_at_location(target_x, target_y)
        if target is None:
            return
        
        # 攻撃者と対象の戦闘データを取得
        attacker_fighter = self.world.component_for_entity(attacker, Fighter)
        target_fighter = self.world.component_for_entity(target, Fighter)
        
        if not attacker_fighter or not target_fighter:
            return
        
        # ダメージ計算
        damage = max(0, attacker_fighter.power - target_fighter.defense)
        
        if damage > 0:
            target_fighter.hp -= damage
            logger.info(f"Entity {attacker} deals {damage} damage to entity {target}")
            
            # 対象が死亡した場合
            if target_fighter.hp <= 0:
                logger.info(f"Entity {target} is defeated")
                # 後で死亡処理を実装 