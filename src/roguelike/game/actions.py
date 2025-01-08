"""
Game actions that can be performed by entities.
"""

class Action:
    """Base class for all actions."""
    pass

class MovementAction(Action):
    """Action for moving in a direction."""
    def __init__(self, dx: int, dy: int):
        self.dx = dx
        self.dy = dy

class WaitAction(Action):
    """Action for doing nothing and waiting a turn."""
    pass

class QuitAction(Action):
    """Action for quitting the game."""
    pass 