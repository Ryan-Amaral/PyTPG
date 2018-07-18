"""
An action.
"""
class Action:

    """
    Creates an action object with a specified action, either a team or atomic.
    Args:
        act:
            (Long or Team) Long if atomic, Team otherwise.
    """
    def __init__(self, act):
        self.act = act

    """
    Returns a boolean telling whether this action is a specific action (atomic),
    or refers to a team (not atomic).
    """
    def isAtomic(self):
        return type(self.act) is not Team

    """
    Checks if the action in self is equivalent to other.
    Args:
        other:
            (Action) The action to compare self to.
    Returns:
        Whether the Action objects have the same action, either the same team,
        or same atomic value.
    """
    def equals(self, other):
        if self.isAtomic() and other.isAtomic() and self.act == other.act:
            return True
        elif (!self.isAtomic() and !other.isAtomic() and
                self.act.uid == other.act.uid):
            return True

        return False
