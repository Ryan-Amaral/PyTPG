"""
The main class to do training on a population of Teams.
Created By: Ryan Amaral.
Created On: June 29, 2018 13:44.
Created Because: I was tired of Java.
"""
class TpgTrainer:

    import random
    import time
    import pickle

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
        fitShare: Whether to use fitness sharing, uses single outcome otherwise
    """
    def evolve(self, fitShare=True):
        self.select(fitShare=fitShare)
        self.generateNewTeams()
        self.nextEpoch()
        pass

    """
    Selects the individuals to keep for next generation, deletes others. The
    amount deleted will be filled in through generating new teams.
    Args:
        fitShare: Whether to use fitness sharing, uses single outcome otherwise
    """
    def select(self, fitShare=True):
        delTeams = [] # list of teams to delete
        numKeep = self.gap * len(self.rootTeams) # number of roots to keep

        tasks = self.rootTeams[0].outcomes.keys()
        outcomes = {}
        # get outcomes of all teams
        for team in self.rootTeams:
            outcomes[team] = [0]*len(tasks)
            for t in range(len(tasks)):
                outcomes[team][t] = team.outcomes[tasks[t]]

    """
    Generates new teams from existing teams (in the root population).
    """
    def generateNewTeams(self):
        pass

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
                    if random.uniform(0,1) < self.pActionIsTeam:
                        action = Action(random.choice(self.teams))
                    else:
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
    """
    def nextEpoch(self):
        pass
