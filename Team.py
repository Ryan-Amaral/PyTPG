"""
A Team.
"""
class Team:

    def __init__(self, birthGen = 0):
        self.birthGen = birthGen
        self.learners = []
        self.outcomes = {} # outcomes for tasks from training episodes
        self.learnerRefCount # learners that reference this team

    """
    Adds the learner if not already in, and increments reference smount to the
    learner.
    """
    def addLearner(self, learner):
        if learner not in self.learners:
            learner.teamRefCount += 1
            self.learners.append(learner)

    """
    Deletes the learner from this team's learners if it is in the list.
    """
    def deleteLearner(self, learner):
        if learner in self.learners:
            learner.teamRefCount -= 1
            self.learners.remove(learner)

    """
    Call before deleting a team, to properly dereference learners.
    """
    def erase(self):
        for learner in self.learners:
            learner.teamRefCount -= 1


    """
    Returns the number of atomic actions that this team has.
    """
    def numAtomicActions(self):
        pass
