"""
Module for quest visualization.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, TYPE_CHECKING
import math

import tcod
from tcod.console import Console
from roguelike.core.constants import Colors
from roguelike.game.quests.types import QuestStatus

if TYPE_CHECKING:
    from roguelike.game.quests.quests import Quest, QuestChain


class QuestVisualizer:
    """Class for visualizing quest dependencies."""

    def __init__(self, console_width: int, console_height: int):
        self.console_width = console_width
        self.console_height = console_height
        self.node_spacing = 4  # Spacing between nodes
        self.level_height = 3  # Height between levels

    def render_quest_dependencies(
        self,
        console: Console,
        quests: Dict[str, 'Quest'],
        quest_chains: Dict[str, 'QuestChain'],
        x: int,
        y: int,
        width: int,
        height: int
    ) -> None:
        """Render quest dependencies.

        Args:
            console: Target console
            quests: Quest dictionary
            quest_chains: Quest chain dictionary
            x: Starting X coordinate
            y: Starting Y coordinate
            width: Width of render area
            height: Height of render area
        """
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(quests)
        levels = self._assign_levels(dependency_graph)
        node_positions = self._calculate_node_positions(levels, x, y, width, height)

        # Draw edges
        self._draw_edges(console, quests, node_positions)

        # Draw nodes
        self._draw_nodes(console, quests, quest_chains, node_positions)

    def _build_dependency_graph(
        self,
        quests: Dict[str, 'Quest']
    ) -> Dict[str, Set[str]]:
        """Build dependency graph.

        Args:
            quests: Quest dictionary

        Returns:
            Graph representing dependencies
        """
        graph: Dict[str, Set[str]] = {}
        for quest_id, quest in quests.items():
            graph[quest_id] = set()
            for prereq_id in quest.prerequisites:
                if prereq_id in quests:
                    graph[quest_id].add(prereq_id)
        return graph

    def _assign_levels(
        self,
        graph: Dict[str, Set[str]]
    ) -> List[Set[str]]:
        """Assign levels to each node.

        Args:
            graph: Dependency graph

        Returns:
            List of node sets by level
        """
        levels: List[Set[str]] = []
        assigned = set()

        while len(assigned) < len(graph):
            current_level = set()
            for node in graph:
                if node in assigned:
                    continue
                if all(prereq in assigned for prereq in graph[node]):
                    current_level.add(node)
            assigned.update(current_level)
            levels.append(current_level)

        return levels

    def _calculate_node_positions(
        self,
        levels: List[Set[str]],
        base_x: int,
        base_y: int,
        width: int,
        height: int
    ) -> Dict[str, Tuple[int, int]]:
        """Calculate render positions for each node.

        Args:
            levels: Node sets by level
            base_x: Base X coordinate
            base_y: Base Y coordinate
            width: Width of render area
            height: Height of render area

        Returns:
            Mapping of node IDs to render positions
        """
        positions: Dict[str, Tuple[int, int]] = {}
        max_nodes_per_level = max(len(level) for level in levels)
        
        for level_idx, level in enumerate(levels):
            y = base_y + level_idx * self.level_height
            nodes = sorted(level)
            spacing = width / (len(nodes) + 1)
            
            for node_idx, node in enumerate(nodes):
                x = base_x + (node_idx + 1) * spacing
                positions[node] = (int(x), y)

        return positions

    def _draw_edges(
        self,
        console: Console,
        quests: Dict[str, 'Quest'],
        positions: Dict[str, Tuple[int, int]]
    ) -> None:
        """Draw edges representing dependencies.

        Args:
            console: Target console
            quests: Quest dictionary
            positions: Node render positions
        """
        for quest_id, quest in quests.items():
            if quest_id not in positions:
                continue

            x1, y1 = positions[quest_id]
            for prereq_id in quest.prerequisites:
                if prereq_id not in positions:
                    continue

                x2, y2 = positions[prereq_id]
                color = self._get_edge_color(quests[prereq_id], quest)
                
                # Simple line drawing
                if y1 > y2:
                    for y in range(y2, y1 + 1):
                        x = x2 + (x1 - x2) * (y - y2) // (y1 - y2)
                        console.print(x, y, "│", fg=color)

    def _draw_nodes(
        self,
        console: Console,
        quests: Dict[str, 'Quest'],
        quest_chains: Dict[str, 'QuestChain'],
        positions: Dict[str, Tuple[int, int]]
    ) -> None:
        """Draw quest nodes.

        Args:
            console: Target console
            quests: Quest dictionary
            quest_chains: Quest chain dictionary
            positions: Node render positions
        """
        for quest_id, (x, y) in positions.items():
            quest = quests[quest_id]
            color = self._get_node_color(quest)
            chain_symbol = "⚜" if any(
                quest_id in chain.quest_ids
                for chain in quest_chains.values()
            ) else " "
            
            # Draw quest name
            console.print(
                x - len(quest.name) // 2,
                y,
                f"{chain_symbol}{quest.name}",
                fg=color
            )

    def _get_node_color(self, quest: 'Quest') -> Tuple[int, int, int]:
        """Get color based on quest state.

        Args:
            quest: Target quest

        Returns:
            RGB color value
        """
        if quest.status == QuestStatus.COMPLETED:
            return Colors.LIGHT_GREEN
        elif quest.status == QuestStatus.FAILED:
            return Colors.LIGHT_RED
        elif quest.status == QuestStatus.IN_PROGRESS:
            return Colors.LIGHT_BLUE
        else:
            return Colors.WHITE

    def _get_edge_color(
        self,
        prereq_quest: 'Quest',
        dependent_quest: 'Quest'
    ) -> Tuple[int, int, int]:
        """Get color based on dependency state.

        Args:
            prereq_quest: Prerequisite quest
            dependent_quest: Dependent quest

        Returns:
            RGB color value
        """
        if prereq_quest.status == QuestStatus.COMPLETED:
            return Colors.GREEN
        elif prereq_quest.status == QuestStatus.FAILED:
            return Colors.RED
        else:
            return Colors.GRAY 