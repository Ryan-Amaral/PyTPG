
"""
A team has multiple learners, each learner has a program which is executed to
produce the bid value for this learner's action.
"""
class Learner:

    def __init__(self):
        pass

    """
    Get the bid value, highest gets its action selected.
    """
    def bid(self, obs):
        pass

    """
    Returns the action of this learner, either atomic, or requests the action
    from the action team.
    """
    def getAction(self):
        pass

    """
    Returns true if the action is atomic, otherwise the action is a team.
    """
    def isActionAtomic(self):
        pass

    """
    Returns true if the action of this learner is equivalent to act.
    """
    def compareAction(self, act):
        pass

    """
    Changes the action into the newAct.
    """
    def changeAction(self, newAct):
        pass
