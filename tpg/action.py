import tpg.team

"""
An action. Each learner of a team will bid to use its own action, either an atomic
action or another team (continue traversing the graph from the next team).
"""
class Action:

    """
    Creates an action object with a specified action, either a team or atomic.
    Args:
        act:
            (Int or Team) Int if atomic, Team otherwise.
    """
    def __init__(self, act):
        self.act = act

    """
    Performs this object's action.
    Args:
        obs:
            (Float[]): Current state of the environment.
        vis:
            (Dict(Team)): Teams already visited so we don't repeat.
        regDict:
            (Dict<Int,Float[]>) Dictionary of registers for learner.
    Returns:
        (Int) The action selected, either atomic right from this action object,
        or from the team of this action.
    """
    def getAction(self, obs, vis=set(), regDict=None):
        if self.isAtomic():
            return self.act # return atomic
        else: # else act is team, return its action
            return self.act.getAction(obs, vis=vis, regDict=regDict)

    """
    Returns a boolean telling whether this action is a specific action (atomic),
    or refers to a team (not atomic).
    """
    def isAtomic(self):
        return isinstance(self.act, int) or isinstance(self.act, list)

    """
    Checks if the action in self is equivalent to other.
    Args:
        other:
            (Action) The action to compare self to.
    Returns:
        (Bool) Whether the Action objects have the same action, either the same
        team, or same atomic value.
    """
    def equals(self, other):
        if self.isAtomic() and other.isAtomic() and self.act is other.act:
            return True
        elif (not self.isAtomic() and not other.isAtomic() and
                self.act.uid == other.act.uid):
            return True

        return False
