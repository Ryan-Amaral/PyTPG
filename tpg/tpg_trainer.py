from __future__ import division
import random
import time
from operator import itemgetter

from tpg.action import Action
from tpg.learner import Learner
from tpg.team import Team
from tpg.tpg_agent import TpgAgent

"""
The main class to do training on a population of Teams.
Created By: Ryan Amaral.
Created On: June 29, 2018 13:44.
Created Because: I was tired of Java.
"""
class TpgTrainer:

    uidCounter = 0

    """
    Initializes the Training procedure, potentially picking up from a
    previously left off point.
    Args:
        actions        : (Int[]) The actions available in the env.
        randSeed       :
        teamPopSizeInit: (Int) Initial Team population size.
        gap            : Proportion of agents to replace per gen.
        pLearnerDelete :
        pLearnerAdd    :
        pMutateAction  :
        pActionIsTeam  :
        maxTeamSize    :
        maxProgramSize :
        pProgramDelete :
        pProgramAdd    :
        pProgramSwap   :
        pProgramMutate :
        popInit        : Object containing all info needed to carry on from a
            previous training session. Serialize and deserialize with pickle.
    """
    def __init__(self, actions, randSeed=0, teamPopSizeInit=360, gap=0.5,
            pLearnerDelete=0.7, pLearnerAdd=0.7, pMutateAction=0.2,
            pActionIsTeam=0.5, maxTeamSize=5, maxProgramSize=96,
            pProgramDelete=0.5, pProgramAdd=0.5, pProgramSwap=1.0,
            pProgramMutate=1.0, popInit=None):

        # set the variables
        self.actions = actions
        self.randSeed = randSeed
        self.teamPopSizeInit = teamPopSizeInit
        self.gap = gap
        self.pLearnerDelete = pLearnerDelete
        self.pLearnerAdd = pLearnerAdd
        self.pMutateAction = pMutateAction
        self.pActionIsTeam = pActionIsTeam
        self.maxTeamSize = maxTeamSize
        self.maxProgramSize = maxProgramSize
        self.pProgramDelete = pProgramDelete
        self.pProgramAdd = pProgramAdd
        self.pProgramSwap = pProgramSwap
        self.pProgramMutate = pProgramMutate

        # establish random for training
        self.rand = random.Random()
        if randSeed == 0:
            self.rand.seed(int(round(time.time())))
        else:
            self.rand.seed(randSeed)

        # create initial populations if starting anew
        if popInit is None:
            self.teams = []
            self.rootTeams = []
            self.learners = []
            self.curGen = 0
            self.initPops()
        else: # or carry on from object
            self.teams = popInit.teams
            self.rootTeams = popInit.rootTeams
            self.learners = popInit.learners
            self.curGen = popInit.gen
            TpgTrainer.uidCounter = popInit.uidCounter
            Learner.idCount = popInit.idCount

        self.teamQueue = list(self.rootTeams)
        self.tasks = set() # set of tasks done per all individuals

        for i in range(len(self.teamQueue)):
            self.teamQueue[i].rootNum = i

    """
    Attempts to add a task to the set of tasks. Needs to be made thread safe on
    client side if applicable.
    """
    def addTask(self, task):
        self.tasks.add(task)

    """
    Gets/pops the next team from the population for the client, in the form of
    an instance of TpgAgent. Needs to be made thread safe on client side if
    applicable.
    Returns:
        (TpgAgent) None if no team left in queue, means to call for evolution.
    """
    def getNextAgent(self):
        if len(self.teamQueue) == 0:
            agent = None
        else:
            agent = TpgAgent(self.teamQueue.pop(), self)

        return agent

    """
    Gets all the agents. Empties the teamQueue. Needs to be made thread safe on
    client side if applicable.
    Returns:
        (List[TpgAgent]) A list containing all of the remaining agents.
    """
    def getAllAgents(self):
        agents = list(reversed(
                [TpgAgent(team, trainer=self) for team in self.teamQueue]))
        self.teamQueue = []

        return agents

    """
    How many root teams / agents have not yet been withdrawn this generation.
    Can use this to check for end of generation, but is not thread safe. So a
    more reliable alternative is to call getNextTeam, and if None, then
    generation is done.
    """
    def remainingAgents(self):
        return len(self.teamQueue)

    """
    Creates the initial population of teams and learners, on initialization of
    training.
    """
    def initPops(self):
        # create teams to fill population
        for i in range(self.teamPopSizeInit):
            # take two distinct initial actions for each of two learners on team
            ac1 = self.rand.choice(self.actions)
            ac2 = self.rand.choice([a for a in self.actions if a != ac1])

            team = Team() # create new team

            # add/create first learner
            learner = Learner(ac1, self.maxProgramSize, randSeed=self.randSeed)
            team.addLearner(learner)
            self.learners.append(learner)

            # add/create second learner
            learner = Learner(ac2, self.maxProgramSize, randSeed=self.randSeed)
            team.addLearner(learner)
            self.learners.append(learner)

            # add other random learners
            learnerMax = self.rand.randint(0, self.maxTeamSize - 2)
            for i in range(learnerMax):
                learner = Learner(
                    self.actions[self.rand.randint(0,len(self.actions)-1)],
                    maxProgSize=self.maxProgramSize, randSeed=self.randSeed)
                team.addLearner(learner)
                self.learners.append(learner)

            team.uid = TpgTrainer.uidCounter
            TpgTrainer.uidCounter += 1

            # add into population
            self.teams.append(team)
            self.rootTeams.append(team)

    """
    To be called once all teams finish their runs of the current generation.
    Selects, creates, and preps the population for the next generation.
    Args:
        fitShare    : (Bool) Whether to use fitness sharing, uses single outcome
                      otherwise.
        outcomesKeep: (Str[]) List of outcomes to keep for next generation, so
                      unaltered teams won't have to be evaluated on the same
                      trial again, for efficiency. This does require some work
                      to be implemented on the client side.
    """
    def evolve(self, fitShare=True, outcomesKeep=[]):
        self.select(fitShare=fitShare)
        self.generateNewTeams()
        self.nextEpoch(outcomesKeep=outcomesKeep)

    """
    Selects the individuals to keep for next generation, deletes others. The
    amount deleted will be filled in through generating new teams.
    Args:
        fitShare: (Bool) Whether to use fitness sharing, uses single outcome
            otherwise.
    """
    def select(self, fitShare=True):
        delTeams = [] # list of teams to delete
        numKeep = int(self.gap * len(self.rootTeams)) # number of roots to keep

        teamScoresMap = {}
        taskTotalScores = [0]*len(self.tasks) # store overall score per task
        # get outcomes of all teams outcome[team][tasknum]
        for team in self.rootTeams:
            teamScoresMap[team] = [0]*len(self.tasks)
            for t,task in enumerate(self.tasks):
                teamScoresMap[team][t] = team.outcomes[task]
                taskTotalScores[t] += team.outcomes[task]#up task total

        scores = []
        if fitShare: # fitness share across all outcomes
            for team in teamScoresMap.keys():
                teamRelTaskScore = 0 # teams final fitness shared score
                for taskNum in range(len(self.tasks)):
                    if taskTotalScores[taskNum] != 0:
                        teamRelTaskScore += (teamScoresMap[team][taskNum] /
                                                    taskTotalScores[taskNum])
                scores.append((team, teamRelTaskScore))
        else: # just take first outcome
            for team in teamScoresMap.keys():
                scores.append((team, teamScoresMap[team][0]))

        scores.sort(key=itemgetter(1), reverse=True) # scores descending
        delTeams = scores[numKeep:] # teams to get rid of

        # properly delete the teams
        for team, _ in delTeams:
            team.erase()
            self.teams.remove(team)
            self.rootTeams.remove(team)


    """
    Generates new teams from existing teams (in the root population).
    """
    def generateNewTeams(self):
        parents = list(self.rootTeams) # parents are all original root teams
        # add teams until maxed size
        while len(self.teams) < self.teamPopSizeInit:
            # choose 2 random teams as parents
            par1 = self.rand.choice(parents)
            par2 = self.rand.choice([par for par in parents if par is not par1])

            # get learners
            par1Lrns = set(par1.learners)
            par2Lrns = set(par2.learners)

            # make 2 children at a time
            child1 = Team(birthGen=self.curGen)
            child2 = Team(birthGen=self.curGen)

            # new children get intersection of parents learners
            for learner in par1Lrns.intersection(par2Lrns):
                child1.addLearner(learner)
                child2.addLearner(learner)

            # learners unique to a parent goes to one child or other, with one
            # child having higher priority for a learner
            for learner in par1Lrns.symmetric_difference(par2Lrns):
                superChild = None
                subChild = None
                if self.rand.choice([True,False]) == True:
                    superChild = child1
                    subChild = child2
                else:
                    superChild = child2
                    subChild = child1

                # apply learner to child if can,
                # if not, give to other child if can
                if (len(superChild.learners) < self.maxTeamSize and
                        (len(superChild.learners) < 2 or
                            len(subChild.learners) >= 2)):
                    superChild.addLearner(learner)
                else:
                    subChild.addLearner(learner)

            self.mutate(child1) # attempt a mutation
            if (set(child1.learners) == set(par1.learners) or
                    set(child1.learners) == set(par2.learners)):
                while not self.mutate(child1): # attempt mutation untill it works
                    continue

            self.mutate(child2) # attempt a mutation
            if (set(child2.learners) == set(par1.learners) or
                    set(child2.learners) == set(par2.learners)):
                while not self.mutate(child2): # attempt mutation untill it works
                    continue

            child1.uid = TpgTrainer.uidCounter
            TpgTrainer.uidCounter += 1
            child2.uid = TpgTrainer.uidCounter
            TpgTrainer.uidCounter += 1

            # add children to team populations
            self.teams.append(child1)
            self.teams.append(child2)
            self.rootTeams.append(child1)
            self.rootTeams.append(child2)

    """
    Mutates a team and it's learners.
    Args:
        team: (Team) The team to mutate.
    Returns: (Bool) Whether the team was successfully mutated.
    """
    def mutate(self, team):
        isTeamChanged = False # flag to track when team actually changes
        tmpLearners = list(team.learners)
        self.rand.shuffle(tmpLearners)
        # delete some learners maybe
        for learner in tmpLearners:
            if len(team.learners) <= 2:
                break # must have atleast 2 learners
            if team.numAtomicActions() == 1 and learner.action.isAtomic():
                continue # never delete the sole atomic action
            # delete the learner
            if self.rand.uniform(0,1) < self.pLearnerDelete:
                team.removeLearner(learner)
                isTeamChanged = True

        # mutate the learners
        isTeamChanged = self.mutateLearners(team, tmpLearners) or isTeamChanged

        return isTeamChanged

    """
    Mutates the learners of a team.
    Args:
        team    : (Team) The team to mutate the learners of.
        learners: (Learner[]) All of the learners of the team before mutation.
    Returns:
        (Boolean) Whether the team ended up actually being mutated.
    """
    def mutateLearners(self, team, learners):
        isTeamChanged = False
        for learner in learners:
            if len(team.learners) == self.maxTeamSize:
                break; # limit team size
            # maybe add a learner
            if self.rand.uniform(0,1) < self.pLearnerAdd:
                isLearnerChanged = False
                lrnr = Learner(learner=learner, makeNew=True,
                        birthGen=self.curGen)
                # does and tells if did actually mutate program of learner
                isLearnerChanged = lrnr.mutateProgram(self.pProgramDelete,
                    self.pProgramAdd, self.pProgramSwap, self.pProgramMutate,
                    self.maxProgramSize)

                # maybe mutate the action of the learner
                if self.rand.uniform(0,1) < self.pMutateAction:
                    action = None
                    if self.rand.uniform(0,1) < self.pActionIsTeam: # team action
                        actionTeam = self.rand.choice(self.teams)
                        action = Action(actionTeam)
                        actionTeam.learnerRefCount += 1
                    else: # atomic action
                        action = Action(self.rand.choice(self.actions))
                    # try to mutate the learners action, and record whether
                    # learner changed at all
                    isLearnerChanged = (lrnr.mutateAction(action) or
                                                            isLearnerChanged)
                # apply changes
                if isLearnerChanged:
                    team.addLearner(lrnr)
                    self.learners.append(lrnr)
                    isTeamChanged = True

        return isTeamChanged

    """
    A sort of clean up method to prepare for a new epoch of learning.
    Args:
        outcomesKeep: (Str[]) List of outcomes to keep for next generation, so
            unaltered teams won't have to be evaluated on the same trial again,
            for efficiency. This does require some work to be implemented on the
            client side.
    """
    def nextEpoch(self, outcomesKeep=[]):
        # decide new root teams
        self.rootTeams = []
        for team in self.teams:
            # keep some outcomes for efficiency
            team.outcomes = { key: team.outcomes[key] for key in outcomesKeep }
            if team.learnerRefCount == 0:
                self.rootTeams.append(team) # root teams must have no references

        # remove unused learners
        tmpLearners = list(self.learners)
        for learner in tmpLearners:
            if learner.teamRefCount == 0:
                self.learners.remove(learner)
                # dereference if action is team
                if not learner.action.isAtomic():
                    learner.action.act.learnerRefCount -= 1

        self.teamQueue = list(self.rootTeams)
        self.rand.shuffle(self.teamQueue)
        for i in range(len(self.teamQueue)):
            self.teamQueue[i].rootNum = i

        self.tasks = set()

        self.curGen += 1
