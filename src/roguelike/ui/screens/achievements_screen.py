"""
Achievement screen implementation.
"""

import logging
from typing import List, Optional, Tuple

import tcod

from roguelike.core.constants import Colors
from roguelike.game.achievements import Achievement, AchievementManager

logger = logging.getLogger(__name__)


class AchievementsScreen:
    """Screen for displaying achievements."""

    def __init__(self, console: tcod.console.Console):
        """Initialize the achievements screen.
        
        Args:
            console: The console to render to
        """
        self.console = console
        self.achievement_manager = AchievementManager.get_instance()
        self.selected_index = 0
        self.scroll_offset = 0
        self.max_visible_items = self.console.height - 4  # Reserve space for header and footer

    def render(self) -> None:
        """Render the achievements screen."""
        try:
            self.console.clear()

            # Get all achievements
            achievements = self._get_sorted_achievements()
            total_points = self.achievement_manager.get_achievement_points()
            unlocked_count = len([a for a in achievements if a.unlocked])

            # Draw header
            header = f" Achievements ({unlocked_count}/{len(achievements)}) - {total_points} points "
            header_x = (self.console.width - len(header)) // 2
            self.console.print(header_x, 1, header, Colors.YELLOW)
            self.console.draw_rect(0, 2, self.console.width, 1, "─", Colors.WHITE)

            # Draw achievements
            visible_achievements = achievements[self.scroll_offset:self.scroll_offset + self.max_visible_items]
            for i, achievement in enumerate(visible_achievements):
                y = i + 3
                is_selected = i + self.scroll_offset == self.selected_index
                self._draw_achievement(achievement, y, is_selected)

            # Draw footer
            self.console.draw_rect(0, self.console.height - 1, self.console.width, 1, "─", Colors.WHITE)
            footer = " ↑/↓: Navigate   ESC: Close "
            footer_x = (self.console.width - len(footer)) // 2
            self.console.print(footer_x, self.console.height - 1, footer, Colors.WHITE)

            logger.debug("Rendered achievements screen")

        except Exception as e:
            logger.error(f"Error rendering achievements screen: {e}", exc_info=True)

    def _draw_achievement(self, achievement: Achievement, y: int, selected: bool) -> None:
        """Draw a single achievement entry.
        
        Args:
            achievement: The achievement to draw
            y: The y-coordinate to draw at
            selected: Whether this achievement is selected
        """
        try:
            # Determine colors
            if selected:
                bg_color = Colors.DARK_GRAY
                fg_color = Colors.WHITE
            else:
                bg_color = None
                fg_color = Colors.WHITE if achievement.unlocked else Colors.DARK_GRAY

            # Draw background if selected
            if selected:
                self.console.draw_rect(0, y, self.console.width, 1, " ", bg=bg_color)

            # Draw achievement icon
            icon = "★" if achievement.unlocked else "☆"
            self.console.print(1, y, icon, fg_color, bg_color)

            # Draw achievement name
            name = achievement.name if achievement.unlocked or not achievement.hidden else "???"
            self.console.print(3, y, name, fg_color, bg_color)

            # Draw points
            points = f"{achievement.points}pts"
            points_x = self.console.width - len(points) - 1
            self.console.print(points_x, y, points, fg_color, bg_color)

            # Draw description if selected
            if selected and (achievement.unlocked or not achievement.hidden):
                desc_y = min(y + 1, self.console.height - 3)
                desc = f"  {achievement.description}"
                self.console.print(0, desc_y, desc, Colors.LIGHT_GRAY)

                if achievement.unlocked and achievement.unlock_date:
                    date_str = f"Unlocked: {achievement.unlock_date.strftime('%Y-%m-%d %H:%M:%S')}"
                    date_x = self.console.width - len(date_str) - 1
                    self.console.print(date_x, desc_y, date_str, Colors.LIGHT_GRAY)

        except Exception as e:
            logger.error(f"Error drawing achievement: {e}", exc_info=True)

    def _get_sorted_achievements(self) -> List[Achievement]:
        """Get sorted list of achievements.
        
        Returns:
            List of achievements sorted by unlock status and name
        """
        achievements = list(self.achievement_manager.achievements.values())
        return sorted(achievements, key=lambda a: (not a.unlocked, a.name))

    def handle_input(self, event: tcod.event.Event) -> Optional[dict]:
        """Handle input events.
        
        Args:
            event: The input event to handle
            
        Returns:
            Action dict if input was handled, None otherwise
        """
        try:
            if isinstance(event, tcod.event.KeyDown):
                if event.sym == tcod.event.K_UP:
                    self._move_cursor(-1)
                    return {}
                elif event.sym == tcod.event.K_DOWN:
                    self._move_cursor(1)
                    return {}
                elif event.sym == tcod.event.K_ESCAPE:
                    return {"action": "exit"}

            return None

        except Exception as e:
            logger.error(f"Error handling input: {e}", exc_info=True)
            return None

    def _move_cursor(self, dy: int) -> None:
        """Move the selection cursor.
        
        Args:
            dy: Amount to move cursor vertically
        """
        try:
            achievements = self._get_sorted_achievements()
            new_index = self.selected_index + dy
            
            if 0 <= new_index < len(achievements):
                self.selected_index = new_index
                
                # Adjust scroll if selection would be off screen
                if self.selected_index < self.scroll_offset:
                    self.scroll_offset = self.selected_index
                elif self.selected_index >= self.scroll_offset + self.max_visible_items:
                    self.scroll_offset = self.selected_index - self.max_visible_items + 1

        except Exception as e:
            logger.error(f"Error moving cursor: {e}", exc_info=True) 