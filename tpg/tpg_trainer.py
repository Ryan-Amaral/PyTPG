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
        teamPopSize    : (Int) Team population size to maintain throughout evolution.
        rTeamPopSize   : (Int) Root ". Keep as 0 to not care about.
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
        tourneyGap     : (Float) Gap for tournament selection.
        actionRange    : ((Float, Float, Float)) A 3-tuple of min, max, and step
            size for actions (if multi-action).
        singlePop      : (Boolean) Whether this trainer will only handle one
            population. Initializes the population automatically if true.
    """
    def __init__(self, actions, randSeed=0, teamPopSize=360, rTeamPopSize=0,
            gap=0.5, pLearnerDelete=0.7, pLearnerAdd=0.7, pMutateAction=0.2,
            pActionIsTeam=0.5, maxTeamSize=5, maxProgramSize=96,
            pProgramDelete=0.5, pProgramAdd=0.5, pProgramSwap=1.0,
            pProgramMutate=1.0, tourneyGap=0.5,
            actionRange=(0.0, 1.0, 0.05), singlePop=True):

        # action values will be same among all populations
        self.actions = actions
        if isinstance(actions, int):
            self.multiAction = True
        else:
            self.multiAction = False
        self.actionRange = actionRange

        # default population values
        self.randSeed = randSeed
        self.teamPopSize = teamPopSize
        self.rTeamPopSize = rTeamPopSize
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

        # establish random for training
        self.rand = random.Random()
        if randSeed == 0:
            self.rand.seed()
        else:
            self.rand.seed(randSeed)

        # create dictionary to hold populations
        self.populations = {}

        # create initial populations if starting anew
        if singlePop == True:
            self.createPopulation()

    """
    Adds a new population to the trainer, for multi population training. popName
    must be unique among populations. If any other argument is None, the default
    value from the trainer will be taken.
    """
    def createPopulation(self, popName=None, teamPopSize=None, rTeamPopSize=None,
            gap=None, pLearnerDelete=None, pLearnerAdd=None, pMutateAction=None,
            pActionIsTeam=None, maxTeamSize=None, maxProgramSize=None,
            pProgramDelete=None, pProgramAdd=None, pProgramSwap=None,
            pProgramMutate=None, tourneyGap=None):

        self.populations[popName] = lambda: None # create default population

        if teamPopSize is not None: # use new val
            self.populations[popName].teamPopSize = teamPopSize
        else: # or take default value
            self.populations[popName].teamPopSize = self.teamPopSize

        if rTeamPopSize is not None: # use new val
            self.populations[popName].rTeamPopSize = rTeamPopSize
        else: # or take default value
            self.populations[popName].rTeamPopSize = self.rTeamPopSize

        if gap is not None: # use new val
            self.populations[popName].gap = gap
        else: # or take default value
            self.populations[popName].gap = self.gap

        if pLearnerDelete is not None: # use new val
            self.populations[popName].pLearnerDelete = pLearnerDelete
        else: # or take default value
            self.populations[popName].pLearnerDelete = self.pLearnerDelete

        if pLearnerAdd is not None: # use new val
            self.populations[popName].pLearnerAdd = pLearnerAdd
        else: # or take default value
            self.populations[popName].pLearnerAdd = self.pLearnerAdd

        if pMutateAction is not None: # use new val
            self.populations[popName].pMutateAction = pMutateAction
        else: # or take default value
            self.populations[popName].pMutateAction = self.pMutateAction

        if pActionIsTeam is not None: # use new val
            self.populations[popName].pActionIsTeam = pActionIsTeam
        else: # or take default value
            self.populations[popName].pActionIsTeam = self.pActionIsTeam

        if maxTeamSize is not None: # use new val
            self.populations[popName].maxTeamSize = maxTeamSize
        else: # or take default value
            self.populations[popName].maxTeamSize = self.maxTeamSize

        if maxProgramSize is not None: # use new val
            self.populations[popName].maxProgramSize = maxProgramSize
        else: # or take default value
            self.populations[popName].maxProgramSize = self.maxProgramSize

        if pProgramDelete is not None: # use new val
            self.populations[popName].pProgramDelete = pProgramDelete
        else: # or take default value
            self.populations[popName].pProgramDelete = self.pProgramDelete

        if pProgramDelete is not None: # use new val
            self.populations[popName].pProgramAdd = pProgramAdd
        else: # or take default value
            self.populations[popName].pProgramAdd = self.pProgramAdd

        if pProgramSwap is not None: # use new val
            self.populations[popName].pProgramSwap = pProgramSwap
        else: # or take default value
            self.populations[popName].pProgramSwap = self.pProgramSwap

        if pProgramMutate is not None: # use new val
            self.populations[popName].pProgramMutate = pProgramMutate
        else: # or take default value
            self.populations[popName].pProgramMutate = self.pProgramMutate

        if tourneyGap is not None: # use new val
            self.populations[popName].tourneyGap = tourneyGap
        else: # or take default value
            self.populations[popName].tourneyGap = self.tourneyGap

        # create populations
        self.populations[popName].teams = []
        self.populations[popName].rootTeams = []
        self.populations[popName].learners = []

        self.populations[popName].curGen = 0
        self.populations[popName].tournamentsPlayed = 0

        self.initPops(popName=None) # fill in the new population

        self.populations[popName].teamQueue = list(self.populations[popName].rootTeams)
        self.populations[popName].tasks = set() # set of tasks done per all individuals

        for i in range(len(self.populations[popName].teamQueue)):
            self.populations[popName].teamQueue[i].rootNum = i

        self.populations[popName].scoreStats = {}

        self.populations[popName].elites = [] # list of elites to save

    """
    Attempts to add a task to the set of tasks. Needs to be made thread safe on
    client side if applicable.
    """
    def addTask(self, task, popName=None):
        self.populations[popName].tasks.add(task)

    """
    Clears the outcomes of all root teams.
    Args:
        tasks:
            (Str[]) List of tasks to clear from the outcomes, leave as None to
            clear all outcomes.
    """
    def clearOutcomes(self, tasks=None, popName=None):
        for team in self.populations[popName].rootTeams:
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
        (Agent[]) The agents that scored the best. Based on positions, and points
        awarded to those positions.
    """
    def getBestAgents(self, tasks=None, amount=1, topn=3, popName=None):
        if tasks is None:
            tasks = self.populations[popName].tasks
        elif len(tasks) == 0:
            tasks = [TpgAgent.defTaskName]

        taskPosMatrix = {}
        # fill position matrix
        for task in tasks:
            taskPosMatrix[task] = sorted([rt for rt in self.populations[popName].rootTeams if task in rt.outcomes],
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

        bestTeams = sorted(teamPoints.items(), key=itemgetter(1), reverse=True)[:amount]

        return [TpgAgent(bt[0]) for bt in bestTeams]


    """
    Gets the topn best agents at each task.
    Args:
        tasks:
            (Str[]) List of tasks to base best on. If None, uses cur gen tasks.
            If Empty, uses default task.
        topn:
            (Int) Number of positions to consider.
    Returns:
        (Dict{str:Agent[]}) Dictionary with tasks as the keys, and a list of agents
        in order
    """
    def getAgentsPositions(self, tasks=None, topn=3, popName=None):
        if tasks is None:
            tasks = self.populations[popName].tasks
        elif len(tasks) == 0:
            tasks = [TpgAgent.defTaskName]

        taskPosMatrix = {}
        # fill position matrix
        for task in tasks:
            taskPosMatrix[task] = sorted([TpgAgent(rt) for rt in self.populations[popName].rootTeams if task in rt.outcomes],
                    key = lambda ag: ag.team.outcomes[task], reverse=True)[:topn]

        return taskPosMatrix

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
    def getNextAgent(self, noRef=False, popName=None):
        if len(self.populations[popName].teamQueue) == 0:
            agent = None
        else:
            trainer = self
            if noRef:
                trainer = None
            agent = TpgAgent(self.populations[popName].teamQueue.pop(), trainer=trainer)

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
    def getAllAgents(self, skipTasks=None, noRef=False, popName=None):
        agents = []
        trainer = self
        if noRef:
            trainer = None

        if skipTasks is None:
            agents = list(reversed(
                [TpgAgent(team, trainer=trainer) for team in self.populations[popName].teamQueue
                    if TpgAgent.defTaskName not in team.outcomes]))
        else:
            if len(skipTasks) == 0:
                agents = list(reversed(
                    [TpgAgent(team, trainer=trainer) for team in self.populations[popName].teamQueue]))
            else:
                agents = list(reversed(
                    [TpgAgent(team, trainer=trainer) for team in self.populations[popName].teamQueue
                        if any(task not in team.outcomes for task in skipTasks)]))

        self.populations[popName].teamQueue = []

        return agents

    """
    How many root teams / agents have not yet been withdrawn this generation.
    Can use this to check for end of generation, but is not thread safe. So a
    more reliable alternative is to call getNextTeam, and if None, then
    generation is done.
    """
    def remainingAgents(self, popName=None):
        return len(self.populations[popName].teamQueue)

    """
    Gets desired number of agents for tournament selection. Needs updating
    Args:
        tourneySize:
            (Int) Number of agents to take.
        replace:
            (Bool) Whether to keep selected teams in teamQueue. Absolutely
            should not if doing paralell tournaments.
    Returns:
        (List[TpgAgent]) A list containing the agents for the tournament.
    """
    def getTournamentAgents(self, tourneySize=8, replace=False, popName=None):
        agents = []
        if replace: # don't remove team from teamQueue
            teams = []
            for i in range(tourneySize):
                candidates = [team for team in self.populations[popName].teamQueue if team not in teams]
                if len(candidates) > 0:
                    teams.append(random.choice(candidates))
                    agents.append(TpgAgent(teams[-1], trainer=self))
        else: # remove team from queue
            for i in range(tourneySize):
                if len(self.populations[popName].teamQueue) > 0:
                    agents.append(TpgAgent(self.populations[popName].teamQueue.pop(), trainer=self))
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
    def applyAgentsScores(self, agents, popName=None):
        # make sure we do tasks in evolution
        for task in agents[0].team.outcomes:
            self.addTask(task, popName=popName)

        teams = [] # list of teams that the agents refer to

        for agent in agents:
            for team in self.populations[popName].rootTeams:
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
        (Team[]) All root teams, with the newly updated outcomes.
    """
    def applyScores(self, scores, popName=None):
        for score in scores:
            for team in self.populations[popName].rootTeams:
                if score[0] == team.uid:
                    for task, outcome in score[1].items():
                        team.outcomes[task] = outcome
                    break # on to next score

        return self.populations[popName].rootTeams

    """
    Creates the initial population of teams and learners, on initialization of
    training.
    """
    def initPops(self, popName=None):
        # create teams to fill population
        for i in range(self.populations[popName].teamPopSize):
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
            learner = Learner(ac1, self.populations[popName].maxProgramSize, randSeed=self.randSeed)
            team.addLearner(learner)
            self.populations[popName].learners.append(learner)

            # add/create second learner
            learner = Learner(ac2, self.populations[popName].maxProgramSize, randSeed=self.randSeed)
            team.addLearner(learner)
            self.populations[popName].learners.append(learner)

            # add other random learners
            #learnerMax = self.rand.randint(0, self.maxTeamSize - 2)
            learnerMax = self.populations[popName].maxTeamSize - 2
            for i in range(learnerMax):
                if not self.multiAction: # choose single number
                    ac = self.rand.choice(self.actions)
                else: # choose list of length self.actions within range
                    ac = [self.rand.uniform(minv, maxv) for i in range(self.actions)]
                learner = Learner(ac,maxProgSize=self.populations[popName].maxProgramSize, randSeed=self.randSeed)
                team.addLearner(learner)
                self.populations[popName].learners.append(learner)

            team.uid = TpgTrainer.teamIdCounter
            TpgTrainer.teamIdCounter += 1

            # add into population
            self.populations[popName].teams.append(team)
            self.populations[popName].rootTeams.append(team)

    """
    To be called once all teams finish their runs of the current generation.
    Selects, creates, and preps the population for the next generation. Or called
    when a tournament is completed.
    Args:
        fitMthd: (Str) Method to use for determining fitness. 'single' uses first
            task found. 'combine' uses a combined score of all tasks. 'fitshare'
            uses the fitness sharing method among the tasks.
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
    def evolve(self, fitMthd='single', tourneyAgents=None, tourneyTeams=None,
            tasks=None, elitistTasks=[], popName=None):
        rTeams = None # root teams to get from tourneyAgents, or None
        if tourneyAgents is not None:
            rTeams = [agent.team for agent in tourneyAgents]
        elif tourneyTeams is not None:
            rTeams = tourneyTeams
        self.select(fitMthd=fitMthd, rTeams=rTeams, tasks=tasks, elitistTasks=elitistTasks, popName=popName)
        self.generateNewTeams(parents=rTeams, popName=popName)
        self.nextEpoch(tourney=tourneyAgents is not None, popName=popName)

    """
    Selects the individuals to keep for next generation, deletes others. The
    amount deleted will be filled in through generating new teams.
    Args:
        fitMthd: (Str) Method to use for determining fitness. 'single' uses first
            task found. 'combine' uses a combined score of all tasks. 'fitshare'
            uses the fitness sharing method among the tasks.
        tourneyAgents: (Agent[]) The agents in a current tournament if doing
            tournament selection. Leave as None if doing generational selection.
        tasks: (Str[]) List of tasks to be evaluated on in selection. If empty,
            uses only default task. If None, uses tasks for current generation.
            Really only need if using tournament selection with multiple paralell
            tournaments where some may have different tasks, or any multiprocessing.
        elitistTasks: (Str[]) List of tasks to maintain elitism on, AKA keep the
            top performing agent for every task in the list.
    """
    def select(self, fitMthd='single', rTeams=None, tasks=None, elitistTasks=[], popName=None):
        gapSz = self.populations[popName].gap
        # if rTeams not supplied use whole root population
        if rTeams is None:
            rTeams = list(self.populations[popName].rootTeams)
        else:
            gapSz = self.populations[popName].tourneyGap

        delTeams = [] # list of teams to delete
        numKeep = int(gapSz*len(rTeams)) # number of roots to keep

        if tasks is None:
            tasks = self.populations[popName].tasks
        elif len(tasks) == 0:
            tasks = [TpgAgent.defTaskName]

        teamScoresMap = {}
        taskTotalScores = [0]*len(tasks) # store overall score per task
        # get outcomes of all teams outcome[team][tasknum]
        for team in rTeams:
            teamScoresMap[team] = [0]*len(tasks)
            for t,task in enumerate([tsk for tsk in tasks if tsk in team.outcomes]):
                teamScoresMap[team][t] = team.outcomes[task]

                taskTotalScores[t] += team.outcomes[task]# up task total

        scores = [] # scores used for fitnesses

        eliteTaskTeams = {} # save which team is elite for each task

        # find the elites for desired tasks
        eliteTeams = [] # teams to keep for elitism
        for eTask in elitistTasks: # change this to be all tasks in tasks or elitist tasks ( this only good for my current research)
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
            eliteTaskTeams[eTask] = bestTeam # save elite team of this tasks
            if bestTeam not in eliteTeams and eTask in elitistTasks:
                eliteTeams.append(bestTeam) # this is best team for task

        self.populations[popName].elites = eliteTeams

        statScores = [] # list of scores used for saving stats

        # assign fitness to individuals by selected method
        # use fitness sharing
        if fitMthd == 'fitShare': # fitness share across all outcomes
            for team in teamScoresMap.keys():
                teamRelTaskScore = 0 # teams final fitness shared score
                statScores.append(0)
                for taskNum in range(len(tasks)):
                    if taskTotalScores[taskNum] != 0:
                        teamRelTaskScore += (teamScoresMap[team][taskNum] /
                                                    taskTotalScores[taskNum])
                    statScores[-1] += teamScoresMap[team][taskNum]
                scores.append((team, teamRelTaskScore))

        # combine scores accross all tasks
        elif fitMthd == 'combine':
            teamTaskMap = {}
            for team in teamScoresMap.keys():
                teamFit = 0 # fitness accross tasks for individual
                teamTaskMap[team] = {}
                for task in tasks:
                    taskFit = 1/(1+(eliteTaskTeams[task].outcomes[task] -
                                    team.outcomes[task]))
                    teamFit += taskFit
                    teamTaskMap[team][task] = taskFit

                scores.append((team, teamFit))
                statScores.append(teamFit)


        # just use score of first task found
        elif fitMthd == 'single': # just take first outcome
            for team in teamScoresMap.keys():
                scores.append((team, teamScoresMap[team][0]))
                statScores.append(teamScoresMap[team][0])

        scores.sort(key=itemgetter(1), reverse=True) # scores descending

        # store tasks in descending order of top team for task selection
        if fitMthd == 'combine':
            self.populations[popName].topTeamTasks = [
                    tsk for (tsk,scr) in sorted(teamTaskMap[scores[0][0]].items(),
                    key=itemgetter(1), reverse=True)]

        self.saveScores(statScores, popName=popName) # save scores for reporting

        delTeams = scores[numKeep:] # teams to get rid of

        # properly delete the teams
        for team, _ in delTeams:
            if team in eliteTeams:
                continue # don't delete an elite, even if bad on current eval
            team.erase()
            self.populations[popName].teams.remove(team)
            self.populations[popName].rootTeams.remove(team)
            if team in rTeams:
                rTeams.remove(team)

    """
    Generates new teams from existing teams (in the root population).
    Args:
        parents:
            (Team[]) Parents to use, leave as None to use whole root popultaion.
    """
    def generateNewTeams(self, parents=None, popName=None):
        if parents is None:
            parents = list(self.populations[popName].rootTeams) # parents are all original root teams
        # add teams until maxed size
        while (len(self.populations[popName].teams) < self.populations[popName].teamPopSize or (self.populations[popName].rTeamPopSize > 0 and
                self.populations[popName].getRootTeamsSize() < self.populations[popName].rTeamPopSize)):
            # choose 2 random teams as parents
            par1 = self.rand.choice(parents)
            par2 = self.rand.choice([par for par in parents if par is not par1])

            # get learners
            par1Lrns = set(par1.learners)
            par2Lrns = set(par2.learners)

            # make 2 children at a time
            child1 = Team(birthGen=self.populations[popName].curGen)
            child2 = Team(birthGen=self.populations[popName].curGen)

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
                if (len(superChild.learners) < self.populations[popName].maxTeamSize and
                        (len(superChild.learners) < 2 or
                            len(subChild.learners) >= 2)):
                    superChild.addLearner(learner)
                else:
                    subChild.addLearner(learner)

            self.mutate(child1, popName=popName) # attempt a mutation
            if (set(child1.learners) == set(par1.learners) or
                    set(child1.learners) == set(par2.learners)):
                while not self.mutate(child1, popName=popName): # attempt mutation untill it works
                    continue

            self.mutate(child2, popName=popName) # attempt a mutation
            if (set(child2.learners) == set(par1.learners) or
                    set(child2.learners) == set(par2.learners)):
                while not self.mutate(child2, popName=popName): # attempt mutation untill it works
                    continue

            child1.uid = TpgTrainer.teamIdCounter
            TpgTrainer.teamIdCounter += 1
            child2.uid = TpgTrainer.teamIdCounter
            TpgTrainer.teamIdCounter += 1

            # add children to team populations
            self.populations[popName].teams.append(child1)
            self.populations[popName].teams.append(child2)
            self.populations[popName].rootTeams.append(child1)
            self.populations[popName].rootTeams.append(child2)

    """
    Mutates a team and it's learners.
    Args:
        team: (Team) The team to mutate.
    Returns: (Bool) Whether the team was successfully mutated.
    """
    def mutate(self, team, popName=None):
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
            if self.rand.uniform(0,1) < self.populations[popName].pLearnerDelete:
                team.removeLearner(learner)
                isTeamChanged = True

        # mutate the learners
        isTeamChanged = self.mutateLearners(team, tmpLearners, popName=popName) or isTeamChanged

        return isTeamChanged

    """
    Mutates the learners of a team.
    Args:
        team    : (Team) The team to mutate the learners of.
        learners: (Learner[]) All of the learners of the team before mutation.
    Returns:
        (Boolean) Whether the team ended up actually being mutated.
    """
    def mutateLearners(self, team, learners, popName=None):
        isTeamChanged = False
        for learner in learners:
            if len(team.learners) == self.populations[popName].maxTeamSize:
                break; # limit team size
            # maybe add a learner
            if self.rand.uniform(0,1) < self.populations[popName].pLearnerAdd:
                isLearnerChanged = False
                lrnr = Learner(learner=learner, makeNew=True,
                        birthGen=self.populations[popName].curGen)
                # does and tells if did actually mutate program of learner
                isLearnerChanged = lrnr.mutateProgram(self.populations[popName].pProgramDelete,
                    self.populations[popName].pProgramAdd, self.populations[popName].pProgramSwap, self.populations[popName].pProgramMutate,
                    self.populations[popName].maxProgramSize)

                # maybe mutate the action of the learner
                if self.rand.uniform(0,1) < self.populations[popName].pMutateAction:
                    action = None
                    if self.rand.uniform(0,1) < self.populations[popName].pActionIsTeam: # team action
                        actionTeam = self.rand.choice(self.populations[popName].teams)
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
                                    [self.clip(i+self.rand.choice([-stp,stp]), minv, maxv)
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
                    self.populations[popName].learners.append(lrnr)
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
    def nextEpoch(self, tourney=False, popName=None):
        # remove unused learners
        tmpLearners = list(self.populations[popName].learners)
        for learner in tmpLearners:
            if learner.teamRefCount == 0:
                self.populations[popName].learners.remove(learner)
                # dereference if action is team
                if not learner.action.isAtomic():
                    learner.action.act.learnerRefCount -= 1

        # decide new root teams
        self.populations[popName].rootTeams = []
        for team in self.populations[popName].teams:
            if team.learnerRefCount == 0 or team in self.populations[popName].elites:
                # root teams must have no references or be elite
                self.populations[popName].rootTeams.append(team)

        self.populations[popName].teamQueue = list(self.populations[popName].rootTeams)
        self.rand.shuffle(self.populations[popName].teamQueue)
        for i in range(len(self.populations[popName].teamQueue)):
            self.populations[popName].teamQueue[i].rootNum = i

        self.populations[popName].tasks = set()

        if tourney == True:
            self.populations[popName].tournamentsPlayed += 1
        else:
            self.populations[popName].curGen += 1

    def getRootTeamsSize(self, popName=None):
        numRTeams = 0
        for team in self.populations[popName].teams:
            if team.learnerRefCount == 0:
                numRTeams += 1

        return numRTeams

    """
    Saves stats about the previous generations scores, in a dict.
    """
    def saveScores(self, scores, popName=None):
        self.populations[popName].scoreStats = {}
        self.populations[popName].scoreStats['scores'] = scores
        self.populations[popName].scoreStats['min'] = min(scores)
        self.populations[popName].scoreStats['max'] = max(scores)
        self.populations[popName].scoreStats['average'] = sum(scores)/len(scores)

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
    def generateScoreStats(self, tasks=[], mode='sum', popName=None):
        if tasks is None:
            tasks = self.populations[popName].tasks
        elif len(tasks) == 0:
            tasks = [TpgAgent.defTaskName]

        scores = [0]*len(self.populations[popName].rootTeams)
        i = -1
        for team in self.populations[popName].rootTeams:
            i += 1
            for task in tasks:
                if task in team.outcomes:
                    scores[i] += team.outcomes[task]
            if mode == 'avg':
                scores[-1] /= len(tasks)

        self.populations[popName].scoreStats = {}
        self.populations[popName].scoreStats['scores'] = scores
        self.populations[popName].scoreStats['min'] = min(scores)
        self.populations[popName].scoreStats['max'] = max(scores)
        self.populations[popName].scoreStats['average'] = sum(scores)/len(scores)

        return self.populations[popName].scoreStats

    """
    Gets the score stats of all teams on the specified task.
    """
    def getTaskScores(self, task, popName=None):
        scores = [0]*len(self.populations[popName].rootTeams)

        i = -1
        for team in self.populations[popName].rootTeams:
            i += 1
            scores[i] = team.outcomes[task]

        scoreStats = {}
        scoreStats['scores'] = scores
        scoreStats['min'] = min(scores)
        scoreStats['max'] = max(scores)
        scoreStats['average'] = sum(scores)/len(scores)

        return scoreStats

    # https://stackoverflow.com/questions/4092528/how-to-clamp-an-integer-to-some-range
    def clip(self, val, minv, maxv):
        return max(minv, min(val, maxv))
