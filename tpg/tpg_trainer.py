from __future__ import division
import random
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

    teamIdCounter = 0

    """
    Initializes the Training procedure, potentially picking up from a
    previously left off point.
    Args:
        actions        : (Int[] or Int) The actions available in the env. If
            Int[], the actions are each number in the list, use for single action
            output. If Int, the actions will be a list of length of the Int, use
            for multi action output.
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
        tourneyGap     : (Float) Gap for tournament selection.
        actionRange    : ((Float, Float, Float)) A 3-tuple of min, max, and step
            size for actions (if multi-action).
    """
    def __init__(self, actions, randSeed=0, teamPopSizeInit=360, gap=0.5,
            pLearnerDelete=0.7, pLearnerAdd=0.7, pMutateAction=0.2,
            pActionIsTeam=0.5, maxTeamSize=5, maxProgramSize=96,
            pProgramDelete=0.5, pProgramAdd=0.5, pProgramSwap=1.0,
            pProgramMutate=1.0, popInit=None, tourneyGap=0.5,
            actionRange=(0.0, 1.0, 0.05)):

        # set the variables
        self.actions = actions
        if isinstance(actions, int):
            self.multiAction = True
        else:
            self.multiAction = False
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
        self.tourneyGap = tourneyGap
        self.actionRange = actionRange

        # establish random for training
        self.rand = random.Random()
        if randSeed == 0:
            self.rand.seed()
        else:
            self.rand.seed(randSeed)

        # create initial populations if starting anew
        if popInit is None:
            self.teams = []
            self.rootTeams = []
            self.learners = []
            self.curGen = 0
            self.tournamentsPlayed = 0
            self.initPops()
        else: # or carry on from object
            self.teams = popInit.teams
            self.rootTeams = popInit.rootTeams
            self.learners = popInit.learners
            self.curGen = popInit.gen
            self.tournamentsPlayed = popInit.tournamentsPlayed
            TpgTrainer.teamIdCounter = popInit.teamIdCounter
            Learner.idCount = popInit.idCount

        self.teamQueue = list(self.rootTeams)
        self.tasks = set() # set of tasks done per all individuals

        for i in range(len(self.teamQueue)):
            self.teamQueue[i].rootNum = i

        self.scoreStats = {}

    """
    Attempts to add a task to the set of tasks. Needs to be made thread safe on
    client side if applicable.
    """
    def addTask(self, task):
        self.tasks.add(task)

    """
    Clears the outcomes of all root teams.
    Args:
        tasks:
            (Str[]) List of tasks to clear from the outcomes, leave as None to
            clear all outcomes.
    """
    def clearOutcomes(self, tasks=None):
        for team in self.rootTeams:
            if tasks is None:
                team.outcomes = {}
            else:
                for task in tasks:
                    team.outcomes.pop(task, None)

    """
    Gets the agent that scores the best at the specified tasks.
    Args:
        tasks:
            (Str[]) List of tasks to base best on. If None, uses cur gen tasks.
            If Empty, uses default task.
        amount:
            (Int) Number of best to take.
        topn:
            (Int) Positions to consider for points.
    Returns:
        (Agent) The agent that scored the best. Based on positions, and points
        awarded to those positions.
    """
    def getBestAgents(self, tasks=None, amount=1, topn=3):
        if tasks is None:
            tasks = self.tasks
        elif len(tasks) == 0:
            tasks = [TpgAgent.defTaskName]

        taskPosMatrix = {}
        # fill position matrix
        for task in tasks:
            taskPosMatrix[task] = sorted([rt for rt in self.rootTeams if task in rt.outcomes],
                    key = lambda rt: rt.outcomes[task], reverse=True)[:topn]

        teamPoints = {}
        # assign points to teams based on positions
        for task in tasks:
            for i in range(len(taskPosMatrix[task])):
                team = taskPosMatrix[task][i]
                if team not in teamPoints:
                    teamPoints[team] = topn - i
                else:
                    teamPoints[team] += topn - i

        bestTeams = sorted(teamPoints.items(), key=itemgetter(1), reverse=True)[amount]

        return [TpgAgent(bt[0]) for bt in bestTeams]

    """
    Gets/pops the next team from the population for the client, in the form of
    an instance of TpgAgent. Needs to be made thread safe on client side if
    applicable.
    Args:
        noRef:
            (Bool): Whether to link to this trainer, don't use if multiprocessing.
    Returns:
        (TpgAgent) None if no team left in queue, means to call for evolution.
    """
    def getNextAgent(self, noRef=False):
        if len(self.teamQueue) == 0:
            agent = None
        else:
            trainer = self
            if noRef:
                trainer = None
            agent = TpgAgent(self.teamQueue.pop(), trainer=trainer)

        return agent

    """
    Gets all the agents. Empties the teamQueue. Needs to be made thread safe on
    client side if applicable.
    Args:
        skipTasks:
            (String[]): Don't return agents that already completed all task in
            this list. If None, skips only the default tasks. If empty list,
            skips no task.
        noRef:
            (Bool): Whether to link to this trainer, don't use if multiprocessing.
    Returns:
        (List[TpgAgent]) A list containing all of the remaining agents.
    """
    def getAllAgents(self, skipTasks=None, noRef=False):
        agents = []
        trainer = self
        if noRef:
            trainer = None

        if skipTasks is None:
            agents = list(reversed(
                [TpgAgent(team, trainer=trainer) for team in self.teamQueue
                    if TpgAgent.defTaskName not in team.outcomes]))
        else:
            if len(skipTasks) == 0:
                agents = list(reversed(
                    [TpgAgent(team, trainer=trainer) for team in self.teamQueue]))
            else:
                agents = list(reversed(
                    [TpgAgent(team, trainer=trainer) for team in self.teamQueue
                        if any(task not in team.outcomes for task in skipTasks)]))

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
    Gets desired number of agents for tournament selection.
    Args:
        tourneySize:
            (Int) Number of agents to take.
        replace:
            (Bool) Whether to keep selected teams in teamQueue. Absolutely
            should not if doing paralell tournaments.
    Returns:
        (List[TpgAgent]) A list containing the agents for the tournament.
    """
    def getTournamentAgents(self, tourneySize=8, replace=False):
        agents = []
        if replace: # don't remove team from teamQueue
            teams = []
            for i in range(tourneySize):
                candidates = [team for team in self.teamQueue if team not in teams]
                if len(candidates) > 0:
                    teams.append(random.choice(candidates))
                    agents.append(TpgAgent(teams[-1], trainer=self))
        else: # remove team from queue
            for i in range(tourneySize):
                if len(self.teamQueue) > 0:
                    agents.append(TpgAgent(self.teamQueue.pop(), trainer=self))
                else:
                    break # no more agents to add

        return agents

    """
    Takes in a list of agents and applies the scores in those agents teams to
    the matching root teams in trainer. Because of some weird stuff that happens
    when multiprocessing. Very inefficient, I need to find a better way.
    Returns:
        (Team[]) The teams that the scores got applied to.
    """
    def applyAgentsScores(self, agents):
        # make sure we do tasks in evolution
        for task in agents[0].team.outcomes:
            self.addTask(task)

        teams = [] # list of teams that the agents refer to

        for agent in agents:
            for team in self.rootTeams:
                if agent.team.uid == team.uid:
                    teams.append(team)
                    for task, outcome in agent.team.outcomes.items():
                        team.outcomes[task] = outcome
                    break # on to next agent

        return teams

    """
    Takes in a list of 2-tuples containing the team uid and outcome dict. Just
    like applyAgentsScores, but more efficient on the client side, when used
    with multiprocessing.
    Args:
        scores:
            ((uid, outcomes)) UID of the team, followed by the outcome dict to
            apply.
    Returns:
        (Team[]) The teams that the scores got applied to.
    """
    def applyScores(self, scores):

        teams = [] # list of teams that the agents refer to

        for score in scores:
            for team in self.rootTeams:
                if score[0] == team.uid:
                    teams.append(team)
                    for task, outcome in score[1].items():
                        team.outcomes[task] = outcome
                    break # on to next score

        return teams

    """
    Creates the initial population of teams and learners, on initialization of
    training.
    """
    def initPops(self):
        # create teams to fill population
        for i in range(self.teamPopSizeInit):
            # take two distinct initial actions for each of two learners on team
            if not self.multiAction: # choose single number
                ac1 = self.rand.choice(self.actions)
                ac2 = self.rand.choice([a for a in self.actions if a != ac1])
            else: # choose list of length self.actions within range
                minv = self.actionRange[0]
                maxv = self.actionRange[1]
                ac1 = [self.rand.uniform(minv, maxv) for i in range(self.actions)]
                ac2 = [self.rand.uniform(minv, maxv) for i in range(self.actions)]

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
                if not self.multiAction: # choose single number
                    ac = self.rand.choice(self.actions)
                else: # choose list of length self.actions within range
                    ac = [self.rand.uniform(minv, maxv) for i in range(self.actions)]
                learner = Learner(ac,maxProgSize=self.maxProgramSize, randSeed=self.randSeed)
                team.addLearner(learner)
                self.learners.append(learner)

            team.uid = TpgTrainer.teamIdCounter
            TpgTrainer.teamIdCounter += 1

            # add into population
            self.teams.append(team)
            self.rootTeams.append(team)

    """
    To be called once all teams finish their runs of the current generation.
    Selects, creates, and preps the population for the next generation. Or called
    when a tournament is completed.
    Args:
        fitShare    : (Bool) Whether to use fitness sharing, uses single outcome
                      otherwise.
        tourneyAgents: (Agent[]) The agents in a current tournament if doing
            tournament selection. Leave as None if doing generational selection.
        tourneyTeams: (Team[]) Like tourneyAgents, but teams in case thats all
            you have, probably in case of multiprocessing.
        tasks: (Str[]) List of tasks to be evaluated on in selection. If empty,
            uses only default task. If None, uses tasks for current generation.
            Really only need if using tournament selection with multiple paralell
            tournaments where some may have different tasks, or any multiprocessing.
        elitistTasks: (Str[]) List of tasks to maintain elitism on, AKA keep the
            top performing agent for every task in the list.
    """
    def evolve(self, fitShare=False, tourneyAgents=None, tourneyTeams=None,
            tasks=None, elitistTasks=[]):
        rTeams = None # root teams to get from tourneyAgents, or None
        if tourneyAgents is not None:
            rTeams = [agent.team for agent in tourneyAgents]
        elif tourneyTeams is not None:
            rTeams = tourneyTeams
        self.select(fitShare=fitShare, rTeams=rTeams, tasks=tasks, elitistTasks=elitistTasks)
        self.generateNewTeams(parents=rTeams)
        self.nextEpoch(tourney=tourneyAgents is not None)

    """
    Selects the individuals to keep for next generation, deletes others. The
    amount deleted will be filled in through generating new teams.
    Args:
        fitShare: (Bool) Whether to use fitness sharing, uses single outcome
            otherwise.
        tourneyAgents: (Agent[]) The agents in a current tournament if doing
            tournament selection. Leave as None if doing generational selection.
        tasks: (Str[]) List of tasks to be evaluated on in selection. If empty,
            uses only default task. If None, uses tasks for current generation.
            Really only need if using tournament selection with multiple paralell
            tournaments where some may have different tasks, or any multiprocessing.
        elitistTasks: (Str[]) List of tasks to maintain elitism on, AKA keep the
            top performing agent for every task in the list.
    """
    def select(self, fitShare=False, rTeams=None, tasks=None, elitistTasks=[]):
        gapSz = self.gap
        # if rTeams not supplied use whole root population
        if rTeams is None:
            rTeams = list(self.rootTeams)
        else:
            gapSz = self.tourneyGap

        delTeams = [] # list of teams to delete
        numKeep = int(gapSz*len(rTeams)) # number of roots to keep

        if tasks is None:
            tasks = self.tasks
        elif len(tasks) == 0:
            tasks = [TpgAgent.defTaskName]

        statScores = [] # list of scores used for saving stats

        teamScoresMap = {}
        taskTotalScores = [0]*len(tasks) # store overall score per task
        # get outcomes of all teams outcome[team][tasknum]
        for team in rTeams:
            teamScoresMap[team] = [0]*len(tasks)
            for t,task in enumerate([tsk for tsk in tasks if tsk in team.outcomes]):
                teamScoresMap[team][t] = team.outcomes[task]
                taskTotalScores[t] += team.outcomes[task]# up task total

        scores = []
        if fitShare: # fitness share across all outcomes
            for team in teamScoresMap.keys():
                teamRelTaskScore = 0 # teams final fitness shared score
                statScores.append(0)
                for taskNum in range(len(tasks)):
                    if taskTotalScores[taskNum] != 0:
                        teamRelTaskScore += (teamScoresMap[team][taskNum] /
                                                    taskTotalScores[taskNum])
                    statScores[-1] += teamScoresMap[team][taskNum]
                scores.append((team, teamRelTaskScore))
        else: # just take first outcome
            for team in teamScoresMap.keys():
                scores.append((team, teamScoresMap[team][0]))
                statScores.append(teamScoresMap[team][0])

        eliteTeams = [] # teams to keep for elitism
        for eTask in elitistTasks:
            bestScore = 0
            bestTeam = None
            for team in rTeams:
                if eTask in team.outcomes:
                    if bestTeam is None: # default first to best
                        bestScore = team.outcomes[eTask]
                        bestTeam = team
                    else: # seach for best after first
                        if team.outcomes[eTask] > bestScore:
                            bestScore = team.outcomes[eTask]
                            bestTeam = team
            if bestTeam not in eliteTeams:
                eliteTeams.append(bestTeam) # this is best team for task

        scores.sort(key=itemgetter(1), reverse=True) # scores descending

        self.saveScores(statScores) # save scores for reporting

        delTeams = scores[numKeep:] # teams to get rid of

        # properly delete the teams
        for team, _ in delTeams:
            if team in eliteTeams:
                continue # don't delete an elite, even if bad on current eval
            team.erase()
            self.teams.remove(team)
            self.rootTeams.remove(team)
            if team in rTeams:
                rTeams.remove(team)

    """
    Generates new teams from existing teams (in the root population).
    Args:
        parents:
            (Team[]) Parents to use, leave as None to use whole root popultaion.
    """
    def generateNewTeams(self, parents=None):
        if parents is None:
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

            child1.uid = TpgTrainer.teamIdCounter
            TpgTrainer.teamIdCounter += 1
            child2.uid = TpgTrainer.teamIdCounter
            TpgTrainer.teamIdCounter += 1

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
                    else: # atomic action
                        if not self.multiAction: # choose single number
                            action = Action(self.rand.choice(self.actions))
                        else: # choose list of length self.actions within range
                            minv = self.actionRange[0]
                            maxv = self.actionRange[1]
                            if lrnr.action.isAtomic():
                                act = lrnr.action.act
                                stp = self.actionRange[2]
                                action = Action(
                                    [clip(i+self.rand.choice([-stp,stp]), minv, maxv)
                                                for i in act])
                            else:
                                action = Action([self.rand.uniform(minv, maxv)
                                            for i in range(self.actions)])

                    # try to mutate the learners action, and record whether
                    # learner changed at all
                    isLearnerChanged = (lrnr.mutateAction(action) or
                                                            isLearnerChanged)
                # apply changes
                if isLearnerChanged:
                    team.addLearner(lrnr)
                    self.learners.append(lrnr)
                    isTeamChanged = True
                    if not lrnr.action.isAtomic():
                        lrnr.action.act.learnerRefCount += 1

        return isTeamChanged

    """
    A sort of clean up method to prepare for a new epoch of learning.
    Args:
        tourney:
            (Bool) Whether doing tournament selection.
    """
    def nextEpoch(self, tourney=False):
        # remove unused learners
        tmpLearners = list(self.learners)
        for learner in tmpLearners:
            if learner.teamRefCount == 0:
                self.learners.remove(learner)
                # dereference if action is team
                if not learner.action.isAtomic():
                    learner.action.act.learnerRefCount -= 1

        # decide new root teams
        self.rootTeams = []
        for team in self.teams:
            if team.learnerRefCount == 0:
                self.rootTeams.append(team) # root teams must have no references

        self.teamQueue = list(self.rootTeams)
        self.rand.shuffle(self.teamQueue)
        for i in range(len(self.teamQueue)):
            self.teamQueue[i].rootNum = i

        self.tasks = set()

        if tourney == True:
            self.tournamentsPlayed += 1
        else:
            self.curGen += 1

    """
    Saves stats about the previous generations scores, in a dict.
    """
    def saveScores(self, scores):
        self.scoreStats = {}
        self.scoreStats['scores'] = scores
        self.scoreStats['min'] = min(scores)
        self.scoreStats['max'] = max(scores)
        self.scoreStats['average'] = sum(scores)/len(scores)

    """
    Iterates through all root teams to generate a score stats now.
    Args:
        tasks:
            (Str[]) The tasks to score on. Leave empty for default score. None
            for whatever was used the previous generation.
        mode:
            (Str) How to handle multiple tasks. 'sum' to sum them. 'avg' to
            average them.
    Returns:
        (Dict<Str,float): The score stats.
    """
    def generateScoreStats(self, tasks=[], mode='sum'):
        if tasks is None:
            tasks = self.tasks
        elif len(tasks) == 0:
            tasks = [TpgAgent.defTaskName]

        scores = [0]*len(self.rootTeams)
        i = -1
        for team in self.rootTeams:
            i += 1
            for task in tasks:
                if task in team.outcomes:
                    scores[i] += team.outcomes[task]
            if mode == 'avg':
                scores[-1] /= len(tasks)

        self.scoreStats = {}
        self.scoreStats['scores'] = scores
        self.scoreStats['min'] = min(scores)
        self.scoreStats['max'] = max(scores)
        self.scoreStats['average'] = sum(scores)/len(scores)

        return self.scoreStats

    """
    Gets the current state of the trainer by returning an instance of TrainerState
    which contains the team population, rootTeams population, learner population,
    current generation, and team and learner id counters.
    """
    def getTrainerState():
        return TrainerState(self.teams, self.rootTeams, self.learners,
            self.curGen, self.tournamentsPlayed)

    # https://stackoverflow.com/questions/4092528/how-to-clamp-an-integer-to-some-range
    def clip(val, minv, maxv):
        return max(minv, min(val, maxv))

"""
Contains all information needed to pick up from wherever last left off. An
instance can be obtained by the client and saved with something like Pickle.
"""
class TrainerState:
    def __init__(self, teams, rootTeams, learners, gen, tournamentsPlayed):
        self.teams = teams
        self.rootTeams = rootTeams
        self.learners = learners
        self.curGen = gen
        self.tournamentsPlayed = tournamentsPlayed
        self.teamIdCounter = TpgTrainer.teamIdCounter
        self.learnerIdCounter = Learner.learnerIdCounter
