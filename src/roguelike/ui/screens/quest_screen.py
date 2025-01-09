"""
Quest screen implementation.
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

import tcod

from roguelike.core.constants import Colors
from roguelike.game.quests.quests import Quest, QuestManager, QuestStatus, QuestChain, QuestLogEntry

logger = logging.getLogger(__name__)


class QuestScreen:
    def __init__(self, console: tcod.console.Console, player_level: int):
        """Initialize the quest screen.
        
        Args:
            console: The console to render to
            player_level: Current player level
        """
        self.console = console
        self.quest_manager = QuestManager.get_instance()
        self.player_level = player_level
        self.selected_index = 0
        self.scroll_offset = 0
        self.max_visible_items = self.console.height - 4
        self.view_mode = "available"  # "available", "active", "completed", "failed", "chains", "log"
        self.show_chain_details = False
        self.show_quest_history = False
        self.current_history: List[QuestLogEntry] = []

    def render(self) -> None:
        """Render the quest screen."""
        try:
            self.console.clear()

            if self.view_mode == "log":
                self._render_quest_log()
                return
            elif self.view_mode == "chains":
                if self.show_chain_details:
                    self._render_chain_details()
                else:
                    self._render_quest_chains()
                return

            # Get quests based on current view
            if self.view_mode == "available":
                quests_data = self.quest_manager.get_available_quests(self.player_level)
                quests = [q for q, _ in quests_data]
                failure_reasons = {q: r for q, r in quests_data}
            elif self.view_mode == "active":
                quests = self.quest_manager.get_active_quests()
                failure_reasons = {}
            elif self.view_mode == "completed":
                quests = self.quest_manager.get_completed_quests()
                failure_reasons = {}
            else:  # failed
                quests = self.quest_manager.get_failed_quests()
                failure_reasons = {}

            # Draw header
            header = f" {self.view_mode.title()} Quests ({len(quests)}) "
            header_x = (self.console.width - len(header)) // 2
            header_color = Colors.RED if self.view_mode == "failed" else Colors.YELLOW
            self.console.print(header_x, 1, header, header_color)
            self.console.draw_rect(0, 2, self.console.width, 1, "─", Colors.WHITE)

            # Draw quests
            visible_quests = quests[self.scroll_offset:self.scroll_offset + self.max_visible_items]
            for i, quest in enumerate(visible_quests):
                y = i + 3
                is_selected = i + self.scroll_offset == self.selected_index
                failure_reason = failure_reasons.get(quest)
                self._draw_quest(quest, y, is_selected, failure_reason)

            # Draw footer
            self._draw_footer()

        except Exception as e:
            logger.error(f"Error rendering quest screen: {e}", exc_info=True)

    def _render_quest_chains(self) -> None:
        """Render the quest chains view."""
        try:
            # Draw header
            header = " Quest Chains "
            header_x = (self.console.width - len(header)) // 2
            self.console.print(header_x, 1, header, Colors.BLUE)
            self.console.draw_rect(0, 2, self.console.width, 1, "─", Colors.WHITE)

            # Get available and completed chains
            available_chains = self.quest_manager.get_available_quest_chains()
            completed_chains = self.quest_manager.get_completed_quest_chains()
            all_chains = available_chains + completed_chains

            # Draw chains
            visible_chains = all_chains[self.scroll_offset:self.scroll_offset + self.max_visible_items]
            for i, chain in enumerate(visible_chains):
                y = i + 3
                is_selected = i + self.scroll_offset == self.selected_index
                self._draw_quest_chain(chain, y, is_selected)

            # Draw footer
            self._draw_footer()

        except Exception as e:
            logger.error(f"Error rendering quest chains: {e}", exc_info=True)

    def _render_chain_details(self) -> None:
        """Render detailed view of selected quest chain."""
        try:
            # Get current chain
            available_chains = self.quest_manager.get_available_quest_chains()
            completed_chains = self.quest_manager.get_completed_quest_chains()
            all_chains = available_chains + completed_chains
            if not (0 <= self.selected_index < len(all_chains)):
                return
            
            chain = all_chains[self.selected_index]

            # Draw header
            header = f" {chain.name} "
            header_x = (self.console.width - len(header)) // 2
            self.console.print(header_x, 1, header, Colors.BLUE)
            self.console.draw_rect(0, 2, self.console.width, 1, "─", Colors.WHITE)

            # Draw description
            y = 3
            self.console.print(2, y, chain.description, Colors.LIGHT_GRAY)
            y += 2

            # Draw quest list
            self.console.print(2, y, "Quests in this chain:", Colors.WHITE)
            y += 1

            for quest_id in chain.quest_ids:
                quest = self.quest_manager.quests.get(quest_id)
                if not quest:
                    continue

                # Draw quest status
                if quest.status == QuestStatus.COMPLETED:
                    status = "✓"
                    color = Colors.GREEN
                elif quest.status == QuestStatus.FAILED:
                    status = "×"
                    color = Colors.RED
                elif quest.status == QuestStatus.IN_PROGRESS:
                    status = "⋯"
                    color = Colors.YELLOW
                else:
                    status = "□"
                    color = Colors.WHITE

                quest_text = f"  {status} {quest.name}"
                self.console.print(2, y, quest_text, color)
                y += 1

            # Draw chain rewards if completed
            if chain.completed:
                y += 1
                self.console.print(2, y, "Chain Rewards:", Colors.LIGHT_GREEN)
                y += 1

                bonus_gold = int(chain.chain_reward.gold * chain.chain_reward.bonus_multiplier)
                bonus_xp = int(chain.chain_reward.experience * chain.chain_reward.bonus_multiplier)
                
                reward_text = f"  • {bonus_gold} gold, {bonus_xp} XP"
                self.console.print(2, y, reward_text, Colors.LIGHT_GREEN)
                y += 1

                if chain.chain_reward.unique_items:
                    self.console.print(2, y, "  • Unique Items:", Colors.LIGHT_GREEN)
                    y += 1
                    for item in chain.chain_reward.unique_items:
                        self.console.print(4, y, f"- {item}", Colors.LIGHT_GREEN)
                        y += 1

            # Draw footer
            self._draw_footer()

        except Exception as e:
            logger.error(f"Error rendering chain details: {e}", exc_info=True)

    def _draw_quest_chain(self, chain: QuestChain, y: int, selected: bool) -> None:
        """Draw a single quest chain entry."""
        try:
            # Determine colors
            if selected:
                bg_color = Colors.DARK_GRAY
                fg_color = Colors.WHITE
            else:
                bg_color = None
                fg_color = Colors.WHITE if not chain.completed else Colors.GREEN

            # Draw background if selected
            if selected:
                self.console.draw_rect(0, y, self.console.width, 1, " ", bg=bg_color)

            # Draw chain status icon
            icon = "✓" if chain.completed else "⋯"
            self.console.print(1, y, icon, fg_color, bg_color)

            # Draw chain name
            self.console.print(3, y, chain.name, fg_color, bg_color)

            # Draw progress
            if not chain.completed:
                completed_quests = sum(
                    1 for quest_id in chain.quest_ids
                    if (quest := self.quest_manager.quests.get(quest_id))
                    and quest.status == QuestStatus.COMPLETED
                )
                total_quests = len(chain.quest_ids)
                progress = f"{completed_quests}/{total_quests}"
                progress_x = self.console.width - len(progress) - 1
                self.console.print(progress_x, y, progress, fg_color, bg_color)

        except Exception as e:
            logger.error(f"Error drawing quest chain: {e}", exc_info=True)

    def _draw_footer(self) -> None:
        """Draw the screen footer."""
        self.console.draw_rect(0, self.console.height - 1, self.console.width, 1, "─", Colors.WHITE)
        
        if self.view_mode == "chains" and self.show_chain_details:
            footer = " ESC: Back "
        elif self.view_mode == "log" and self.show_quest_history:
            footer = " ESC: Back   ENTER: View Details "
        else:
            footer = " ↑/↓: Navigate   TAB: Change View   ENTER: Select   ESC: Close "
        
        footer_x = (self.console.width - len(footer)) // 2
        self.console.print(footer_x, self.console.height - 1, footer, Colors.WHITE)

    def _render_quest_log(self) -> None:
        """Render the quest log view."""
        try:
            # Draw header
            header = " Quest Log "
            header_x = (self.console.width - len(header)) // 2
            self.console.print(header_x, 1, header, Colors.BLUE)
            self.console.draw_rect(0, 2, self.console.width, 1, "─", Colors.WHITE)

            if self.show_quest_history:
                self._render_quest_history()
            else:
                self._render_recent_events()

            # Draw footer
            self._draw_footer()

        except Exception as e:
            logger.error(f"Error rendering quest log: {e}", exc_info=True)

    def _render_recent_events(self) -> None:
        """Render recent quest events."""
        try:
            entries = self.quest_manager.get_recent_quest_events()
            visible_entries = entries[self.scroll_offset:self.scroll_offset + self.max_visible_items]

            for i, entry in enumerate(visible_entries):
                y = i + 3
                is_selected = i + self.scroll_offset == self.selected_index
                self._draw_log_entry(entry, y, is_selected)

        except Exception as e:
            logger.error(f"Error rendering recent events: {e}", exc_info=True)

    def _render_quest_history(self) -> None:
        """Render history for selected quest or chain."""
        try:
            visible_entries = self.current_history[self.scroll_offset:self.scroll_offset + self.max_visible_items]

            for i, entry in enumerate(visible_entries):
                y = i + 3
                is_selected = i + self.scroll_offset == self.selected_index
                self._draw_log_entry(entry, y, is_selected)

        except Exception as e:
            logger.error(f"Error rendering quest history: {e}", exc_info=True)

    def _draw_log_entry(self, entry: QuestLogEntry, y: int, selected: bool) -> None:
        """Draw a single log entry."""
        try:
            # Determine colors
            if selected:
                bg_color = Colors.DARK_GRAY
                fg_color = Colors.WHITE
            else:
                bg_color = None
                fg_color = self._get_entry_color(entry.entry_type)

            # Draw background if selected
            if selected:
                self.console.draw_rect(0, y, self.console.width, 1, " ", bg=bg_color)

            # Format timestamp
            timestamp = entry.timestamp.strftime("%H:%M:%S")
            self.console.print(1, y, timestamp, fg_color, bg_color)

            # Draw message
            message_x = len(timestamp) + 2
            self.console.print(message_x, y, entry.message, fg_color, bg_color)

            # Draw details if selected
            if selected and entry.details:
                details_y = min(y + 1, self.console.height - 3)
                self._draw_entry_details(entry, details_y)

        except Exception as e:
            logger.error(f"Error drawing log entry: {e}", exc_info=True)

    def _draw_entry_details(self, entry: QuestLogEntry, y: int) -> None:
        """Draw details for a log entry."""
        try:
            if not entry.details:
                return

            if entry.entry_type == "complete":
                self.console.print(2, y, "Rewards:", Colors.LIGHT_GREEN)
                y += 1
                reward_text = f"  • {entry.details['reward_gold']} gold, {entry.details['reward_xp']} XP"
                if entry.details['reward_items']:
                    reward_text += f", {', '.join(entry.details['reward_items'])}"
                self.console.print(2, y, reward_text, Colors.LIGHT_GREEN)

            elif entry.entry_type == "fail":
                self.console.print(2, y, f"Failure reason: {entry.details['reason']}", Colors.RED)

            elif entry.entry_type == "chain_complete":
                self.console.print(2, y, "Chain Rewards:", Colors.LIGHT_GREEN)
                y += 1
                self.console.print(2, y, f"  • {entry.details['bonus_gold']} gold, {entry.details['bonus_xp']} XP", Colors.LIGHT_GREEN)
                y += 1
                if entry.details['unique_items']:
                    self.console.print(2, y, "  • Unique Items:", Colors.LIGHT_GREEN)
                    y += 1
                    for item in entry.details['unique_items']:
                        self.console.print(4, y, f"- {item}", Colors.LIGHT_GREEN)
                        y += 1

        except Exception as e:
            logger.error(f"Error drawing entry details: {e}", exc_info=True)

    def _get_entry_color(self, entry_type: str) -> int:
        """Get color for log entry type."""
        return {
            "start": Colors.LIGHT_BLUE,
            "progress": Colors.WHITE,
            "complete": Colors.GREEN,
            "fail": Colors.RED,
            "chain_progress": Colors.BLUE,
            "chain_complete": Colors.YELLOW
        }.get(entry_type, Colors.WHITE)

    def _cycle_view_mode(self) -> None:
        """Cycle through available view modes."""
        modes = ["available", "active", "completed", "failed", "chains", "log"]
        current_index = modes.index(self.view_mode)
        self.view_mode = modes[(current_index + 1) % len(modes)]
        self.selected_index = 0
        self.scroll_offset = 0
        self.show_chain_details = False
        self.show_quest_history = False
        self.current_history = []

    def _handle_selection(self) -> Optional[dict]:
        """Handle selection of quest, chain, or log entry."""
        if self.view_mode == "available":
            return self._try_start_quest()
        elif self.view_mode == "chains" and not self.show_chain_details:
            self.show_chain_details = True
            return {}
        elif self.view_mode == "log":
            return self._handle_log_selection()
        return None

    def _handle_log_selection(self) -> Optional[dict]:
        """Handle selection in the log view."""
        try:
            if self.show_quest_history:
                return {}  # Just show details of selected entry

            entries = self.quest_manager.get_recent_quest_events()
            if not (0 <= self.selected_index < len(entries)):
                return None

            entry = entries[self.selected_index]
            
            # Get history for the selected quest or chain
            if entry.details and "chain_id" in entry.details:
                self.current_history = self.quest_manager.get_chain_history(entry.details["chain_id"])
            else:
                self.current_history = self.quest_manager.get_quest_history(entry.quest_id)

            self.show_quest_history = True
            self.selected_index = 0
            self.scroll_offset = 0
            return {}

        except Exception as e:
            logger.error(f"Error handling log selection: {e}", exc_info=True)
            return None

    def handle_input(self, event: tcod.event.Event) -> Optional[dict]:
        """Handle input events."""
        try:
            if isinstance(event, tcod.event.KeyDown):
                if event.sym == tcod.event.K_UP:
                    self._move_cursor(-1)
                    return {}
                elif event.sym == tcod.event.K_DOWN:
                    self._move_cursor(1)
                    return {}
                elif event.sym == tcod.event.K_TAB:
                    self._cycle_view_mode()
                    return {}
                elif event.sym == tcod.event.K_RETURN:
                    return self._handle_selection()
                elif event.sym == tcod.event.K_ESCAPE:
                    if self.view_mode == "chains" and self.show_chain_details:
                        self.show_chain_details = False
                        return {}
                    elif self.view_mode == "log" and self.show_quest_history:
                        self.show_quest_history = False
                        self.current_history = []
                        return {}
                    return {"action": "exit"}

            return None

        except Exception as e:
            logger.error(f"Error handling input: {e}", exc_info=True)
            return None

    def _move_cursor(self, dy: int) -> None:
        """Move the selection cursor."""
        try:
            if self.view_mode == "log":
                if self.show_quest_history:
                    items = self.current_history
                else:
                    items = self.quest_manager.get_recent_quest_events()
            elif self.view_mode == "chains":
                available_chains = self.quest_manager.get_available_quest_chains()
                completed_chains = self.quest_manager.get_completed_quest_chains()
                items = available_chains + completed_chains
            elif self.view_mode == "available":
                items = [q for q, _ in self.quest_manager.get_available_quests(self.player_level)]
            elif self.view_mode == "active":
                items = self.quest_manager.get_active_quests()
            elif self.view_mode == "completed":
                items = self.quest_manager.get_completed_quests()
            else:  # failed
                items = self.quest_manager.get_failed_quests()
                
            new_index = self.selected_index + dy
            
            if 0 <= new_index < len(items):
                self.selected_index = new_index
                
                # Adjust scroll if selection would be off screen
                if self.selected_index < self.scroll_offset:
                    self.scroll_offset = self.selected_index
                elif self.selected_index >= self.scroll_offset + self.max_visible_items:
                    self.scroll_offset = self.selected_index - self.max_visible_items + 1

        except Exception as e:
            logger.error(f"Error moving cursor: {e}", exc_info=True)

    def _try_start_quest(self) -> Optional[dict]:
        """Try to start the selected quest.
        
        Returns:
            Action dict if quest was started, None otherwise
        """
        if self.view_mode != "available":
            return None
            
        quests = [q for q, _ in self.quest_manager.get_available_quests(self.player_level)]
        if not quests:
            return None
            
        selected_quest = quests[self.selected_index]
        success, message = self.quest_manager.start_quest(selected_quest.quest_id, self.player_level)
        
        if success:
            self._cycle_view_mode()  # Switch to active quests view
            return {"action": "refresh"}
            
        return None 