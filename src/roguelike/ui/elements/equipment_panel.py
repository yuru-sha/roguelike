"""
Equipment panel UI element.
"""

from typing import Any, Dict, Optional, Tuple
import tcod

from roguelike.core.constants import Colors, EquipmentSlot
from roguelike.world.entity.components.base import Equipment, Renderable
from roguelike.ui.elements.base import UIElement
from roguelike.ui.layouts.game_layout import GameLayout

class EquipmentPanel(UIElement):
    """Panel showing equipped items."""

    def __init__(self, console: tcod.console.Console):
        """Initialize the equipment panel.
        
        Args:
            console: The console to render to
        """
        super().__init__(console, GameLayout.EQUIPMENT)
        self.title = "Equipment"
        self.slot_names = {
            EquipmentSlot.MAIN_HAND: "Main Hand",
            EquipmentSlot.OFF_HAND: "Off Hand",
            EquipmentSlot.HEAD: "Head",
            EquipmentSlot.NECK: "Neck",
            EquipmentSlot.BODY: "Body",
            EquipmentSlot.ARMS: "Arms",
            EquipmentSlot.RING_LEFT: "Left Ring",
            EquipmentSlot.RING_RIGHT: "Right Ring",
            EquipmentSlot.LEGS: "Legs",
            EquipmentSlot.FEET: "Feet",
            EquipmentSlot.CLOAK: "Cloak",
        }

    def render(self, world: Any, player_id: int) -> None:
        """Render the equipment panel.
        
        Args:
            world: The game world
            player_id: The player entity ID
        """
        super().render()
        
        # Draw title
        self.print_centered(0, f"┤ {self.title} ├", Colors.YELLOW)

        try:
            # Get player equipment
            equipment = world.component_for_entity(player_id, Equipment)
            
            # Draw equipment slots
            y = 2
            for slot in EquipmentSlot:
                slot_name = self.slot_names.get(slot, str(slot))
                item_id = equipment.slots.get(slot)
                
                if item_id is not None:
                    try:
                        item_render = world.component_for_entity(item_id, Renderable)
                        item_name = item_render.name
                        self.print(2, y, f"{slot_name}: {item_name}")
                    except Exception:
                        self.print(2, y, f"{slot_name}: ???", Colors.RED)
                else:
                    self.print(2, y, f"{slot_name}: -", Colors.DARK_GRAY)
                
                y += 1
                if y >= self.area.height - 1:
                    break

        except Exception as e:
            self.print(2, 2, "Error loading equipment", Colors.RED) 