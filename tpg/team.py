
"""
The main building block of TPG. Each team has multiple learning which decide the
action to take in the graph.
"""
class Team:

    """
    Returns an action to use based on the current observation.
    """
    def act(self, obs):
        pass

    """
    Adds learner to the team and updates number of references to that program.
    """
    def addLearner(self, learner=None, prog=None, act=None):
        pass

    """
    Removes learner from the team and updates number of references to that program.
    """
    def removeLearner(self, learner):
        pass

    """
    Bulk removes learners form teams.
    """
    def removeLearners(self):
        pass

    """
    Number of learners with atomic actions on this team.
    """
    def numAtomicActions(self):
        pass
