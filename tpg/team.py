from tpg.learner import Learner
import tpg.action
import tpg.extensions

"""
A Team. A node in the graph that makes the Tangled Program Graph.
"""
class Team:

    def __init__(self, birthGen = 0):
        self.birthGen = birthGen
        self.learners = []
        self.outcomes = {} # outcomes for tasks from training episodes
        self.learnerRefCount = 0 # learners that reference this team

        # only filled in root teams
        self.envsActions = {} # actions made per env
        self.teamsEnvsVis = {} # envs that each team visits

    """
    Search for an action to perform based on the observation.
    Args:
        obs:
            (Float[]): Current state of the environment.
        vis:
            (Dict(Team)): Teams already visited so we don't repeat.
        regDict:
            (Dict<Int,Float[]>) Dictionary of registers for learner.
    Returns:
        (Int or Float[]) The action.
    """
    def getAction(self, obs, vis=set(), regDict=None):
        vis.add(self) # remember that we visited this team

        # choose learner with highest bid
        maxBid = 0
        maxLearner = None
        for learner in self.learners:
            if not learner.action.isAtomic() and learner.action.act in vis:
                continue # don't take already visited team's bid

            bid = learner.bid(obs, regDict)
            if maxLearner is None: # first bid
                maxBid = bid
                maxLearner = learner

            if bid > maxBid: # bid is better
                maxBid = bid
                maxLearner = learner

        if maxLearner is None:
            return 0 # default move if no choice made
        else:
            return maxLearner.action.getAction(obs, vis=vis, regDict=regDict)

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
    def removeLearner(self, learner):
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
        num = 0
        for lrnr in self.learners:
            if lrnr.action.isAtomic():
                num += 1
        return num

    """
    Returns all nodes and edges from this root team. Should only call if this
    is a root team.
    """
    def getRootTeamGraph(self):
        return tpg.extensions.getRootTeamGraph(self)
