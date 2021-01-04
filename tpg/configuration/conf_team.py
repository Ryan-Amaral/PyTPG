from tpg import learner
from tpg.utils import flip
from tpg.learner import Learner
import random
import uuid

"""
The main building block of TPG. Each team has multiple learning which decide the
action to take in the graph.
"""
class ConfTeam:

    def init_def(self, initParams):
        self.learners = []
        self.outcomes = {} # scores at various tasks
        self.fitness = None
        self.inLearners = [] # ids of learners referencing this team
        self.id = uuid.uuid4()

        self.genCreate = initParams["generation"]

    """
    Returns an action to use based on the current state. Team traversal.
    NOTE: Do not set visited = list() because that will only be
    evaluated once, and thus won't create a new list every time.
    """
    def act_def(self, state, visited, actVars=None):
        # If we've already visited me, throw an exception
        if str(self.id) in visited:
            print("Visited:")
            for i,cursor in enumerate(visited):
                print("{}|{}".format(i, cursor))
            raise(Exception("Already visited {}!".format(str(self.id))))

        visited.append(str(self.id)) # track visited teams


        top_learner = max([lrnr for lrnr in self.learners
                if lrnr.isActionAtomic() or str(lrnr.getActionTeam().id) not in visited],
            key=lambda lrnr: lrnr.bid(state, actVars=actVars))


        # Print the path taken to this atomic action
        # if top_learner.isActionAtomic():
        #     path = ""
        #     for i,cursor in enumerate(visited):
        #         if i == 0:
        #             path += "("
        #         else:
        #             path += "->("
                
        #         path += cursor + ")"

        #     path += "-> " + str(top_learner.actionObj.actionCode)

        #     print("[{}][{}] {}".format(actVars['frameNum'], len(visited), path))

        return top_learner.getAction(state, visited=visited, actVars=actVars)



    """
    Returns an action to use based on the current state. Learner traversal.
    """
    def act_learnerTrav(self, state, visited=list(), actVars=None):

        topLearner = max([lrnr for lrnr in self.learners
                if lrnr.isActionAtomic() or str(lrnr.id) not in visited],
            key=lambda lrnr: lrnr.bid(state, actVars=actVars))

        visited.add(str(topLearner.id))
        return topLearner.getAction(state, visited=visited, actVars=actVars)

    """
    Adds learner to the team and updates number of references to that program.
    """
    def addLearner_def(self, learner=None):
        program = learner.program

        self.learners.append(learner)
        learner.inTeams.append(str(self.id)) # Add this team's id to the list of teams that reference the learner

        return True

    """
    Removes learner from the team and updates number of references to that program.
    """
    def removeLearner_def(self, learner):
        # only delete if actually in this team
        '''
        TODO log the attempt to remove a learner that doesn't appear in this team
        '''
        if learner not in self.learners:
            raise Exception("Attempted to remove a learner ({}) not referenced by team {}".format(
            str(learner.id), str(self.id)
        ))

        # Find the learner to remove
        to_remove = [cursor for  cursor in self.learners if cursor == learner]
        if len(to_remove) != 1:
            raise Exception("Duplicate learner detected during team.removeLearner. {} duplicates".format(len(to_remove)))
        to_remove = to_remove[0]

        # Build a new list of learners containing only learners that are not the learner
        self.learners = [cursor for cursor in self.learners if cursor != learner ]

        # Remove our id from the learner's inTeams
        # NOTE: Have to do this after removing the learner otherwise, removal will fail 
        # since the learner's inTeams will not match 
        to_remove.inTeams.remove(str(self.id))

    """
    Bulk removes learners from teams.
    """
    def removeLearners_def(self):
        for learner in self.learners:
            learner.inTeams.remove(str(self.id))

        del self.learners[:]

    """
    Number of learners with atomic actions on this team.
    """
    def numAtomicActions_def(self):
        num = 0
        for lrnr in self.learners:
            if lrnr.isActionAtomic():
                num += 1

        return num

    """
    Mutates the learner set of this team.
    """
    def mutate_def(self, mutateParams, allLearners, teams):

        
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
