from tpg.utils import flip
from tpg.learner import Learner
import random

"""
The main building block of TPG. Each team has multiple learning which decide the
action to take in the graph.
"""
class Team:

    idCount = 0

    def __init__(self):
        self.learners = []
        self.outcomes = {} # scores at various tasks
        self.fitness = None
        self.numLearnersReferencing = 0 # number of learners that reference this
        self.id = Team.idCount
        Team.idCount += 1

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
        for lrnr in list(self.learners):
            self.removeLearner(lrnr)

    """
    Number of learners with atomic actions on this team.
    """
    def numAtomicActions(self):
        num = 0
        for lrnr in self.learners:
            if lrnr.isActionAtomic():
                num += 1

        return num

    """
    Mutates the learner set of this team.
    """
    def mutate(self, pDelLrn, pAddLrn, pMutLrn, allLearners,
                pMutProg, pMutAct, pActAtom, atomics, allTeams,
                pDelInst, pAddInst, pSwpInst, pMutInst,
                inputs=None, outputs=None, update=True):

        # delete some learners
        p = pDelLrn
        while flip(p) and len(self.learners) > 2: # must have >= 2 learners
            p *= pDelLrn # decrease next chance

            # choose non-atomic learners if only one atomic remaining
            learner = random.choice([l for l in self.learners
                                     if not l.isActionAtomic() or
                                        not self.numAtomicActions() < 2])
            self.removeLearner(learner)

        # add some learners
        p = pAddLrn
        while flip(p):
            p *= pAddLrn # decrease next chance

            learner = random.choice([l for l in allLearners
                                     if l not in self.learners and
                                        l.action is not self])
            self.addLearner(learner)

        # give chance to mutate all learners
        oLearners = list(self.learners)
        for learner in oLearners:
            if flip(pMutLrn):
                # must remove then re-add fresh mutated learner
                self.removeLearner(learner)
                newLearner = Learner(learner=learner)
                newLearner.mutate(
                        pMutProg, pMutAct, pActAtom, atomics, self, allTeams,
                        pDelInst, pAddInst, pSwpInst, pMutInst,
                        inputs=inputs, outputs=outputs, update=update)
                self.addLearner(newLearner)
