"""
Quest system implementation.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import random
import tcod

from roguelike.core.constants import Colors
from roguelike.core.event import Event, EventType, EventManager
from roguelike.game.quests.types import QuestType, QuestStatus, QuestCondition
from roguelike.game.quests.progress import QuestProgress
from roguelike.game.quests.statistics import QuestStatisticsManager

logger = logging.getLogger(__name__) 