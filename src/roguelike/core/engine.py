from typing import Optional, Tuple, Dict, Any
import tcod
import esper
import numpy as np

from roguelike.core.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT,
    Colors, GameStates
)
from roguelike.world.map.generator.dungeon_generator import DungeonGenerator
from roguelike.world.entity.prefabs.player import create_player, level_up_player
from roguelike.world.spawner.spawner import populate_dungeon
from roguelike.game.states.game_state import GameState
from roguelike.ui.handlers.input_handler import InputHandler
from roguelike.utils.logging import GameLogger
from roguelike.world.entity.components.base import Position, Fighter, Level, Renderable

logger = GameLogger.get_instance()

class Engine:
    """
    The main game engine class that coordinates all game systems.
    """
    
    def __init__(self):
        """Initialize the game engine."""
        logger.info("Initializing game engine")
        
        # Initialize TCOD
        tcod.console_set_custom_font(
            'data/fonts/dejavu10x10_gs_tc.png',
            tcod.FONT_TYPE_GREYSCALE | tcod.FONT_LAYOUT_TCOD
        )
        
        self.root_console = tcod.Console(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.context = tcod.context.new(
            columns=SCREEN_WIDTH,
            rows=SCREEN_HEIGHT,
            title="Roguelike",
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
            'player': self.player
            # Add more state data as needed
        }
    
    def load_game(self, data: Dict[str, Any]) -> None:
        """
        Load a saved game state.
        
        Args:
            data: Dictionary containing the game state
        """
        logger.info("Loading game")
        self.game_state = GameState.load_game(data['game_state'])
        # Load more state data as needed
    
    def update(self) -> None:
        """Update game state for one frame."""
        for event in tcod.event.get():
            action = self.input_handler.handle_input(event, self.game_state.state)
            
            if action:
                self._handle_action(action)
                
                # Handle enemy turn after player action
                if self.game_state.state == GameStates.ENEMY_TURN:
                    self._handle_enemy_turn()
    
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
        else:
            self.game_state.add_message(
                f"The enemy hits you for {damage} damage!",
                Colors.RED
            )
        
        if defender_fighter.hp <= 0:
            if defender == self.player:
                self.game_state.state = GameStates.PLAYER_DEAD
                self.game_state.add_message("You died!", Colors.RED)
            else:
                self.game_state.add_message(
                    "The enemy is dead!",
                    Colors.GREEN
                )
                # Award XP to player
                if attacker == self.player:
                    player_level = self.world.component_for_entity(self.player, Level)
                    if player_level.add_xp(xp_gained):
                        self.game_state.add_message(
                            "You level up!",
                            Colors.YELLOW
                        )
                        level_up_player(self.world, self.player)
    
    def _handle_enemy_turn(self) -> None:
        """Handle enemy turns."""
        for ent, (pos, fighter) in self.world.get_components(Position, Fighter):
            if ent == self.player:
                continue
                
            # Simple AI: Move towards player if visible
            if self.fov_map[pos.y, pos.x]:
                player_pos = self.world.component_for_entity(self.player, Position)
                dx = np.sign(player_pos.x - pos.x)
                dy = np.sign(player_pos.y - pos.y)
                
                new_x = pos.x + dx
                new_y = pos.y + dy
                
                if new_x == player_pos.x and new_y == player_pos.y:
                    self._handle_combat(ent, self.player)
                elif self.dungeon_generator.is_walkable(new_x, new_y):
                    pos.x = new_x
                    pos.y = new_y
        
        self.game_state.state = GameStates.PLAYERS_TURN
    
    def _handle_pickup(self) -> None:
        """Handle item pickup."""
        if self.player is None:
            return
            
        player_pos = self.world.component_for_entity(self.player, Position)
        
        for ent, (pos, item) in self.world.get_components(Position, Item):
            if pos.x == player_pos.x and pos.y == player_pos.y:
                if len(player_inventory.items) >= player_inventory.capacity:
                    self.game_state.add_message(
                        "Your inventory is full!",
                        Colors.YELLOW
                    )
                    return
                
                player_inventory.items.append(ent)
                self.world.delete_entity(ent)
                self.game_state.add_message(
                    "You picked up an item!",
                    Colors.GREEN
                )
                return
    
    def _handle_stairs(self) -> None:
        """Handle taking stairs to next level."""
        if self.player is None:
            return
            
        # Generate new level
        self.game_state.next_level()
        self.tiles, player_pos = self.dungeon_generator.generate()
        
        # Move player to new position
        player_pos_component = self.world.component_for_entity(self.player, Position)
        player_pos_component.x, player_pos_component.y = player_pos
        
        # Populate new level
        populate_dungeon(self.world, self.dungeon_generator.rooms, self.game_state.dungeon_level)
        
        # Recompute FOV for new level
        self._recompute_fov()
        
        self.game_state.add_message(
            f"You descend deeper into the dungeon... (Level {self.game_state.dungeon_level})",
            Colors.BLUE
        )
    
    def _handle_wizard_mode(self) -> None:
        """Handle wizard mode toggle."""
        if self.game_state.toggle_wizard_mode("wizard"):
            self.game_state.add_message(
                "Wizard mode toggled!",
                Colors.YELLOW
            )
    
    def _render_map(self) -> None:
        """Render the game map."""
        if self.tiles is None or self.fov_map is None:
            return
            
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = self.fov_map[y, x]
                wall = self.tiles[y][x].blocked
                
                if visible:
                    if wall:
                        self.root_console.tiles_rgb[x, y] = (
                            ord('#'),
                            Colors.WHITE,
                            Colors.LIGHT_WALL
                        )
                    else:
                        self.root_console.tiles_rgb[x, y] = (
                            ord('.'),
                            Colors.WHITE,
                            Colors.LIGHT_GROUND
                        )
                    self.tiles[y][x].explored = True
                elif self.tiles[y][x].explored:
                    if wall:
                        self.root_console.tiles_rgb[x, y] = (
                            ord('#'),
                            Colors.WHITE,
                            Colors.DARK_WALL
                        )
                    else:
                        self.root_console.tiles_rgb[x, y] = (
                            ord('.'),
                            Colors.WHITE,
                            Colors.DARK_GROUND
                        )
    
    def _render_entities(self) -> None:
        """Render all entities."""
        # Sort entities by render order
        entities_in_render_order = sorted(
            self.world.get_components(Position, Renderable),
            key=lambda x: x[1][1].render_order
        )
        
        for ent, (pos, render) in entities_in_render_order:
            if self.fov_map is not None and self.fov_map[pos.y, pos.x]:
                self.root_console.tiles_rgb[pos.x, pos.y] = (
                    ord(render.char),
                    render.color,
                    Colors.BLACK
                )
    
    def _render_ui(self) -> None:
        """Render the user interface."""
        # Render messages
        y = SCREEN_HEIGHT - 5
        for message in self.game_state.game_messages[-4:]:  # Show last 4 messages
            self.root_console.print(
                x=1,
                y=y,
                string=message.text,
                fg=message.color
            )
            y += 1
        
        # Render player stats
        if self.player is not None:
            fighter = self.world.component_for_entity(self.player, Fighter)
            level = self.world.component_for_entity(self.player, Level)
            
            hp_text = f"HP: {fighter.hp}/{fighter.max_hp}"
            level_text = f"Level: {level.current_level}"
            xp_text = f"XP: {level.current_xp}/{level.experience_to_next_level}"
            
            self.root_console.print(x=1, y=1, string=hp_text, fg=Colors.WHITE)
            self.root_console.print(x=1, y=2, string=level_text, fg=Colors.WHITE)
            self.root_console.print(x=1, y=3, string=xp_text, fg=Colors.WHITE)
        
        # Render wizard mode indicator
        if self.game_state.wizard_mode:
            self.root_console.print(
                x=SCREEN_WIDTH - 12,
                y=1,
                string="WIZARD MODE",
                fg=Colors.YELLOW
            ) 