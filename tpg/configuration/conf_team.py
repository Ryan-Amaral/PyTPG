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
    def removeLearner_def(self, learner, gen=-1):
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

        # Remove this team id from the learner's inTeams
        # NOTE: Have to do this after removing the learner otherwise, removal will fail 
        # since the learner's inTeams will not match 
        to_remove.inTeams.remove(str(self.id))

        # remove learner from inLearners of it's actions team if applicable
        if gen == to_remove.genCreate and not to_remove.isActionAtomic():
            to_remove.getActionTeam().inLearners.remove(str(learner.id))

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

        mutation_delta = {}
        # delete some learners
        '''
        TODO log mutation deltas...
        '''
        deleted_learners = self.mutation_delete(mutateParams["pLrnDel"], mutateParams["generation"])

        # Create a selection pool from which to add learners to this team
        
        # Filter out learners that already belong to this team
        selection_pool = list(filter(lambda x: x not in self.learners, allLearners))
        
        # Filter out learners that point to this team
        selection_pool = list(filter(lambda x: str(x.id) not in self.inLearners, selection_pool))

        # Filter out learners we just deleted
        selection_pool = list(filter(lambda x: x not in deleted_learners, selection_pool))
        
        added_learners = self.mutation_add(mutateParams["pLrnAdd"], selection_pool)

        # give chance to mutate all learners
        mutated_learners = self.mutation_mutate(mutateParams["pLrnMut"], mutateParams, teams, mutateParams["generation"])

        # Compile mutation_delta for this iteration
        mutation_delta = {} 
        mutation_delta['deleted_learners'] = deleted_learners
        mutation_delta['added_learners'] = added_learners
        mutation_delta['mutated_learners'] = mutated_learners

        # return the number of iterations of mutation
        return mutation_delta
