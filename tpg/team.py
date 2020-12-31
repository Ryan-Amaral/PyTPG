
import uuid
from tpg.utils import flip
from tpg.learner import Learner
import random
import collections
import copy

"""
The main building block of TPG. Each team has multiple learning which decide the
action to take in the graph.
"""
class Team:

    def __init__(self, initParams):
        self.learners = []
        self.outcomes = {} # scores at various tasks
        self.fitness = None
        self.inLearners = [] # ids of learners referencing this team
        self.id = uuid.uuid4()

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
        
        for l in self.learners:
            if l not in o.learners:
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

    '''
    Returns the number of learners referencing this team
    '''
    def numLearnersReferencing(self):
        return len(self.inLearners)

    """
    Returns an action to use based on the current state.
    """
    def act(self, state, visited=set(), actVars=None):
        visited.add(str(self.id)) # track visited teams
        topLearner = max([lrnr for lrnr in self.learners
                if lrnr.isActionAtomic() or str(lrnr.getActionTeam().id) not in visited],
            key=lambda lrnr: lrnr.bid(state, actVars=actVars))
        print("top learner: " + str(topLearner.id))

        return topLearner.getAction(state, visited=visited, actVars=actVars)

    """
    Adds learner to the team and updates number of references to that program.
    """
    def addLearner(self, learner=None):
        program = learner.program

        self.learners.append(learner)
        learner.inTeams.append(str(self.id)) # Add this team's id to the list of teams that reference the learner

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
            target_learner = self.learners[index]
            target_learner.inTeams.remove(str(self.id))
            del self.learners[index]

            # If that learner is pointed to by no other teams, remove it entirely
            if len(target_learner.inTeams) == 0:
                # in addition, if this learner was pointing to a team, make sure to delete the learner's id from that team's inLearners
                if target_learner.actionObj.teamAction != None and target_learner.actionObj.teamAction != -1:
                    target_learner.actionObj.teamAction.inLearners.remove(str(target_learner.id))
                
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
            learner.inTeams.remove(str(self.id))
            # If that learner is pointed to by no other teams, remove it entirely
            if len(learner.inTeams) == 0:
                # in addition, if this learner was pointing to a team, make sure to delete the learner's id from that team's inLearners
                if learner.actionObj.teamAction != None and learner.actionObj.teamAction != -1:
                    learner.actionObj.teamAction.inLearners.remove(str(learner.id))
                
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
        - Probability to delete compounds, that is, if the given probability of deletion is 0.5
          there is a 0.5 * (0.5)^2 probability of 2 learners being erased. 
          0.5 * (0.5)^2 * (0.5)^3 probability of 3 learners being erased, and so on.
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

            # Freak out if we don't have an atomic action
            if self.numAtomicActions() < 1:
                raise Exception("Less than one atomic action in team! This shouldn't happen", self)


            deleted_learners = list()

            # delete some learners
            while flip(probability) and len(self.learners) > 2: # must have >= 2 learners
                probability *= original_probability # decrease next chance


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
                    valid_choices = list(filter(lambda x: not x.isActionAtomic(), self.learners))
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
        - Probability to add compounds, that is, if the given probability of addition is 0.5
          there is a 0.5 * (0.5)^2 probability of 2 learners being added. 
          0.5 * (0.5)^2 * (0.5)^3 probability of 3 learners being added, and so on.
    '''
    def mutation_add(self, probability, selection_pool):
        original_probability = float(probability)

        # Zero chance to add anything, return right away
        if probability == 0.0 or len(selection_pool) == 0:
            return []
        
        if probability >= 1.0:
            # If this were true, we'd end up adding the entire selection pool
            raise Exception("pLrnAdd is greater than or equal to 1.0!")

        added_learners = list()   
        while flip(probability):
            probability *= original_probability # decrease next chance

            learner = random.choice(selection_pool)
            added_learners.append(learner)
            self.addLearner(learner)

            # Ensure we don't pick the same learner twice by filtering the learners we've added from the selection pool
            selection_pool = list(filter(lambda x:x not in added_learners, selection_pool))

        return added_learners

    '''
    Iterates through  this team's learners and mutates them with a given probability.
        - Returns a map of the mutations that occured (key: originalLearner)->(value:mutatedLearner)
        - Ensures that if we only have one atomic action the corresponding learner doesn't mutate to a non-atomic action
        - Mutation: 
            - clones the target learner
            - adds the clone to the team
            - mutates the clone
            - removed the target learner
            - records the target and it's mutated result in mutated_learners 
    '''
    def mutation_mutate(self, probability, mutateParams, teams):
        mutated_learners = {}

        for learner in self.learners:

            if flip(probability):

                # If we only have one learner with an atomic action and the current learner is it
                if self.numAtomicActions() == 1 and learner.isActionAtomic():
                    pActAtom0 = 1.1 # Ensure their action remains atomic
                else:
                    # Otherwise let there be a probability that the learner's action is atomic as defined in the mutate params
                    pActAtom0 = mutateParams['pActAtom']

                #print("Mutating learner {}".format(str(learner.id)))
                
                # Create a new new learner 
                newLearner = Learner(mutateParams, learner.program, learner.actionObj, len(learner.registers))
                #print("Cloned learner {} to create learner {}".format(str(learner.id), str(newLearner.id)))
                # Add the mutated learner to our learners
                # Must add before mutate so that the new learner has this team in its inTeams
                self.addLearner(newLearner)
                #print("cloned learner added to team {}".format(str(self.id)))

                # mutate it
                newLearner.mutate(mutateParams, self, teams, pActAtom0)
                #print("mutated cloned learner")
                #print("mutated learner changed? {}".format(before != newLearner))
                
                #print("removing old learner {} from team".format(str(learner.id)))
                # Remove the existing learner from the team
                self.removeLearner(learner)

                #print("Adding mutated learner {} to mutated learners".format(str(newLearner.id)))
                # Add the mutated learner to our list of mutations
                mutated_learners[str(learner.id)] = str(newLearner.id)


      
        return mutated_learners              

    """
    Mutates the learner set of this team.
    """
    def mutate(self, mutateParams, allLearners, teams):

        
        '''
        With rampant mutations every mutateParams["rampantGen"] generations we do X extra
        iterations of mutation. Where X is a random number between mutateParams["rampantMin"] 
        and mutateParams["rampantMax"].
        '''
        # Throw an error if rampantMin is undefined but 

        # Throw an error if rampantMin > rampant Max
        if mutateParams['rampantGen'] != 0 and mutateParams['rampantMin'] > mutateParams['rampantMax']:
            raise Exception("Min rampant iterations is greater than max rampant iterations!", mutateParams)
        
        if (mutateParams["rampantGen"] > 0 and # The rapantGen cannot be 0, as x mod 0 is undefined
            mutateParams["generation"] % mutateParams["rampantGen"] == 0 and # Determine if this is a rampant generation
            mutateParams["generation"] > mutateParams["rampantGen"]  # Rampant generations cannot occur before generation passes rampantGen
            ): 
            rampantReps = random.randrange(mutateParams["rampantMin"], mutateParams["rampantMax"]) if mutateParams['rampantMin'] < mutateParams['rampantMax'] else mutateParams['rampantMin']
        else:
            rampantReps = 1

        # increase diversity by repeating mutations

        mutation_delta = {}

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
            
            added_learners = self.mutation_add(mutateParams["pLrnAdd"], selection_pool)

            # give chance to mutate all learners
            mutated_learners = self.mutation_mutate(mutateParams["pLrnMut"], mutateParams, teams)

            # Compile mutation_delta for this iteration
            mutation_delta[i] = {} 
            mutation_delta[i]['deleted_learners'] = deleted_learners
            mutation_delta[i]['added_learners'] = added_learners
            mutation_delta[i]['mutated_learners'] = mutated_learners

        # return the number of iterations of mutation
        return rampantReps, mutation_delta

    
