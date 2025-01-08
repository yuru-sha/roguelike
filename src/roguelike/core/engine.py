"""
The main game engine class that coordinates all game systems.
"""

from typing import Dict, Any, Optional
import numpy as np
import tcod
import tcod.event
import esper

from roguelike.core.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    MAP_WIDTH, MAP_HEIGHT,
    TORCH_RADIUS,
    Colors
)
from roguelike.game.states.game_state import GameState
from roguelike.ui.handlers.input_handler import InputHandler
from roguelike.world.map.generator.dungeon_generator import DungeonGenerator
from roguelike.world.entity.components.base import Position, Renderable, Fighter
from roguelike.world.entity.prefabs.player import create_player
from roguelike.world.spawner.spawner import populate_dungeon
from roguelike.game.actions import Action, MovementAction, WaitAction, QuitAction
from roguelike.utils.logging import GameLogger

logger = GameLogger.get_instance()

class Engine:
    """
    The main game engine class that coordinates all game systems.
    """
    
    def __init__(self):
        """Initialize the game engine."""
        logger.info("Initializing game engine")
        
        # Initialize TCOD
        self.root_console = tcod.console.Console(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.context = tcod.context.new(
            columns=SCREEN_WIDTH,
            rows=SCREEN_HEIGHT,
            title="Roguelike",
            tileset=tcod.tileset.load_tilesheet(
                'data/assets/dejavu10x10_gs_tc.png',
                32, 8, tcod.tileset.CHARMAP_TCOD
            ),
            vsync=True
        )
        
        # Initialize game state
        self.game_state = GameState()
        self.input_handler = InputHandler()
        
        # Initialize ECS world
        self.world = esper.World()
        
        # Initialize map
        self.dungeon_generator = DungeonGenerator()
        self.tiles: Optional[np.ndarray] = None
        self.fov_map: Optional[np.ndarray] = None
        
        # Player entity
        self.player: Optional[int] = None
        
        logger.info("Game engine initialized")
    
    def new_game(self) -> None:
        """Start a new game."""
        logger.info("Starting new game")
        
        # Generate first dungeon level
        self.tiles, player_pos = self.dungeon_generator.generate()
        
        # Create player
        self.player = create_player(self.world, *player_pos)
        
        # Populate dungeon
        populate_dungeon(self.world, self.dungeon_generator.rooms, self.game_state.dungeon_level)
        
        # Initialize FOV
        self._initialize_fov()
        
        # Add welcome message
        self.game_state.add_message(
            "Welcome to the Roguelike! Prepare to die...",
            Colors.WHITE
        )
        
        logger.info("New game started")
    
    def save_game(self) -> Dict[str, Any]:
        """
        Save the current game state.
        
        Returns:
            Dictionary containing the game state
        """
        logger.info("Saving game")
        return {
            'game_state': self.game_state.save_game(),
            'dungeon_level': self.game_state.dungeon_level,
            'player': self.player,
            'tiles': self.tiles.tolist(),
            'fov_map': self.fov_map.tolist()
        }
    
    def load_game(self, data: Dict[str, Any]) -> None:
        """
        Load a saved game state.
        
        Args:
            data: Dictionary containing the game state
        """
        logger.info("Loading game")
        self.game_state = GameState.load_game(data['game_state'])
        self.tiles = np.array(data['tiles'])
        self.fov_map = np.array(data['fov_map'])
        self.player = data['player']
    
    def update(self) -> None:
        """Update game state for one frame."""
        for event in tcod.event.get():
            action = self.input_handler.handle_input(event, self.game_state.state)
            
            if action:
                self._handle_action(action)
                
                # Handle enemy turn after player action
                if self.game_state.state == GameStates.ENEMY_TURN:
                    self._handle_enemy_turn()
                    self.game_state.state = GameStates.PLAYERS_TURN
    
    def render(self) -> None:
        """Render the current game state."""
        self.root_console.clear()
        
        # Render map
        self._render_map()
        
        # Render entities
        self._render_entities()
        
        # Render UI
        self._render_ui()
        
        # Present the console
        self.context.present(self.root_console)
    
    def _initialize_fov(self) -> None:
        """Initialize the field of view map."""
        self.fov_map = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=bool)
        self._recompute_fov()
    
    def _recompute_fov(self) -> None:
        """Recompute the field of view."""
        if self.player is None:
            return
            
        player_pos = self.world.component_for_entity(self.player, Position)
        transparency = np.array([[not tile.block_sight for tile in row] for row in self.tiles])
        self.fov_map = tcod.map.compute_fov(
            transparency=transparency,
            pov=(player_pos.y, player_pos.x),
            radius=10,
            light_walls=True,
            algorithm=tcod.FOV_BASIC
        )
    
    def _handle_action(self, action: Dict[str, Any]) -> None:
        """
        Handle a game action.
        
        Args:
            action: Dictionary containing the action and its parameters
        """
        action_type = action.get('action')
        
        if action_type == 'exit':
            raise SystemExit()
        
        if self.game_state.state == GameStates.PLAYERS_TURN:
            if action_type.startswith('move'):
                self._handle_movement(action_type)
            elif action_type == 'pickup':
                self._handle_pickup()
            elif action_type == 'show_inventory':
                self.game_state.state = GameStates.SHOW_INVENTORY
            elif action_type == 'drop_inventory':
                self.game_state.state = GameStates.DROP_INVENTORY
            elif action_type == 'take_stairs':
                self._handle_stairs()
            elif action_type == 'wizard_mode':
                self._handle_wizard_mode()
    
    def _handle_movement(self, direction: str) -> None:
        """
        Handle player movement.
        
        Args:
            direction: Direction to move
        """
        if self.player is None:
            return
            
        dx = dy = 0
        
        if direction == 'move_north':
            dy = -1
        elif direction == 'move_south':
            dy = 1
        elif direction == 'move_west':
            dx = -1
        elif direction == 'move_east':
            dx = 1
        elif direction == 'move_northwest':
            dx, dy = -1, -1
        elif direction == 'move_northeast':
            dx, dy = 1, -1
        elif direction == 'move_southwest':
            dx, dy = -1, 1
        elif direction == 'move_southeast':
            dx, dy = 1, 1
        
        player_pos = self.world.component_for_entity(self.player, Position)
        new_x = player_pos.x + dx
        new_y = player_pos.y + dy
        
        # Check for combat
        target = None
        for ent, (pos, fighter) in self.world.get_components(Position, Fighter):
            if pos.x == new_x and pos.y == new_y:
                target = ent
                break
        
        if target is not None:
            self._handle_combat(self.player, target)
        elif self.dungeon_generator.is_walkable(new_x, new_y):
            player_pos.x = new_x
            player_pos.y = new_y
            self._recompute_fov()
            self.game_state.state = GameStates.ENEMY_TURN
    
    def _handle_combat(self, attacker: int, defender: int) -> None:
        """
        Handle combat between two entities.
        
        Args:
            attacker: The attacking entity ID
            defender: The defending entity ID
        """
        attacker_fighter = self.world.component_for_entity(attacker, Fighter)
        defender_fighter = self.world.component_for_entity(defender, Fighter)
        
        damage = max(0, attacker_fighter.power - defender_fighter.defense)
        xp_gained = defender_fighter.take_damage(damage)
        
        if attacker == self.player:
            self.game_state.add_message(
                f"You hit the enemy for {damage} damage!",
                Colors.WHITE
            )
            
            if xp_gained > 0:
                player_level = self.world.component_for_entity(self.player, Level)
                player_level.add_xp(xp_gained)
                self.game_state.add_message(
                    f"You gain {xp_gained} experience points!",
                    Colors.YELLOW
                )
                
                if player_level.requires_level_up():
                    self.game_state.state = GameStates.LEVEL_UP
        else:
            self.game_state.add_message(
                f"The enemy hits you for {damage} damage!",
                Colors.RED
            )
            
            if defender_fighter.hp <= 0:
                self.game_state.add_message(
                    "You died!",
                    Colors.RED
                )
                self.game_state.state = GameStates.PLAYER_DEAD
    
    def _handle_enemy_turn(self) -> None:
        """Handle the enemy turn."""
        for ent, (pos, fighter, ai) in self.world.get_components(Position, Fighter, AI):
            if ent != self.player and fighter.hp > 0:
                # Simple AI: Move towards player if visible
                if self.fov_map[pos.y, pos.x]:
                    player_pos = self.world.component_for_entity(self.player, Position)
                    dx = player_pos.x - pos.x
                    dy = player_pos.y - pos.y
                    distance = max(abs(dx), abs(dy))
                    
                    if distance <= 1:
                        self._handle_combat(ent, self.player)
                    else:
                        # Move towards player
                        dx = dx // abs(dx) if dx != 0 else 0
                        dy = dy // abs(dy) if dy != 0 else 0
                        new_x = pos.x + dx
                        new_y = pos.y + dy
                        
                        if self.dungeon_generator.is_walkable(new_x, new_y):
                            pos.x = new_x
                            pos.y = new_y
    
    def _handle_pickup(self) -> None:
        """Handle item pickup."""
        if self.player is None:
            return
            
        player_pos = self.world.component_for_entity(self.player, Position)
        player_inventory = self.world.component_for_entity(self.player, Inventory)
        
        for ent, (pos, item) in self.world.get_components(Position, Item):
            if pos.x == player_pos.x and pos.y == player_pos.y:
                if player_inventory.add_item(ent):
                    self.game_state.add_message(
                        f"You pick up the {item.name}!",
                        Colors.GREEN
                    )
                    self.world.remove_component(ent, Position)
                    break
                else:
                    self.game_state.add_message(
                        "Your inventory is full!",
                        Colors.YELLOW
                    )
    
    def _handle_stairs(self) -> None:
        """Handle taking stairs to next level."""
        if self.player is None:
            return
            
        player_pos = self.world.component_for_entity(self.player, Position)
        stairs_pos = self.dungeon_generator.stairs_position
        
        if player_pos.x == stairs_pos[0] and player_pos.y == stairs_pos[1]:
            self.game_state.dungeon_level += 1
            self.game_state.add_message(
                f"You descend deeper into the dungeon... (Level {self.game_state.dungeon_level})",
                Colors.LIGHT_VIOLET
            )
            
            # Generate new level
            self.tiles, player_pos = self.dungeon_generator.generate()
            
            # Move player to new position
            player_pos_comp = self.world.component_for_entity(self.player, Position)
            player_pos_comp.x = player_pos[0]
            player_pos_comp.y = player_pos[1]
            
            # Clear old entities except player
            for ent in self.world.entities:
                if ent != self.player:
                    self.world.delete_entity(ent)
            
            # Populate new dungeon
            populate_dungeon(self.world, self.dungeon_generator.rooms, self.game_state.dungeon_level)
            
            # Recompute FOV
            self._recompute_fov()
    
    def _handle_wizard_mode(self) -> None:
        """Handle toggling wizard mode."""
        if self.game_state.toggle_wizard_mode():
            self.game_state.add_message(
                "Wizard mode activated!",
                Colors.LIGHT_VIOLET
            )
            # Heal player and reveal map
            if self.player is not None:
                fighter = self.world.component_for_entity(self.player, Fighter)
                fighter.hp = fighter.max_hp
                self.fov_map.fill(True)
        else:
            self.game_state.add_message(
                "Invalid wizard mode password!",
                Colors.RED
            )
    
    def _render_map(self) -> None:
        """Render the game map."""
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = self.fov_map[y, x]
                tile = self.tiles[y][x]
                
                if visible:
                    if tile.blocked:
                        self.root_console.print(x, y, "#", fg=Colors.LIGHT_WALL)
                    else:
                        self.root_console.print(x, y, ".", fg=Colors.LIGHT_GROUND)
                    tile.explored = True
                elif tile.explored:
                    if tile.blocked:
                        self.root_console.print(x, y, "#", fg=Colors.DARK_WALL)
                    else:
                        self.root_console.print(x, y, ".", fg=Colors.DARK_GROUND)
    
    def _render_entities(self) -> None:
        """Render all entities."""
        # Sort entities by render order
        entities_in_render_order = sorted(
            self.world.get_components(Position, Renderable),
            key=lambda x: x[1][1].render_order
        )
        
        for ent, (pos, render) in entities_in_render_order:
            if self.fov_map[pos.y, pos.x]:
                self.root_console.print(
                    pos.x, pos.y,
                    render.char,
                    fg=render.color
                )
    
    def _render_ui(self) -> None:
        """Render the user interface."""
        # Render player stats
        if self.player is not None:
            fighter = self.world.component_for_entity(self.player, Fighter)
            level = self.world.component_for_entity(self.player, Level)
            
            hp_text = f"HP: {fighter.hp}/{fighter.max_hp}"
            level_text = f"Level: {level.current_level}"
            xp_text = f"XP: {level.current_xp}/{level.xp_to_next_level}"
            
            self.root_console.print(1, SCREEN_HEIGHT - 2, hp_text, fg=Colors.WHITE)
            self.root_console.print(1, SCREEN_HEIGHT - 3, level_text, fg=Colors.WHITE)
            self.root_console.print(1, SCREEN_HEIGHT - 4, xp_text, fg=Colors.WHITE)
        
        # Render messages
        y = 1
        for message in self.game_state.messages:
            self.root_console.print(
                1, y,
                message.text,
                fg=message.color
            )
            y += 1 
    
    def run(self) -> None:
        """Run the game loop."""
        logger.info("Starting game loop")
        
        # Start new game
        self.new_game()
        
        while True:
            # Clear the console
            self.root_console.clear()
            
            # Render the game
            self.render()
            
            # Present the console
            self.context.present(self.root_console)
            
            # Handle events
            for event in tcod.event.wait():
                action = self.input_handler.handle_input(event)
                
                if action:
                    if isinstance(action, QuitAction):
                        logger.info("Quitting game")
                        raise SystemExit()
                    
                    self.handle_action(action)
    
    def render(self) -> None:
        """Render the game state."""
        # Render map
        self.render_map()
        
        # Render entities
        self.render_entities()
        
        # Render UI
        self.render_ui()
    
    def render_map(self) -> None:
        """Render the game map."""
        if self.tiles is None:
            return
            
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = self.fov_map[y, x]
                if visible:
                    self.tiles[y, x].explored = True
                    if self.tiles[y, x].blocked:
                        self.root_console.print(x, y, "#", fg=Colors.LIGHT_WALL)
                    else:
                        self.root_console.print(x, y, ".", fg=Colors.LIGHT_GROUND)
                elif self.tiles[y, x].explored:
                    if self.tiles[y, x].blocked:
                        self.root_console.print(x, y, "#", fg=Colors.DARK_WALL)
                    else:
                        self.root_console.print(x, y, ".", fg=Colors.DARK_GROUND)
    
    def render_entities(self) -> None:
        """Render all entities."""
        for ent, (pos, rend) in self.world.get_components(Position, Renderable):
            if self.fov_map[pos.y, pos.x]:
                self.root_console.print(pos.x, pos.y, rend.char, fg=rend.color)
    
    def render_ui(self) -> None:
        """Render the user interface."""
        # Render HP bar
        if self.player is not None:
            fighter = self.world.component_for_entity(self.player, Fighter)
            hp_text = f"HP: {fighter.hp}/{fighter.max_hp}"
            self.root_console.print(1, SCREEN_HEIGHT - 2, hp_text, fg=Colors.WHITE)
        
        # Render messages
        y = 1
        for message in self.game_state.messages:
            self.root_console.print(1, y, message.text, fg=message.color)
            y += 1
    
    def handle_action(self, action: Action) -> None:
        """Handle a game action."""
        if isinstance(action, MovementAction):
            self._handle_movement(action)
        elif isinstance(action, WaitAction):
            pass  # Do nothing, just pass the turn
        
        # Update FOV
        self._initialize_fov()
    
    def _handle_movement(self, action: MovementAction) -> None:
        """Handle movement action."""
        if self.player is None:
            return
            
        pos = self.world.component_for_entity(self.player, Position)
        dest_x = pos.x + action.dx
        dest_y = pos.y + action.dy
        
        if not self.tiles[dest_y, dest_x].blocked:
            pos.x = dest_x
            pos.y = dest_y
    
    def _initialize_fov(self) -> None:
        """Initialize or update the field of view."""
        if self.tiles is None or self.player is None:
            return
            
        self.fov_map = np.full((MAP_HEIGHT, MAP_WIDTH), fill_value=False, dtype=bool)
        pos = self.world.component_for_entity(self.player, Position)
        
        # Calculate FOV
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if (abs(x - pos.x) + abs(y - pos.y)) <= TORCH_RADIUS:
                    if not self.tiles[y, x].block_sight:
                        self.fov_map[y, x] = True 