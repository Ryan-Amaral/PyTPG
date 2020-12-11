from tpg.utils import flip
from tpg.learner import Learner
import random

"""
The main building block of TPG. Each team has multiple learning which decide the
action to take in the graph.
"""
class Team:

    def __init__(self, initParams):
        self.learners = []
        self.outcomes = {} # scores at various tasks
        self.fitness = None
        self.numLearnersReferencing = 0 # number of learners that reference this
        self.inLearners = [] # ids of learners referencing this team
        self.id = initParams["idCountTeam"]
        initParams["idCountTeam"] += 1
        self.genCreate = initParams["generation"]

    """
    Returns an action to use based on the current state.
    """
    def act(self, state, visited=set(), actVars=None):
        visited.add(self) # track visited teams

        topLearner = max([lrnr for lrnr in self.learners
                if lrnr.isActionAtomic() or lrnr.getActionTeam() not in visited],
            key=lambda lrnr: lrnr.bid(state, actVars=actVars))

        return topLearner.getAction(state, visited=visited, actVars=actVars)

    """
    Adds learner to the team and updates number of references to that program.
    """
    def addLearner(self, learner=None):
        program = learner.program
        # don't add duplicate program
        if any([lrnr.program == program for lrnr in self.learners]):
            raise Exception("Attempted to add learner whose program already exists in our learner pool", learner)

        self.learners.append(learner)
        learner.inTeams.append(self.id) # Add this team's id to the list of teams that reference the learner

        return True

    """
    Removes learner from the team and updates number of references to that program.
    """
    def removeLearner(self, learner):

        # only delete if actually in this team
        if learner in self.learners:
            '''
            Have to remove by index so we can update the inTeams accordingly.
            Attempting to do self.learners.remove(learner) will fail with a ValueError 
            because once we modify the inTeams it's no longer the same learner. 
            '''
            index = self.learners.index(learner)
            self.learners[index].inTeams.remove(self.id)
            del self.learners[index]
            return

        '''
        TODO log the attempt to remove a learner that doesn't appear in this team
        '''
        print("learner not in team")
        return

    """
    Bulk removes learners from the team.
    """
    def removeLearners(self):
        for learner in self.learners:
            learner.inTeams.remove(self.id)
        del self.learners[:]

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
    def mutate(self, mutateParams, allLearners, teams):

        # repeats of mutation
        if (mutateParams["generation"] % mutateParams["rampantGen"] == 0 and
                mutateParams["generation"] > mutateParams["rampantGen"] and mutateParams["rampantGen"] > 0):
            rampantReps = random.randrange(mutateParams["rampantMin"], mutateParams["rampantMax"])
        else:
            rampantReps = 1

        # increase diversity by repeating mutations
        for i in range(rampantReps):

            # delete some learners
            p = mutateParams["pLrnDel"]
            while flip(p) and len(self.learners) > 2: # must have >= 2 learners
                p *= mutateParams["pLrnDel"] # decrease next chance

                # choose non-atomic learners if only one atomic remaining
                learner = random.choice([l for l in self.learners
                                         if not l.isActionAtomic()
                                            or self.numAtomicActions() > 1])

                # if created this gen, derefence team it references
                if (i > 0 and learner.genCreate == mutateParams["generation"]
                        and not learner.isActionAtomic()):
                    learner.getActionTeam().numLearnersReferencing -= 1

                self.removeLearner(learner)

            # add some learners
            p = mutateParams["pLrnAdd"]
            while flip(p):
                p *= mutateParams["pLrnAdd"] # decrease next chance

                learner = random.choice([l for l in allLearners
                                         if l not in self.learners and
                                            l.getActionTeam() is not self])
                self.addLearner(learner)

            # give chance to mutate all learners
            oLearners = list(self.learners)
            for learner in oLearners:
                if flip(mutateParams["pLrnMut"]):
                    if self.numAtomicActions() == 1 and learner.isActionAtomic():
                        pActAtom0 = 1.1 # action must be kept atomic if only one
                    else:
                        pActAtom0 = mutateParams["pActAtom"]

                    # must remove then re-add fresh mutated learner
                    # if created this gen, derefence team it references
                    if (i > 0 and learner.genCreate == mutateParams["generation"]
                            and not learner.isActionAtomic()):
                        learner.getActionTeam().numLearnersReferencing -= 1
                    self.removeLearner(learner)
                    newLearner = Learner(mutateParams, learner=learner)
                    newLearner.mutate(mutateParams, self, teams, pActAtom0)
                    self.addLearner(newLearner)
