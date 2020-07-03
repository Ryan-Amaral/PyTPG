from tpg.program import Program
from tpg.learner import Learner
from tpg.team import Team
from tpg.agent import Agent
from tpg.action_object import ActionObject
import random
import numpy as np
import pickle

"""
Functionality for actually growing TPG and evolving it to be functional.
"""
class Trainer:


    """
    Create a trainer to store the various evolutionary parameters, and runs under
    them.

    Important parameters:

    actions: Integer number of actions if output is just a single discrete action,
    ex: '18' for the 18 possible actions in an Atari (ALE) gym enironment. Returned
    actions being from 0 to n-1, if n is the number of actions selected.
    Or list of integers (length equal to number of actions), where each element
    is the size of the real vector for that action, ex: '[0,2]' where 0 corresponds
    to a discrete buttom press and 2 corresponds to a 2d joystick position. Or
    ex: '[1,2]' functions the same as the previous example except now the 1 corresponds
    to a real value instead of discrete (pressure sensitive button for example).

    teamPopSize: Initial number of teams / root teams, to be maintained through
    evolution.

    rootBasedPop: Whether population size is based on root teams. If true there
    are always roughly the same amount of root teams (uses more RAM).
    Else it ensures the total team population size is 'teamPopSize' (uses
    less RAM).

    sharedMemory: Whether to use the shared memory module to have more long term
    memory.
    """
    def __init__(self, actions, teamPopSize=360, rootBasedPop=True, sharedMemory=False,
        gap=0.5, uniqueProgThresh=0, initMaxTeamSize=5, initMaxProgSize=128,
        actionProgSize=64, registerSize=8,
        pDelLrn=0.7, pAddLrn=0.7, pMutLrn=0.3, pMutProg=0.66, pMutAct=0.33,
        pActAtom=0.5, pDelInst=0.5, pAddInst=0.5, pSwpInst=1.0, pMutInst=1.0,
        pSwapMultiAct=0.66, pChangeMultiAct=0.40, doElites=True,
        sourceRange=30720, memMatrixShape=(100,8)):

        # store all necessary params

        # first store actions properly
        if isinstance(actions, int):
            self.actions = range(actions)
            self.actionLengths = [0]*actions
        else:
            self.actions = range(len(actions))
            self.actionLengths = list(actions)

        self.traversal = traversal
        self.teamPopSize = teamPopSize
        self.rootBasedPop = rootBasedPop
        self.gap = gap # portion of root teams to remove each generation
        # threshold to accept mutated programs
        self.uniqueProgThresh = uniqueProgThresh # about 1e-5 is good

        self.pDelLrn = pDelLrn
        self.pAddLrn = pAddLrn
        self.pMutLrn = pMutLrn
        self.pMutProg = pMutProg
        self.pMutAct = pMutAct
        self.pActAtom = pActAtom
        self.pDelInst = pDelInst
        self.pAddInst = pAddInst
        self.pSwpInst = pSwpInst
        self.pMutInst = pMutInst
        self.pSwapMultiAct = pSwapMultiAct
        self.pChangeMultiAct = pChangeMultiAct
        self.doElites = doElites

        self.teams = []
        self.rootTeams = []
        self.learners = []

        self.elites = [] # save best at each task

        self.generation = 0

        #Set operation range
        Program.operationRange = 5

        Program.destinationRange = registerSize
        Program.sourceRange = sourceRange

        self.initializePopulations(initMaxTeamSize, initMaxProgSize, registerSize)
        
        # extra operations if memory
        if not sharedMemory:
            Program.operationRange = 5
        else:
            Program.operationRange = 7

        self.memMatrix = np.zeros(shape=memMatrixShape)

    """
    Initializes a popoulation of teams and learners generated randomly with only
    atomic actions.
    """
    def initializePopulations(self, initMaxTeamSize, initMaxProgSize, registerSize):
        for i in range(self.teamPopSize):
            # create 2 unique actions and learners
            ac1,ac2 = random.sample(self.actions, 2)
            ao1 = ActionObject(actionCode=ac1, actionLength=self.actionLengths[ac1],
                maxProgramLength=initMaxProgSize, nRegisters=registerSize)
            ao2 = ActionObject(actionCode=ac2, actionLength=self.actionLengths[ac2],
                maxProgramLength=initMaxProgSize, nRegisters=registerSize)

            l1 = Learner(program=Program(maxProgramLength=initMaxProgSize),
                                         actionObj=ao1, numRegisters=registerSize)
            l2 = Learner(program=Program(maxProgramLength=initMaxProgSize),
                                         actionObj=ao2, numRegisters=registerSize)

            # save learner population
            self.learners.append(l1)
            self.learners.append(l2)

            # create team, add initial learners, set traversal type
            team = Team(self.traversal)
            team.addLearner(l1)
            team.addLearner(l2)

            # add more learners
            moreLearners = random.randint(0, initMaxTeamSize-2)
            for i in range(moreLearners):
                # select action
                ac = random.choice(self.actions)
                ao = ActionObject(actionCode=ac, actionLength=self.actionLengths[ac],
                    maxProgramLength=initMaxProgSize, nRegisters=registerSize)

                # create new learner
                learner = Learner(program=Program(maxProgramLength=initMaxProgSize),
                                  actionObj=ao, numRegisters=registerSize)
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
            return [Agent(team, self.memMatrix, num=i) for i,team in enumerate(rTeams)]
        else:
            # apply scores/fitness to root teams
            self.scoreIndividuals(sortTasks, multiTaskType=multiTaskType,
                                                                doElites=False)
            # return teams sorted by fitness
            return [Agent(team, self.memMatrix, num=i) for i,team in
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
                        learner.actionObj.teamAction.numLearnersReferencing -= 1

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
            child = Team(self.traversal)

            # child starts just like parent
            for learner in parent.learners:
                child.addLearner(learner)

            if self.uniqueProgThresh > 0:
                inputs, outputs = self.getLearnersInsOuts(oLearners)
            else:
                inputs = None
                outputs = None

            actProgMut = (self.generation % 20 >= 10)
            # then mutates
            child.mutate(self.pDelLrn, self.pAddLrn, self.pMutLrn, oLearners,
                        self.pMutProg, self.pMutAct, self.pActAtom,
                        self.actions, self.actionLengths, oTeams,
                        self.pDelInst, self.pAddInst, self.pSwpInst, self.pMutInst,
                        actProgMut, self.uniqueProgThresh, inputs=inputs, outputs=outputs)

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
    Returns the input and output of each learner bid in each state.
    As [learner, stateNum]. Inputs being states, outputs being floats (bid values)
    """
    def getLearnersInsOuts(self, learners, clearStates=True):
        inputs = []
        outputs = []
        for lrnr in learners:
            lrnrInputs = []
            lrnrOutputs = []
            for state in lrnr.states:
                regs = np.zeros(len(lrnr.registers))
                Program.execute(state, regs,
                                lrnr.program.modes, lrnr.program.operations,
                                lrnr.program.destinations, lrnr.program.sources)
                lrnrInputs.append(state)
                lrnrOutputs.append(regs[0])

            if clearStates: # free up some space
                lrnr.states = []

            inputs.append(lrnrInputs)
            outputs.append(lrnrOutputs)

        return inputs, outputs

    """
    Save the trainer to the file, saving any class values to the instance.
    """
    def saveToFile(self, fileName):
        self.teamIdCount = Team.idCount
        self.learnerIdCount = Learner.idCount
        self.programIdCount = Program.idCount
        self.operationRange = Program.operationRange
        self.destinationRange = Program.destinationRange
        self.sourceRange = Program.sourceRange

        pickle.dump(self, open(fileName, 'wb'))

"""
Load some trainer from the file, returning it and repopulate class values.
"""
def loadTrainer(fileName):
    trainer = pickle.load(open(fileName, 'rb'))

    Team.idCount = trainer.teamIdCount
    Learner.idCount = trainer.learnerIdCount
    Program.idCount = trainer.programIdCount
    Program.operationRange = trainer.operationRange
    Program.destinationRange = trainer.destinationRange
    Program.sourceRange = trainer.sourceRange

    return trainer
