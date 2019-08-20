from tpg.program import Program
from tpg.learner import Learner
from tpg.team import Team
from tpg.agent import Agent
import random
import numpy as np

"""
Functionality for actually growing TPG and evolving it to be functional.
"""
class Trainer:

    """
    Create a trainer to store the various evolutionary parameters. Actions are
    either a list of discrete (int) actions, or a number (int) of actions, each
    of which will be between 0 and 1.
    """
    def __init__(self, actions, teamPopSize=360, rTeamPopSize=360, gap=0.5,
        uniqueProgThresh=0, initMaxTeamSize=5, initMaxProgSize=128, registerSize=8,
        pDelLrn=0.7, pAddLrn=0.7, pMutLrn=0.3, pMutProg=0.66, pMutAct=0.33,
        pActAtom=0.5, pDelInst=0.5, pAddInst=0.5, pSwpInst=1.0, pMutInst=1.0,
        pSwapMultiAct=0.66, pChangeMultiAct=0.40):

        # store all necessary params
        self.actions = actions
        self.multiAction = isinstance(self.actions, int)

        self.teamPopSize = teamPopSize
        self.rTeamPopSize = rTeamPopSize
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

        self.teams = []
        self.rootTeams = []
        self.learners = []

        self.elites = [] # save best at each task

        self.generation = 0

        self.initializePopulations(initMaxTeamSize, initMaxProgSize, registerSize)

    """
    Initializes a popoulation of teams and learners generated randomly with only
    atomic actions.
    """
    def initializePopulations(self, initMaxTeamSize, initMaxProgSize, registerSize):
        for i in range(self.teamPopSize):
            # create 2 unique actions and learners
            if self.multiAction == False:
                a1,a2 = random.sample(self.actions, 2)
            else:
                a1 = [random.uniform(0,1) for _ in range(self.actions)]
                a2 = [random.uniform(0,1) for _ in range(self.actions)]
            l1 = Learner(program=Program(maxProgramLength=initMaxProgSize),
                                         action=a1, numRegisters=registerSize)
            l2 = Learner(program=Program(maxProgramLength=initMaxProgSize),
                                         action=a2, numRegisters=registerSize)

            # save learner population
            self.learners.append(l1)
            self.learners.append(l2)

            # create team and add initial learners
            team = Team()
            team.addLearner(l1)
            team.addLearner(l2)

            # add more learners
            moreLearners = random.randint(0, initMaxTeamSize-2)
            for i in range(moreLearners):
                # select action
                if self.multiAction == False:
                    act = random.choice(self.actions)
                else:
                    act = [random.uniform(0,1) for _ in range(self.actions)]
                # create new learner
                learner = Learner(program=Program(maxProgramLength=initMaxProgSize),
                                  action=act,
                                  numRegisters=registerSize)
                team.addLearner(learner)
                self.learners.append(learner)

            # save to team populations
            self.teams.append(team)
            self.rootTeams.append(team)

    """
    Gets all rootTeams/agents.
    """
    def getAgents(self):
        agents = []
        for i,t in enumerate(self.rootTeams):
            a = Agent(t, num=i)
            agents.append(a)

        return agents

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
    def evolve(self, task='task'):
        self.scoreIndividuals(task) # assign scores to individuals
        self.saveFitnessStats() # save fitness stats
        self.select() # select individuals to keep
        self.generate() # create new individuals from those kept
        self.nextEpoch() # set up for next generation

    """
    Assigns a fitness to each agent based on performance at the task.
    """
    def scoreIndividuals(self, task):
        self.elites = [] # empty out elites
        elite = None
        for rt in self.rootTeams:
            rt.fitness = rt.outcomes[task]
            if elite is None or rt.fitness > elite.fitness:
                elite = rt

        # save best, even if no longer root after mutate
        self.elites.append(elite)

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
                        learner.action.numLearnersReferencing -= 1

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

        # multiActs for action pool for multiaction mutation
        if self.multiAction:
            multiActs = []
            for learner in oLearners:
                if learner.isActionAtomic():
                    multiActs.append(list(learner.action))
        else:
            multiActs = None

        while (len(self.teams) < self.teamPopSize or
                self.countRootTeams() < self.rTeamPopSize):

            # get parent root team, and child to be based on that
            parent = random.choice(self.rootTeams)
            child = Team()

            # child starts just like parent
            for learner in parent.learners:
                child.addLearner(learner)

            if self.uniqueProgThresh > 0:
                inputs, outputs = self.getLearnersInsOuts(oLearners)
            else:
                inputs = None
                outputs = None
            # then mutates
            child.mutate(self.pDelLrn, self.pAddLrn, self.pMutLrn, oLearners,
                        self.pMutProg, self.pMutAct, self.pActAtom,
                        self.actions, oTeams,
                        self.pDelInst, self.pAddInst, self.pSwpInst, self.pMutInst,
                        multiActs, self.pSwapMultiAct, self.pChangeMultiAct
                        self.uniqueProgThresh, inputs=inputs, outputs=outputs, update=True)

            self.teams.append(child)
            self.rootTeams.append(child)

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
