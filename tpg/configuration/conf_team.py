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
    def act_def(self, state, visited, actVars=None, path_trace=None):

        # If we've already visited me, throw an exception
        if str(self.id) in visited:
            print("Visited:")
            for i,cursor in enumerate(visited):
                print("{}|{}".format(i, cursor))
            raise(Exception("Already visited team {}!".format(str(self.id))))

        # Add this team's id to the list of visited ids
        visited.append(str(self.id)) 
        
        '''
        Valid learners are ones which:
            * Are action atomic
            * Whose team we have not yet visited
        '''
        valid_learners = [lrnr for lrnr in self.learners
                if lrnr.isActionAtomic() or str(lrnr.getActionTeam().id) not in visited]


        top_learner = max(valid_learners,
            key=lambda lrnr: lrnr.bid(state, actVars=actVars))

    
        # If we're tracing this path
        if path_trace != None:
            
            last_segment = path_trace[-1] if len(path_trace) != 0 else None

            # Create our path segment
            path_segment =  {
                'team_id': str(self.id),
                'top_learner': str(top_learner.id),
                'top_bid': top_learner.bid(state, actVars=actVars),
                'top_action': top_learner.actionObj.actionCode if top_learner.isActionAtomic() else str(top_learner.actionObj.teamAction.id),
                'depth': last_segment['depth'] + 1 if last_segment != None else 0,# Record path depth
                'bids': []
            }

            # Populate bid values
            for cursor in valid_learners:
                path_segment['bids'].append({
                    'learner_id': str(cursor.id),
                    'bid': cursor.bid(state, actVars=actVars),
                    'action': cursor.actionObj.actionCode if cursor.isActionAtomic() else str(cursor.actionObj.teamAction.id)
                })

            # Append our path segment to the trace
            path_trace.append(path_segment)

        return top_learner.getAction(state, visited=visited, actVars=actVars, path_trace=path_trace) 


    """
    Returns an action to use based on the current state. Learner traversal.
    """
    def act_learnerTrav(self, state, visited, actVars=None, path_trace=None):

        valid_learners = [lrnr for lrnr in self.learners
                if lrnr.isActionAtomic() or str(lrnr.id) not in visited]

        top_learner = max(valid_learners,
            key=lambda lrnr: lrnr.bid(state, actVars=actVars))

        # If we're tracing this path
        if path_trace != None:
            last_segment = path_trace[-1] if len(path_trace) != 0 else None

            # Create our path segment
            path_segment =  {
                'team_id': str(self.id),
                'top_learner': str(top_learner.id),
                'top_bid': top_learner.bid(state, actVars=actVars),
                'top_action': top_learner.actionObj.actionCode if top_learner.isActionAtomic() else str(top_learner.actionObj.teamAction.id),
                'depth': last_segment['depth'] + 1 if last_segment != None else 0,# Record path depth
                'bids': []
            }

            # Populate bid values
            for cursor in valid_learners:
                path_segment['bids'].append({
                    'learner_id': str(cursor.id),
                    'bid': cursor.bid(state, actVars=actVars),
                    'action': cursor.actionObj.actionCode if cursor.isActionAtomic() else str(cursor.actionObj.teamAction.id)
                })

            # Append our path segment to the trace
            path_trace.append(path_segment)

        visited.append(str(top_learner.id))
        return top_learner.getAction(state, visited=visited, actVars=actVars, path_trace=path_trace)

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
        new_learners = []

        for i in range(rampantReps):
            #print("i/rampant reps:  {}/{} ".format(i, rampantReps))
            # delete some learners
            '''
            TODO log mutation deltas...
            '''
            deleted_learners = self.mutation_delete(mutateParams["pLrnDel"])

            # Create a selection pool from which to add learners to this team
            
            # Filter out learners that already belong to this team
            selection_pool = list(filter(lambda x: x not in self.learners, allLearners))
            
            # Filter out learners that point to this team
            selection_pool = list(filter(lambda x: str(x.id) not in self.inLearners, selection_pool))

            # Filter out learners we just deleted
            selection_pool = list(filter(lambda x: x not in deleted_learners, selection_pool))
            
            added_learners = self.mutation_add(mutateParams["pLrnAdd"], selection_pool)

            # give chance to mutate all learners
            mutated_learners, mutation_added_learners = self.mutation_mutate(mutateParams["pLrnMut"], mutateParams, teams)
            new_learners += mutation_added_learners

            # Compile mutation_delta for this iteration
            mutation_delta[i] = {} 
            mutation_delta[i]['deleted_learners'] = deleted_learners
            mutation_delta[i]['added_learners'] = added_learners
            mutation_delta[i]['mutated_learners'] = mutated_learners

        for cursor in new_learners:
            if cursor in self.learners:
                new_learners.remove(cursor)

        for cursor in new_learners:
                if len(cursor.inTeams) == 0 and not cursor.isActionAtomic():
                    cursor.actionObj.teamAction.inLearners.remove(str(cursor.id))

        # return the number of iterations of mutation
        return rampantReps, mutation_delta