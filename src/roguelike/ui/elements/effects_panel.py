"""
Status effects panel UI element.
"""

from typing import Any, Dict, Optional, Tuple
import tcod

from roguelike.core.constants import Colors, StatusEffect
from roguelike.world.entity.components.base import StatusEffects
from roguelike.ui.elements.base import UIElement
from roguelike.ui.layouts.game_layout import GameLayout

class EffectsPanel(UIElement):
    """Panel showing active status effects."""

    def __init__(self, console: tcod.console.Console):
        """Initialize the effects panel.
        
        Args:
            console: The console to render to
        """
        super().__init__(console, GameLayout.EFFECTS)
        self.title = "Effects"
        self.effect_colors = {
            StatusEffect.POISONED: Colors.GREEN,
            StatusEffect.BURNING: Colors.RED,
            StatusEffect.FROZEN: Colors.LIGHT_BLUE,
            StatusEffect.STUNNED: Colors.YELLOW,
            StatusEffect.HASTED: Colors.LIGHT_VIOLET,
            StatusEffect.SLOWED: Colors.BROWN,
            StatusEffect.INVISIBLE: Colors.CYAN,
            StatusEffect.REGENERATING: Colors.LIGHT_GREEN,
        }

    def render(self, world: Any, player_id: int) -> None:
        """Render the effects panel.
        
        Args:
            world: The game world
            player_id: The player entity ID
        """
        super().render()
        
        # Draw title
        self.print_centered(0, f"┤ {self.title} ├", Colors.YELLOW)

        try:
            # Get player status effects
            effects = world.component_for_entity(player_id, StatusEffects)
            
            if not effects.effects:
                self.print(2, 2, "No active effects", Colors.DARK_GRAY)
                return

            # Draw active effects
            y = 2
            for effect, data in effects.effects.items():
                effect_name = effect.name.title()
                effect_color = self.effect_colors.get(effect, Colors.WHITE)
                
                # Show effect name and duration
                self.print(
                    2, y,
                    f"{effect_name} ({data.duration})",
                    effect_color
                )
                
                y += 1
                if y >= self.area.height - 1:
                    break

        except Exception as e:
            self.print(2, 2, "Error loading effects", Colors.RED) 