"""
Module for visualizing quest progress.
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

import tcod
from tcod.console import Console

from roguelike.core.constants import Colors
from roguelike.game.quests.quests import Quest, QuestChain, QuestStatus
from roguelike.game.quests.progress import QuestProgress
from roguelike.game.quests.statistics import QuestStatisticsManager


class QuestProgressView:
    """Class for visualizing quest progress."""

    def __init__(self, console_width: int, console_height: int):
        """Initialize progress view.

        Args:
            console_width: Width of console
            console_height: Height of console
        """
        self.console_width = console_width
        self.console_height = console_height
        self.stats_manager = QuestStatisticsManager()
        self.progress_bar_chars = ["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]
        self.animation_frame = 0
        self.last_update = datetime.now()

    def render_quest_progress(
        self,
        console: Console,
        quest: Quest,
        progress: QuestProgress,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> None:
        """Draw quest progress.

        Args:
            console: Console to draw on
            quest: Quest to draw progress for
            progress: Quest progress
            x: Starting X coordinate for drawing
            y: Starting Y coordinate for drawing
            width: Width of drawing area
            height: Height of drawing area
        """
        # Draw header
        self._draw_quest_header(console, quest, x, y, width)
        y += 2

        # Progress towards objectives
        for i, objective in enumerate(quest.objectives):
            if y >= height - 2:
                break

            current, required = objective.get_progress()
            percentage = (current / required) * 100 if required > 0 else 0

            # Objective description
            desc = f"{objective.description} ({current}/{required})"
            color = Colors.GREEN if objective.completed else Colors.WHITE
            console.print(x + 2, y, desc, color)

            # Animated progress bar
            bar_width = width - 4
            self._draw_animated_progress_bar(
                console, x + 2, y + 1, bar_width, percentage
            )

            # Completion time display
            if objective.completed and progress.completion_time:
                time_str = progress.completion_time.strftime("%Y-%m-%d %H:%M:%S")
                console.print(
                    x + width - len(time_str) - 2,
                    y,
                    time_str,
                    Colors.LIGHT_GRAY
                )

            y += 3

        # Time information display
        if progress.start_time:
            elapsed = datetime.now() - progress.start_time
            time_str = self._format_elapsed_time(elapsed)
            console.print(
                x + 2,
                y,
                f"Time elapsed: {time_str}",
                Colors.YELLOW
            )

        # Quest status display
        status_icon = self._get_status_icon(quest.status)
        status_color = self._get_status_color(quest.status)
        console.print(
            x + width - 4,
            y,
            f"{status_icon}",
            status_color
        )

    def render_chain_progress(
        self,
        console: Console,
        chain: QuestChain,
        quests: Dict[str, Quest],
        quest_progress: Dict[str, QuestProgress],
        x: int,
        y: int,
        width: int,
        height: int
    ) -> None:
        """Draw progress for a quest chain.

        Args:
            console: Console to draw on
            chain: Quest chain to draw progress for
            quests: Quest dictionary
            quest_progress: Quest progress dictionary
            x: Starting X coordinate for drawing
            y: Starting Y coordinate for drawing
            width: Width of drawing area
            height: Height of drawing area
        """
        # Chain header
        header = f"≡ {chain.name} ≡"
        header_x = x + (width - len(header)) // 2
        console.print(header_x, y, header, Colors.YELLOW)
        console.draw_rect(x, y + 1, width, 1, "─", Colors.WHITE)
        y += 2

        # Progress for each quest in the chain
        for i, quest_id in enumerate(chain.quest_ids):
            if y >= height - 2:
                break

            quest = quests.get(quest_id)
            if not quest:
                continue

            progress = quest_progress.get(quest_id)
            if not progress:
                continue

            # Connection line between quests
            if i > 0:
                console.print(x + width // 2, y - 1, "↓", Colors.WHITE)

            # Quest status display
            status_icon = self._get_status_icon(quest.status)
            status_color = self._get_status_color(quest.status)
            
            # Quest name and progress
            name = f"{status_icon} {quest.name}"
            console.print(x + 2, y, name, status_color)

            if progress.completion_time:
                time_str = progress.completion_time.strftime("%Y-%m-%d %H:%M:%S")
                console.print(
                    x + width - len(time_str) - 2,
                    y,
                    time_str,
                    Colors.LIGHT_GRAY
                )

            # Overall progress
            total_progress = self._calculate_quest_progress(quest, progress)
            bar_width = width - 4
            self._draw_animated_progress_bar(
                console, x + 2, y + 1, bar_width, total_progress
            )

            y += 3

        # Overall progress for the chain
        if y < height - 2:
            total_chain_progress = self._calculate_chain_progress(
                chain, quests, quest_progress
            )
            console.draw_rect(x, y, width, 1, "─", Colors.WHITE)
            y += 1
            console.print(
                x + 2,
                y,
                f"Chain progress: {total_chain_progress:.1f}%",
                Colors.YELLOW
            )

    def render_progress_summary(
        self,
        console: Console,
        quest: Quest,
        progress: QuestProgress,
        statistics: Dict[str, Any],
        x: int,
        y: int,
        width: int,
        height: int
    ) -> None:
        """Draw progress summary.

        Args:
            console: Console to draw on
            quest: Quest to draw summary for
            progress: Quest progress
            statistics: Statistics
            x: Starting X coordinate for drawing
            y: Starting Y coordinate for drawing
            width: Width of drawing area
            height: Height of drawing area
        """
        # Header
        header = "≡ Progress Summary ≡"
        header_x = x + (width - len(header)) // 2
        console.print(header_x, y, header, Colors.YELLOW)
        console.draw_rect(x, y + 1, width, 1, "─", Colors.WHITE)
        y += 2

        # Basic information
        self._draw_stat_line(
            console, x + 2, y,
            "Quest",
            quest.name,
            Colors.WHITE
        )
        y += 1

        self._draw_stat_line(
            console, x + 2, y,
            "Status",
            quest.status.name,
            self._get_status_color(quest.status)
        )
        y += 1

        if progress.start_time:
            elapsed = datetime.now() - progress.start_time
            time_str = self._format_elapsed_time(elapsed)
            self._draw_stat_line(
                console, x + 2, y,
                "Elapsed Time",
                time_str,
                Colors.YELLOW
            )
        y += 2

        # Statistics
        console.print(x + 2, y, "≡ Statistics ≡", Colors.LIGHT_BLUE)
        y += 1

        success_rate = statistics.get("success_rate", 0) * 100
        self._draw_stat_line(
            console, x + 2, y,
            "Success Rate",
            f"{success_rate:.1f}%",
            self._get_percentage_color(success_rate)
        )
        y += 1

        avg_time = statistics.get("average_completion_time", 0)
        if avg_time > 0:
            time_str = self._format_elapsed_time(timedelta(seconds=avg_time))
            self._draw_stat_line(
                console, x + 2, y,
                "Average Completion Time",
                time_str,
                Colors.WHITE
            )
        y += 2

        # Checkpoints
        if progress.checkpoints:
            console.print(x + 2, y, "≡ Checkpoints ≡", Colors.LIGHT_GREEN)
            y += 1

            for checkpoint in progress.checkpoints[-3:]:  # Show latest 3
                if y >= height - 1:
                    break
                timestamp = datetime.fromisoformat(checkpoint["timestamp"])
                time_str = timestamp.strftime("%H:%M:%S")
                desc = checkpoint["description"]
                console.print(
                    x + 2, y,
                    f"{time_str} - {desc}",
                    Colors.LIGHT_GRAY
                )
                y += 1

    def _draw_animated_progress_bar(
        self,
        console: Console,
        x: int,
        y: int,
        width: int,
        percentage: float
    ) -> None:
        """Draw animated progress bar.

        Args:
            console: Console to draw on
            x: X coordinate
            y: Y coordinate
            width: Bar width
            percentage: Progress percentage (0-100)
        """
        # Update animation frame
        now = datetime.now()
        if (now - self.last_update).total_seconds() > 0.1:
            self.animation_frame = (self.animation_frame + 1) % len(self.progress_bar_chars)
            self.last_update = now

        filled_width = int(width * percentage / 100)
        partial_width = (width * percentage / 100) - filled_width
        partial_char_index = min(
            int(partial_width * len(self.progress_bar_chars)),
            len(self.progress_bar_chars) - 1
        )

        # Draw bar
        color = self._get_percentage_color(percentage)
        console.draw_rect(x, y, width, 1, "░", Colors.DARK_GRAY)
        if filled_width > 0:
            console.draw_rect(x, y, filled_width, 1, "█", color)
        if filled_width < width:
            partial_char = self.progress_bar_chars[partial_char_index]
            console.print(x + filled_width, y, partial_char, color)

        # Percentage display
        percent_str = f"{percentage:.1f}%"
        percent_x = x + (width - len(percent_str)) // 2
        console.print(percent_x, y, percent_str, Colors.WHITE)

    def _draw_stat_line(
        self,
        console: Console,
        x: int,
        y: int,
        label: str,
        value: str,
        color: Tuple[int, int, int]
    ) -> None:
        """Draw a single line of statistics.

        Args:
            console: Console to draw on
            x: X coordinate
            y: Y coordinate
            label: Label
            value: Value
            color: Color
        """
        console.print(x, y, f"{label}: ", Colors.LIGHT_GRAY)
        console.print(x + len(label) + 2, y, value, color)

    def _get_status_color(self, status: QuestStatus) -> Tuple[int, int, int]:
        """Get color based on quest status.

        Args:
            status: Quest status

        Returns:
            RGB color value
        """
        colors = {
            QuestStatus.NOT_STARTED: Colors.GRAY,
            QuestStatus.IN_PROGRESS: Colors.YELLOW,
            QuestStatus.COMPLETED: Colors.GREEN,
            QuestStatus.FAILED: Colors.RED
        }
        return colors.get(status, Colors.WHITE)

    def _get_status_icon(self, status: QuestStatus) -> str:
        """Get status icon based on quest status.

        Args:
            status: Quest status

        Returns:
            Status icon
        """
        icons = {
            QuestStatus.NOT_STARTED: "○",
            QuestStatus.IN_PROGRESS: "◎",
            QuestStatus.COMPLETED: "◉",
            QuestStatus.FAILED: "×"
        }
        return icons.get(status, "?")

    def _get_percentage_color(self, percentage: float) -> Tuple[int, int, int]:
        """Get color based on progress percentage.

        Args:
            percentage: Progress percentage (0-100)

        Returns:
            RGB color value
        """
        if percentage >= 100:
            return Colors.GREEN
        elif percentage >= 75:
            return Colors.LIGHT_GREEN
        elif percentage >= 50:
            return Colors.YELLOW
        elif percentage >= 25:
            return Colors.LIGHT_RED
        return Colors.RED

    def _calculate_quest_progress(
        self,
        quest: Quest,
        progress: QuestProgress
    ) -> float:
        """Calculate overall progress for a quest.

        Args:
            quest: Quest to calculate progress for
            progress: Quest progress

        Returns:
            Progress percentage (0-100)
        """
        if not quest.objectives:
            return 0.0

        total = 0.0
        for i, objective in enumerate(quest.objectives):
            current, required = objective.get_progress()
            total += (current / required) if required > 0 else 0

        return (total / len(quest.objectives)) * 100

    def _calculate_chain_progress(
        self,
        chain: QuestChain,
        quests: Dict[str, Quest],
        quest_progress: Dict[str, QuestProgress]
    ) -> float:
        """Calculate overall progress for a quest chain.

        Args:
            chain: Quest chain to calculate progress for
            quests: Quest dictionary
            quest_progress: Quest progress dictionary

        Returns:
            Progress percentage (0-100)
        """
        if not chain.quest_ids:
            return 0.0

        total = 0.0
        for quest_id in chain.quest_ids:
            quest = quests.get(quest_id)
            progress = quest_progress.get(quest_id)
            if quest and progress:
                total += self._calculate_quest_progress(quest, progress)

        return total / len(chain.quest_ids)

    def _format_elapsed_time(self, elapsed: timedelta) -> str:
        """Format elapsed time as string.

        Args:
            elapsed: Elapsed time

        Returns:
            Formatted time string
        """
        total_seconds = int(elapsed.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes:02d}m {seconds:02d}s"
        elif minutes > 0:
            return f"{minutes}m {seconds:02d}s"
        return f"{seconds}s" 