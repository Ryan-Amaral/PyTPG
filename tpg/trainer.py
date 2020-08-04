from tpg.action_object import ActionObject
from tpg.program import Program
from tpg.learner import Learner
from tpg.team import Team
from tpg.agent import Agent
import random
import numpy as np
import pickle
from collections import namedtuple

"""
Functionality for actually growing TPG and evolving it to be functional.
"""
class Trainer:

    """
    Create a trainer to store the various evolutionary parameters, and runs under
    them.

    Important parameters:

    actions: List of actions, typically just set as 'range(n)' (n=18 for Atari).

    teamPopSize: Initial number of teams / root teams, to be maintained through
    evolution.

    rootBasedPop: Whether population size is based on root teams. If true there
    are always roughly the same amount of root teams (uses more RAM).
    Else it ensures the total team population size is 'teamPopSize' (uses
    less RAM).
    """
    def __init__(self, actions, teamPopSize=360, rootBasedPop=True, gap=0.5,
        inputSize=30720, nRegisters=8, initMaxTeamSize=5, initMaxProgSize=128,
        pLrnDel=0.7, pLrnAdd=0.7, pLrnMut=0.3, pProgMut=0.66, pActMut=0.33,
        pActAtom=0.5, pInstDel=0.5, pInstAdd=0.5, pInstSwp=1.0, pInstMut=1.0,
        doElites=True, nOperations=5, agentActVars=[], trainerMutateVars):

        # store all necessary params

        # first store actions properly
        if isinstance(actions, int):
            # all discrete actions
            self.actionCodes = range(actions)
        else: # list of lengths of each action
            # some may be real actions
            self.actionCodes = range(len(actions))
            self.actionLengths = list(actions)

        # population params
        self.teamPopSize = teamPopSize
        # whether population size is based on root teams or all teams
        self.rootBasedPop = rootBasedPop
        self.gap = gap # portion of root teams to remove each generation

        # input to agent (must be at-least size of input/state from environment)
        self.inputSize = inputSize # defaulted to number of Atari screen pixels
        # number of local memory registers each learner will have
        self.nRegisters = nRegisters

        # params for initializing evolution
        self.initMaxTeamSize = initMaxTeamSize # size of team = # of learners
        self.initMaxProgSize = initMaxProgSize # size of program = # of instructions

        # params for continued evolution
        self.pLrnDel = pLrnDel
        self.pLrnAdd = pLrnAdd
        self.pLrnMut = pLrnMut
        self.pProgMut = pProgMut
        self.pActMut = pActMut
        self.pActAtom = pActAtom
        self.pInstDel = pInstDel
        self.pInstAdd = pInstAdd
        self.pInstSwp = pInstSwp
        self.pInstMut = pInstMut

        # store paramers used in mutation here to not clutter mutate calls
        self.mutateParams = MutateParams(
            pLrnDel, pLrnAdd, pLrnMut, pProgMut, pActMut, pActAtom, pInstDel,
            pInstAdd, pInstSwp, pInstMut, self.actionCodes, nOperations,
            nRegisters, inputSize)

        # whether to keep elites
        self.doElites = doElites

        # how many operations programs can do, must match with program execute
        self.nOperations = nOperations

        # core components of TPG
        self.teams = []
        self.rootTeams = []
        self.learners = []
        self.elites = [] # save best at each task

        self.generation = 0 # track this

        self.initializePopulations()

    """
    Initializes a popoulation of teams and learners generated randomly with only
    atomic actions.
    """
    def initializePopulations(self):
        for i in range(self.teamPopSize):
            # create 2 unique actions and learners
            a1,a2 = random.sample(self.actionCodes, 2)

            l1 = Learner(program=Program(maxProgramLength=self.initMaxProgSize,
                                         nOperations=self.nOperations,
                                         nDestinations=self.nRegisters,
                                         inputSize=self.inputSize),
                        actionObj=ActionObject(actionCode=a1),
                        numRegisters=self.nRegisters)
            l2 = Learner(program=Program(maxProgramLength=self.initMaxProgSize,
                                         nOperations=self.nOperations,
                                         nDestinations=self.nRegisters,
                                         inputSize=self.inputSize),
                        actionObj=ActionObject(actionCode=a2),
                        numRegisters=self.nRegisters)

            # save learner population
            self.learners.append(l1)
            self.learners.append(l2)

            # create team and add initial learners
            team = Team()
            team.addLearner(l1)
            team.addLearner(l2)

            # add more learners
            moreLearners = random.randint(0, self.initMaxTeamSize-2)
            for i in range(moreLearners):
                # select action
                act = random.choice(self.actionCodes)

                # create new learner
                learner = Learner(program=Program(maxProgramLength=self.initMaxProgSize,
                                                  nOperations=self.nOperations,
                                                  nDestinations=self.nRegisters,
                                                  inputSize=self.inputSize),
                                  actionObj=ActionObject(actionCode=act),
                                  numRegisters=self.nRegisters)

                team.addLearner(learner)
                self.learners.append(learner)

            # save to team populations
            self.teams.append(team)
            self.rootTeams.append(team)

    """
    Gets rootTeams/agents. Sorts decending by sortTasks, and skips individuals
    who don't have scores for all skipTasks.
    """
    def getAgents(self, sortTasks=[], multiTaskType='min', skipTasks=[]):
        # remove those that get skipped
        rTeams = [team for team in self.rootTeams
                if len(skipTasks) == 0
                        or any(task not in team.outcomes for task in skipTasks)]

        if len(sortTasks) == 0: # just get all
            return [Agent(team, num=i) for i,team in enumerate(rTeams)]
        else:
            # apply scores/fitness to root teams
            self.scoreIndividuals(sortTasks, multiTaskType=multiTaskType,
                                                                doElites=False)
            # return teams sorted by fitness
            return [Agent(team, num=i) for i,team in
                    enumerate(sorted(rTeams,
                                    key=lambda tm: tm.fitness, reverse=True))]

    """
    Apply saved scores from list to the agents.
    """
    def applyScores(self, scores): # used when multiprocessing
        for score in scores:
            for rt in self.rootTeams:
                if score[0] == rt.id:
                    for task, outcome in score[1].items():
                        rt.outcomes[task] = outcome
                    break # on to next score

        return self.rootTeams

    """
    Evolve the populations for improvements.
    """
    def evolve(self, tasks=['task'], multiTaskType='min'):
        self.scoreIndividuals(tasks, multiTaskType=multiTaskType,
                doElites=self.doElites) # assign scores to individuals
        self.saveFitnessStats() # save fitness stats
        self.select() # select individuals to keep
        self.generate() # create new individuals from those kept
        self.nextEpoch() # set up for next generation

    """
    Assigns a fitness to each agent based on performance at the tasks. Assigns
    fitness values, or just returns sorted root teams.
    """
    def scoreIndividuals(self, tasks, multiTaskType='min', doElites=True):
        # handle generation of new elites, typically just done in evolution
        if doElites:
            # get the best agent at each task
            self.elites = [] # clear old elites
            for task in tasks:
                self.elites.append(max([team for team in self.rootTeams],
                                        key=lambda t: t.outcomes[task]))

        if len(tasks) == 1: # single fitness
            for team in self.rootTeams:
                team.fitness = team.outcomes[tasks[0]]
        else: # multi fitness
            # assign fitness to each agent based on tasks and score type
            if 'pareto' not in multiTaskType or 'lexicase' not in multiTaskType:
                self.simpleScorer(tasks, multiTaskType=multiTaskType)
            elif multiTaskType == 'paretoDominate':
                self.paretoDominateScorer(tasks)
            elif multiTaskType == 'paretoNonDominated':
                self.paretoNonDominatedScorer(tasks)
            elif multiTaskType == 'lexicaseStatic':
                self.lexicaseStaticScorer(tasks)
            elif multiTaskType == 'lexicaseDynamic':
                self.lexicaseDynamicScorer(tasks)

    """
    Gets either the min, max, or average score from each individual for ranking.
    """
    def simpleScorer(self, tasks, multiTaskType='min'):
        # first find min and max in each task
        mins = []
        maxs = []
        for task in tasks:
            mins.append(min([team.outcomes[task] for team in self.rootTeams]))
            maxs.append(max([team.outcomes[task] for team in self.rootTeams]))

        # assign fitness
        if multiTaskType == 'min':
            for rt in self.rootTeams:
                rt.fitness = min([(rt.outcomes[task]-mins[i])/(maxs[i]-mins[i])
                        for i,task in enumerate(tasks)])
        elif multiTaskType == 'max':
            for rt in self.rootTeams:
                rt.fitness = max([(rt.outcomes[task]-mins[i])/(maxs[i]-mins[i])
                        for i,task in enumerate(tasks)])
        elif multiTaskType == 'average':
            for rt in self.rootTeams:
                scores = [(rt.outcomes[task]-mins[i])/(maxs[i]-mins[i])
                            for i,task in enumerate(tasks)]
                rt.fitness = sum(scores)/len(scores)

    """
    Rank agents based on how many other agents it dominates
    """
    def paretoDominateScorer(self, tasks):
        for t1 in self.rootTeams:
            t1.fitness = 0
            for t2 in self.rootTeams:
                if t1 == t2:
                    continue # don't compare to self

                # compare on all tasks
                if all([t1.outcomes[task] >= t2.outcomes[task]
                         for task in tasks]):
                    t1.fitness += 1

    """
    Rank agents based on how many other agents don't dominate it
    """
    def paretoNonDominatedScorer(self, tasks):
        for t1 in self.rootTeams:
            t1.fitness = 0
            for t2 in self.rootTeams:
                if t1 == t2:
                    continue # don't compare to self

                # compare on all tasks
                if all([t1.outcomes[task] < t2.outcomes[task]
                         for task in tasks]):
                    t1.fitness -= 1

    def lexicaseStaticScorer(self, tasks):
        stasks = list(tasks)
        random.shuffle(stasks)

        for rt in self.rootTeams:
            rt.fitness = rt.outcomes[tasks[0]]


    def lexicaseDynamicScorer(self, tasks):
        pass

    """
    Save some stats on the fitness.
    """
    def saveFitnessStats(self):
        fitnesses = []
        for rt in self.rootTeams:
            fitnesses.append(rt.fitness)

        self.fitnessStats = {}
        self.fitnessStats['fitnesses'] = fitnesses
        self.fitnessStats['min'] = min(fitnesses)
        self.fitnessStats['max'] = max(fitnesses)
        self.fitnessStats['average'] = sum(fitnesses)/len(fitnesses)

    """
    Gets stats on some task.
    """
    def getTaskStats(self, task):
        scores = []
        for rt in self.rootTeams:
            scores.append(rt.outcomes[task])

        scoreStats = {}
        scoreStats['scores'] = scores
        scoreStats['min'] = min(scores)
        scoreStats['max'] = max(scores)
        scoreStats['average'] = sum(scores)/len(scores)

        return scoreStats

    """
    Delete a portion of the population according to gap size.
    """
    def select(self):
        rankedTeams = sorted(self.rootTeams, key=lambda rt: rt.fitness, reverse=True)
        numKeep = len(self.rootTeams) - int(len(self.rootTeams)*self.gap)
        deleteTeams = rankedTeams[numKeep:]

        # delete the team unless it is an elite (best at some task at-least)
        # don't delete elites because they may not be root
        for team in [t for t in deleteTeams if t not in self.elites]:
            for learner in team.learners:
                # delete learner from population if this is last team referencing
                if learner.numTeamsReferencing == 1:
                    # remove reference to team if applicable
                    if not learner.isActionAtomic():
                        learner.getActionTeam().numLearnersReferencing -= 1

                    self.learners.remove(learner) # permanently remove

            # remove learners from team and delete team from populations
            team.removeLearners()
            self.teams.remove(team)
            self.rootTeams.remove(team)

    """
    Generates new rootTeams based on existing teams.
    """
    def generate(self):

        oLearners = list(self.learners)
        oTeams = list(self.teams)

        while (len(self.teams) < self.teamPopSize or
                (self.rootBasedPop and self.countRootTeams() < self.teamPopSize)):

            # get parent root team, and child to be based on that
            parent = random.choice(self.rootTeams)
            child = Team()

            # child starts just like parent
            for learner in parent.learners:
                child.addLearner(learner)

            # then mutates
            child.mutate(self.mutateParams, oLearners, oTeams)

            self.teams.append(child)
            self.rootTeams.append(child)

    """
    Finalize populations and prepare for next generation/epoch.
    """
    def nextEpoch(self):
        # add in newly added learners, and decide root teams
        self.rootTeams = []
        for team in self.teams:
            # add any new learners to the population
            for learner in team.learners:
                if learner not in self.learners:
                    self.learners.append(learner)

            # maybe make root team
            if team.numLearnersReferencing == 0 or team in self.elites:
                self.rootTeams.append(team)

        self.generation += 1

    """
    Get the number of root teams currently residing in the teams population.
    """
    def countRootTeams(self):
        numRTeams = 0
        for team in self.teams:
            if team.numLearnersReferencing == 0:
                numRTeams += 1

        return numRTeams

    """
    Save the trainer to the file, saving any class values to the instance.
    """
    def saveToFile(self, fileName):
        self.teamIdCount = Team.idCount
        self.learnerIdCount = Learner.idCount
        self.programIdCount = Program.idCount

        pickle.dump(self, open(fileName, 'wb'))

"""
Load some trainer from the file, returning it and repopulate class values.
"""
def loadTrainer(fileName):
    trainer = pickle.load(open(fileName, 'rb'))

    Team.idCount = trainer.teamIdCount
    Learner.idCount = trainer.learnerIdCount
    Program.idCount = trainer.programIdCount

    return trainer

"""
Struct to hold parameters used in mutation to not clutter function calls.
"""
MutateParams = namedtuple("MutateParams", """pLrnDel pLrnAdd pLrnMut
    pProgMut pActMut pActAtom pInstDel pInstAdd pInstSwp pInstMut
    actionCodes nOperations nDestinations inputSize"""
)
