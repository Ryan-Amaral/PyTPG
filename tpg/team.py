from tpg.utils import flip
from tpg.learner import Learner
import random
import collections

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

    '''
    A team is equal to another object if that object:
        - is an instance of the team class
        - was created on the same generation
        - has the same list of learners it references
        - has the same list of learners referecing it
    '''
    def __eq__(self, o: object) -> bool:

        # Object must be instance of Team
        if not isinstance(o, Team):
            return False

        # Object must be created the same generation as us
        if self.genCreate != o.genCreate:
            return False
        
        '''
        The other object's learners must match our own, therefore:
            - len(self.learners) must be equal to len(o.learners)
            - every learner that appears in our list of learners must appear in the 
              other object's list of learners as well.
        '''
        if len(self.learners) != len(o.learners):
            return False
        
        '''
        Collection comparison via collection counters
        https://www.journaldev.com/37089/how-to-compare-two-lists-in-python
        '''
        if collections.Counter(self.learners) != collections.Counter(o.learners):
            return False
        
        '''
        The other object's inLearners must match our own, therefore:
            - len(self.inLearners) must be equal to len(o.inLearners)
            - every learner that appears in our list of inLearners must appear in 
              the other object's list of inLearners as well. 
        '''
        if len(self.inLearners) != len(o.inLearners):
            return False
        
        '''
        Collection comparison via collection counters
        https://www.journaldev.com/37089/how-to-compare-two-lists-in-python
        '''
        if collections.Counter(self.inLearners) != collections.Counter(o.inLearners):
            return False

        return True

    '''
    Negation of __eq__
    '''
    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

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

    '''
    Executes a delete mutation with a certain probability. 
        - Returns immediately if the probability of deletion is 0.0
        - Raises an exception if the probability of deleition is 1.0 or greater as that would
          simply remove most learners from the team.
        - Probability to delete compounds, that is, if the given probability of delition is 0.5
          there is a 0.5 * 0.5 probability of 2 learners being erased. 
          0.25 * 0.5 probability of 3 learners being erased, and so on.
        - Will not delete any learners if there are 2 or fewer learners on the team
        - Verifies that there is always at least one learner pointing to an atomic action on a team
          raises an exception otherwise.
        - If there is only one learner pointing to an atomic action filter it out and pick from the 
          remaining learners.
        - Returns a list of learners removed from the team
    '''
    def mutation_delete(self, probability):

            original_probability = float(probability)

            if probability == 0.0:
                return []

            if probability >= 1.0:
                # If this were true we'd end up deleting every learner
                raise Exception("pLrnDel is greater than or equal to 1.0!")

            deleted_learners = []

            # delete some learners
            while flip(probability) and len(self.learners) > 2: # must have >= 2 learners
                probability *= original_probability # decrease next chance

                # Freak out if we don't have an atomic action
                if self.numAtomicActions() < 1:
                    raise Exception("Less than one atomic action in team! This shouldn't happen", self)

                # If we have more than one learner with an atomic action pick any learner to delete
                if self.numAtomicActions() > 1:
                    learner = random.choice(self.learners)
                else: 
                    # Otherwise if we only have one, filter it out and pick from the remaining learners
                    '''
                    Use filter() to filter a list. 
                    Call filter(function, iterable) with iterable as a list to get an iterator containing only elements from iterable for which function returns True. 
                    Call list(iterable) with iterable as the previous result to convert iterable to a list.
                    '''
                    valid_choices = list(filter(lambda x: x.isActionAtomic(), self.learners))
                    learner = random.choice(valid_choices)

                deleted_learners.append(learner)
                self.removeLearner(learner)

            return deleted_learners

    ''' 
    A learner is added from the provided selection pool with a given 
    probability. 
        - Returns the learners that have been added.
        - Returns immediately if the probability of addition is 0.0
        - Raises an exception if the probability of addition is 1.0 or greater
        - Returns immediately if the selection pool is empty
    '''
    def mutation_add(self, probability, selection_pool):
        original_probability = float(probability)

        # Zero chance to add anything, return right away
        if probability == 0.0 or len(selection_pool) == 0:
            return []
        
        if probability >= 1.0:
            # If this were true, we'd end up adding the entire selection pool
            raise Exception("pLrnAdd is greater than or equal to 1.0!")

        added_learners = []   
        while flip(probability):
            probability *= original_probability # decrease next chance

            learner = random.choice(selection_pool)
            added_learners.append(learner)
            self.addLearner(learner)

            # Ensure we don't pick the same learner twice
            selection_pool = list(filter(lambda x:x not in added_learners, selection_pool))

        return added_learners

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
            '''
            TODO log mutation deltas...
            '''
            deleted_learners = self.mutation_delete(mutateParams["pLrnDel"])

            # Create a selection pool from which to add learners to this team
            
            # Filter out learners that already belong to this team
            selection_pool = list(filter(lambda x: x not in self.learners, allLearners))
            
            # Filter out learners that point to this team
            selection_pool = list(filter(lambda x: x not in self.inLearners, selection_pool))

            # Filter out learners we just deleted
            selection_pool = list(filter(lambda x: x not in deleted_learners, selection_pool))
            
            self.mutation_add(mutateParams["pLrnAdd"], selection_pool)

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
