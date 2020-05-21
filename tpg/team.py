from tpg.utils import flip
from tpg.learner import Learner
import random

"""
The main building block of TPG. Each team has multiple learning which decide the
action to take in the graph.
"""
class Team:

    idCount = 0

    def __init__(self, traversal):
        self.learners = []
        self.outcomes = {} # scores at various tasks
        self.fitness = None
        self.traversal = traversal
        self.numLearnersReferencing = 0 # number of learners that reference this
        self.id = Team.idCount
        Team.idCount += 1

    def __contains__(self, learner):
        for other in self.learners:
            if learner.id == other.id:
                return True
        return False
    
    def __hash__(self):
        return self.id

    
    """
    Returns an action to use based on the current state.
    """
    def act1(self, state, memMatrix, frameNumber, visited=set()):
        # We've now visited this team, so add it to the visited set.
        visited.add(self)
        
        # 1. Make a list of all Learners who:
        #    a. Have an atomic action (label).
        #    b. Have a team reference, but that team hasn't been visited.
        # 2. Run the bid method of every one of those learners.
        # 3. Find the learner with the largest bid and store it in topLearner.
        topLearner = max([lrnr for lrnr in self.learners if lrnr.isActionAtomic() or lrnr.action not in visited], key=lambda lrnr: lrnr.bid(state, memMatrix, frameNumber))
        
        # Return the action of the top learner. If this action is a team
        # reference, then getAction(..) calls that team's act(..) method
        # recursively. This process continues until we get an atomic action.
        


        return topLearner.getAction2(state, memMatrix, frameNumber, visited)

    
    """
    Returns an action to use based on the current state and traversal type.
    """
    def act(self, state, memMatrix, frameNumber, visited=set()):
        visited.add(self) # track visited teams

        if self.traversal == 'team':
            # Make the first Learner the top learner and save its bid.
            topLearner = self.learners[0]
            topBid = topLearner.bid(state=state, memMatrix=memMatrix, frameNumber=frameNumber)

            # Iterate through every Learner on this Team.
            for learner in self.learners:
                # If we have visited this Learner already, skip it.
                if learner == topLearner: 
                    continue

                # Make sure that if the Learner is not atomic, it is
                # referencing a Team we have not yet visited.
                if learner.isActionAtomic() or learner.action not in visited:
                    # Store the bid from the Learner.
                    bid = learner.bid(state=state, memMatrix=memMatrix, frameNumber=frameNumber)
                    # If the bid is higher than our best learner, update the 
                    # top learner variables and proceed to the next Learner.
                    if bid > topBid:
                        topLearner = learner
                        topBid = bid
            
            # Return the action of the top Learner. If it is a reference to a
            # Team, this process recurisvely continues from that Team's act().'
            return topLearner.getAction2(state, memMatrix, frameNumber, visited)
        
        if self.traversal == 'learner':
            topLearner = max([lrnr for lrnr in self.learners
                   if lrnr.isActionAtomic() or lrnr not in visited],
                key=lambda lrnr: lrnr.bid(state=state,memMatrix=memMatrix,frameNumber=frameNumber))
        
            return topLearner.getAction2(state, memMatrix, visited=visited)

    """
    Same as act, but with additional features. Use act for performance.
    TODO: IMPLEMENT OTHER GET ACTION IN LEARNER TO MAKE THIS USEFUL.
    """
    def act2(self, state, memMatrix, visited=set(), numStates=50):
        visited.add(self) # track visited teams

        # first get candidate (unvisited) learners
        learners = [lrnr for lrnr in self.learners
                if lrnr.action not in visited]
        # break down getting bids to do more stuff to learners
        topLearner = learners[0]
        topBid = learners[0].bid(state)
        learners[0].saveState(state, numStates=numStates)
        for lrnr in learners[1:]:
            bid = lrnr.bid(state, memMatrix)
            lrnr.saveState(state, numStates=numStates)
            if bid > topBid:
                topLearner = lrnr
                topBid = bid

        return topLearner.getAction(state, memMatrix, visited=visited)

    """
    Returns the size of this team in the graph
    """
    def size(self, visited):
        if self in visited:
            return 
        visited.add(self)
        for l in self.learners:
            if not l.isActionAtomic():
                l.action.size(visited)

    """
    Returns the number of learners and instructions in the graph 
    """
    def compileLearnerStats(self, learners, stats):
        for l in self.learners:
            if l not in learners:
                learners.add(l)
                for instruction in l.program.instructions:
                    stats['instructionCount'] += 1
                    if instruction[1] == 0:
                        stats['add'] += 1
                    elif instruction[1] == 1:
                        stats['subtract'] += 1
                    elif instruction[1] == 2:
                        stats['multiply'] += 1
                    elif instruction[1] == 3:
                        stats['divide'] += 1
                    elif instruction[1] == 4:
                        stats['neg'] += 1
                    elif instruction[1] == 5:
                        stats['memRead'] += 1
                    elif instruction[1] == 6:
                        stats['memWrite'] += 1
                if not l.isActionAtomic():
                    l.action.compileLearnerStats( learners, stats)

                



 
    """
    Adds learner to the team and updates number of references to that program.
    """
    def addLearner(self, learner):
        program = learner.program
        
        # Don't add duplicate program.
        if learner in self.learners:
            return False
        
        # Add the incoming learner to the list of learners..
        self.learners.append(learner)

        # Increase the number of teams containing this learner.
        learner.numTeamsReferencing += 1

        # Fall-through true return.
        return True

    """
    Removes learner from the team and updates number of references to that program.
    """
    def removeLearner(self, learner):
        if learner in self.learners:
            learner.numTeamsReferencing -= 1
            self.learners.remove(learner)

    """
    Bulk removes learners from teams.
    """
    def removeLearners(self):
        # Make a copy of the current learner list
        # so we don't delete them while running the for
        # loop.
        for lrnr in list(self.learners):
            # For each learner in our new list, we call
            # removeLearner(L) on each learner in the old list.
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
                multiActs, pSwapMultiAct, pChangeMultiAct,
                uniqueProgThresh, inputs=None, outputs=None):

       # delete some learners
        p = pDelLrn
        while flip(p) and len(self.learners) > 2: # must have >= 2 learners
            p *= pDelLrn # decrease next chance

            # choose non-atomic learners if only one atomic remaining
            learner = random.choice([l for l in self.learners 
                                     if not l.isActionAtomic() or 
                                     self.numAtomicActions() > 1])
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
                if self.numAtomicActions() == 1 and learner.isActionAtomic():
                    pActAtom0 = 1 # action must be kept atomic if only one
                else:
                    pActAtom0 = pActAtom

                # must remove then re-add fresh mutated learner
                self.removeLearner(learner)
                newLearner = Learner(learner=learner)
                newLearner.mutate(
                        pMutProg, pMutAct, pActAtom0, atomics, self, allTeams,
                        pDelInst, pAddInst, pSwpInst, pMutInst,
                        multiActs, pSwapMultiAct, pChangeMultiAct,
                        uniqueProgThresh, inputs=inputs, outputs=outputs)
                self.addLearner(newLearner)


def main():
    # Run some code in here.
    print("In Team.main()")
    from tpg.program import Program
    from tpg.learner import Learner
    import inspect
    team = Team("team")

    print(inspect.signature(Learner.getAction2))

    for i in range(12):
        learner = Learner(program=Program(maxProgramLength=1), action=1, numRegisters=8)
        
        team.addLearner(learner)

    from time import time
    import numpy as np
    
    features = [random.randint(0,10000) for i in range(100)]
    memory = np.array([[random.randint(0,10000) for _ in range(800)] for _ in range(8)])

    print("Features and Memory Created")

    team.act1(features, memory, -1, set())
    team.act(features, memory, -1, set())

   

    start = time()
    for i in range(1000):

        team.act1(features, memory, i)
    stop = time() - start
    print("Ryan Act:", stop)

    start = time()
    for i in range(1000, 2000):
        team.act(features, memory, i)
    stop = time() - start
    print("Robert Act:", stop)




if __name__ == "__main__":
    main()
    
