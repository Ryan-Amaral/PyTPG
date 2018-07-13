"""
The main class to do training on a population of Teams.
Created By: Ryan Amaral.
Created On: June 29, 2018 13:44.
Created Because: I was tired of Java.
"""
class TpgTrainer:

    import random
    import time
    from operator import itemgetter
    from __future__ import division

    """
    Initializes the Training procedure, potentially picking up from a
    previously left off point.
    Args:
        actions        : List of longs, the actions available in the env.
        randSeed       :
        teamPopSizeInit: Initial Team population size.
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
        if randSeed == 0:
            random.seed(int(round(time.time())))
        else:
            random.seed(randSeed)

        # create initial populations if starting anew
        if popInit is None:
            self.teams = []
            self.rootTeams = []
            self.learners = []
            self.curGen = 0
            initPops()
        else: # or carry on from object
            self.teams = popInit.teams
            self.rootTeams = popInit.rootTeams
            self.learners = popInit.learners
            self.curGen = popInit.gen

    """
    Creates the initial population of teams and learners, on initialization of
    training.
    """
    def initPops(self):
        # create teams to fill population
        for i in range(self.teamPopSizeInit):
            # take two distinct initial actions for each of two learners on team
            ac1 = self.actions[random.randint(0,len(self.actions))]
            tmpActions = [a for a in self.actions if a != ac1]
            ac2 = tmpActions[random.randint(0,len(tmpActions))]

            team = Team() # create new team

            # add/create first learner
            learner = Learner(ac1, self.maxProgramSize, randSeed=self.randSeed)
            team.addLearner(learner)
            self.learners.append(learner)

            # add/create seconds learner
            learner = Learner(ac2, self.maxProgramSize, randSeed=self.randSeed)
            team.addLearner(learner)
            self.learners.append(learner)

            # add other random learners
            learnerMax = random.randint(0, self.maxTeamSize - 2)
            for i in range(learnerMax):
                learner = Learner(
                    self.actions[random.randint(0,len(self.actions)),
                    self.maxProgramSize, randSeed=self.randSeed)
                team.addLearner(learner)
                self.learners.append(learner)

            # add into population
            self.teams.append(team)
            self.rootTeams.append(team)

    """
    To be called once all teams finish their runs of the current generation.
    Selects, creates, and preps the population for the next generation.
    Args:
        fitShare    : Whether to use fitness sharing, uses single outcome
            otherwise.
        outcomesKeep: List of outcomes to keep for next generation, so unaltered
            teams won't have to be evaluated on the same trial again, for
            efficiency. This does require some work to be implemented on the
            client side.
    """
    def evolve(self, fitShare=True, outcomesKeep=[]):
        self.select(fitShare=fitShare)
        self.generateNewTeams()
        self.nextEpoch(outcomesKeep=outcomesKeep)
        pass

    """
    Selects the individuals to keep for next generation, deletes others. The
    amount deleted will be filled in through generating new teams.
    Args:
        fitShare: Whether to use fitness sharing, uses single outcome otherwise.
    """
    def select(self, fitShare=True):
        delTeams = [] # list of teams to delete
        numKeep = self.gap * len(self.rootTeams) # number of roots to keep

        teamScoresMap = {}
        tasks = self.rootTeams[0].outcomes.keys()
        taskTotalScores = [0]*len(tasks) # store overall score per task
        # get outcomes of all teams outcome[team][tasknum]
        for team in self.rootTeams:
            teamScoresMap[team] = [0]*len(tasks)
            for t in range(len(tasks)):
                teamScoresMap[team][t] = team.outcomes[tasks[t]]
                taskTotalScores[t] += team.outcomes[tasks[t]] #add to task total

        scores = []
        if fitShare: # fitness share across all outcomes
            for team in teamScoresMap.keys():
                teamRelTaskScore = 0 # teams final fitness shared score
                for taskNum in range(len(tasks)):
                    teamRelTaskScore += teamScoresMap[team][taskNum] /
                                                taskTotalScores[taskNum]
                scores.append((team, teamRelTaskScore))
        else: # just take first outcome
            for team in teamScoresMap.keys():
                scores.append((team, teamScoresMap[team][0]))

        scores.sort(key=itemgetter(1), reverse=True) # scores descending
        delTeams = scores[numKeep:] # teams to get rid of

        # properly delete the teams
        for team in delTeams:
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
            par1 = random.choice(parents)
            par2 = random.choice([par for par in parents if par is not par1])

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
                if random.choice([True,False]) == True:
                    superChild = child1
                    subChild = child2
                else:
                    superChild = child2
                    subChild = child1

                # apply learner to child if can,
                # if not, give to other child if can

    """
    Mutates a team and it's learners.
    """
    def mutate(self, team):
        isTeamChanged = False # flag to track when team actually changes
        tmpLearners = list(team.learners)
        random.shuffle(tmpLearners)
        # delete some learners maybe
        for learner in tmpLearners:
            if len(team.learners) <= 2:
                break # must have atleast 2 learners
            if team.countAtomicActions() == 1 and learner.action.isAtomic():
                continue # never delete the sole atomic action
            # delete the learner
            if random.uniform(0,1) < self.pLearnerDelete:
                team.removeLearner(learner):
                isTeamChanged = True

        # mutate the learners
        isTeamChanged = mutateLearners or isTeamChanged

        return isTeamChanged

    """
    Mutates the learners of a team.
    """
    def mutateLearners(self, team, learners):
        for learner in learners:
            if len(team.learners) == self.maxTeamSize:
                break; # limit team size
            # maybe add a learner
            if random.uniform(0,1) < self.pLearnerAdd:
                isLearnerChanged = False
                lrnr = Learner(learner=learner, makeNew=True,
                        birthGen=self.curGen)
                # does and tells if did actually mutate program of learner
                isLearnerChanged = lrnr.mutateProgram(self.pProgramDelete,
                    self.pProgramAdd, self.pProgramSwap, self.pProgramMutate,
                    self.maxProgramSize)

                # maybe mutate the action of the learner
                if random.uniform(0,1) < self.pMutateAction:
                    action = None
                    if random.uniform(0,1) < self.pActionIsTeam: # team action
                        actionTeam = random.choice(self.teams)
                        action = Action(actionTeam)
                        actionTeam.learnerRefCount += 1
                    else: # atomic action
                        action = Action(random.choice(self.actions))
                    # try to mutate the learners action, and record whether
                    # learner changed at all
                    isLearnerChanged = lrnr.mutateAction(action) or
                                                                isLearnerChanged
                # apply changes
                if isLearnerChanged:
                    team.addLearner(lrnr)
                    self.learners.append(lrnr)
                    isTeamChanged = True

        return isTeamChanged

    """
    A sort of clean up method to prepare for a new epoch of learning.
    Args:
        outcomesKeep: List of outcomes to keep for next generation, so unaltered
            teams won't have to be evaluated on the same trial again, for
            efficiency. This does require some work to be implemented on the
            client side.
    """
    def nextEpoch(self, outcomesKeep=[]):
        # decide new root teams
        self.rootTeams.clear()
        for team in self.teams:
            # keep some outcomes for efficiency
            team.outcomes = {key:val for key, val in team.outcomes.iteritems()
                            if key in outcomesKeep}
            if team.learnerRefCount == 0:
                rootTeams.append(team) # root teams must have no references

        # remove unused learners
        tmpLearners = list(self.learners)
        for learner in tmpLearners:
            if learner.teamRefCount == 0:
                self.learners.remove(learner)
                # dereference if action is team
                if not learner.action.isAtomic:
                    learner.action.team.learnerRefCount -= 1

        # maybe do something about teamqueue here, don't know how I'm
        # implementing that yet

        self.curGen += 1
