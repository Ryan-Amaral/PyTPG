"""
An action.
"""
class Action:

    """
    Creates an action object with a specified action, either a team or atomic.
    Args:
        action:
            (Long or Team) Long if atomic, Team otherwise.
    """
    def __init__(self, action):
        self.action = action

    """
    Returns a boolean telling whether this action is a specific action (atomic),
    or refers to a team (not atomic).
    """
    def isAtomic():
        return type(action) is not Team
