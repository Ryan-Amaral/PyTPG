
"""
The main building block of TPG. Each team has multiple learning which decide the
action to take in the graph.
"""
class Team:

    idCount = 0

    def __init__(self):
        self.learners = []
        self.outcomes = {} # scores at various tasks
        self.numLearnersReferencing = 0 # number of learners that reference this

    """
    Returns an action to use based on the current state.
    """
    def act(self, state, visited=set()):
        visited.add(self) # track visited teams
        topLearner = max(self.learners, key=lambda lrnr: lrnr.bid(state))
        return topLearner.getAction(state, visited=visited)

    """
    Adds learner to the team and updates number of references to that program.
    """
    def addLearner(self, learner=None, program=None, action=None):
        if learner is not None:
            program = learner.program
        elif program is not None and action is not None:
            learner = Learner(program=program, action=action)

        if any([lrnr.program == program for lrnr in self.learners]):
            return False # don't add duplicate program

        self.learners.append(learner)
        program.numTeamsReferencing += 1

        return True

    """
    Removes learner from the team and updates number of references to that program.
    """
    def removeLearner(self, learner):
        if learner in self.learners:
            learner.program.numTeamsReferencing -= 1
            self.learners.remove(learner)

    """
    Bulk removes learners from teams.
    """
    def removeLearners(self):
        for lrnr in self.learners:
            lrnr.program.numTeamsReferencing -= 1
        self.learners = []

    """
    Number of learners with atomic actions on this team.
    """
    def numAtomicActions(self):
        num = 0
        for lrnr in self.learners:
            if lrnr.isActionAtomic():
                num += 1

        return num
