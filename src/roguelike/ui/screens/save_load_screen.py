"""
Save/Load game screen implementation.
"""

from typing import Dict, List, Optional, Tuple
import tcod
import tcod.event
from datetime import datetime

from roguelike.core.constants import Colors, SCREEN_WIDTH, SCREEN_HEIGHT
from roguelike.utils.serialization import SaveManager

class SaveLoadScreen:
    """Screen for saving and loading games."""
    
    def __init__(self, console: tcod.console.Console, is_save: bool = True):
        """
        Initialize the save/load screen.
        
        Args:
            console: The console to render to
            is_save: True for save screen, False for load screen
        """
        self.console = console
        self.is_save = is_save
        self.selected_slot = 0
        self.saves: Dict[int, datetime] = {}
        self._refresh_saves()
        
    def _refresh_saves(self) -> None:
        """Refresh the list of save files."""
        saves = SaveManager.list_saves()
        self.saves.clear()
        
        for slot, path in saves.items():
            try:
                timestamp = datetime.fromtimestamp(path.stat().st_mtime)
                self.saves[slot] = timestamp
            except (OSError, ValueError):
                continue
    
    def render(self) -> None:
        """Render the screen."""
        self.console.clear()
        
        # Draw title
        title = "Save Game" if self.is_save else "Load Game"
        x = SCREEN_WIDTH // 2 - len(title) // 2
        self.console.print(x=x, y=2, string=title, fg=Colors.WHITE)
        
        # Draw save slots
        start_y = 5
        for i in range(10):  # 10 save slots
            slot_text = f"Slot {i}"
            if i in self.saves:
                timestamp = self.saves[i].strftime("%Y-%m-%d %H:%M:%S")
                slot_text = f"Slot {i} - {timestamp}"
            
            color = Colors.YELLOW if i == self.selected_slot else Colors.WHITE
            self.console.print(
                x=5,
                y=start_y + i,
                string=slot_text,
                fg=color
            )
        
        # Draw instructions
        instructions = [
            "↑/↓: Select slot",
            "Enter: Confirm",
            "Esc: Cancel"
        ]
        start_y = SCREEN_HEIGHT - len(instructions) - 2
        for i, text in enumerate(instructions):
            self.console.print(
                x=5,
                y=start_y + i,
                string=text,
                fg=Colors.LIGHT_GRAY
            )
    
    def handle_input(self, event: tcod.event.Event) -> Optional[Dict]:
        """
        Handle input events.
        
        Args:
            event: The input event
            
        Returns:
            Action dictionary or None
        """
        if isinstance(event, tcod.event.KeyDown):
            if event.sym == tcod.event.K_ESCAPE:
                return {'action': 'exit'}
                
            elif event.sym == tcod.event.K_UP:
                self.selected_slot = max(0, self.selected_slot - 1)
                
            elif event.sym == tcod.event.K_DOWN:
                self.selected_slot = min(9, self.selected_slot + 1)
                
            elif event.sym == tcod.event.K_RETURN:
                if self.is_save:
                    return {
                        'action': 'save',
                        'slot': self.selected_slot
                    }
                elif self.selected_slot in self.saves:
                    return {
                        'action': 'load',
                        'slot': self.selected_slot
                    }
        
        return None 