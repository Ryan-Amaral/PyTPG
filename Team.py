"""
A Team.
"""
class Team:

    def __init__(self, birthGen = 0):
        self.birthGen = birthGen
        self.learners = []
        self.outcomes = {} # outcomes from training episodes
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
    Call before deleting a team, to properly dereference learners.
    """
    def erase(self):
        for learner in self.learners:
            learner.teamRefCount -= 1
