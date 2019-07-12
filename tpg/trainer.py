from tpg.program import Program
from tpg.learner import Learner
from tpg.team import Team
from tpg.agent import Agent
import random

"""
Functionality for actually growing TPG and evolving it to be functional.
"""
class Trainer:

    """
    Create a trainer to store the various evolutionary parameters.
    """
    def __init__(self, actions, teamPopSize=360, rTeamPopSize=360, gap=0.5,
        initMaxTeamSize=5, initMaxProgSize=128, registerSize=8,
        pDelLrn=0.7, pAddLrn=0.7, pMutLrn=0.3, pMutProg=0.66, pMutAct=0.33,
        pActAtom=0.5, pDelInst=0.5, pAddInst=0.5, pSwpInst=1.0, pMutInst=1.0):

        # store all necessary params
        self.actions = actions

        self.teamPopSize = teamPopSize
        self.rTeamPopSize = rTeamPopSize
        self.gap = gap

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

        self.generation = 0

        self.initializePopulations(initMaxTeamSize, initMaxProgSize, registerSize)

    """
    Initializes a popoulation of teams and learners generated randomly with only
    atomic actions.
    """
    def initializePopulations(self, initMaxTeamSize, initMaxProgSize, registerSize):
        for i in range(self.teamPopSize):
            # create 2 unique actions and learners
            a1,a2 = random.sample(self.actions, 2)
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
                learner = Learner(program=Program(maxProgramLength=initMaxProgSize),
                                  action=random.choice(self.actions),
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
        for rt in self.rootTeams:
            rt.fitness = rt.outcomes[task]

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

        for team in deleteTeams:
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
                self.countRootTeams() < self.rTeamPopSize):

            # get parent root team, and child to be based on that
            parent = random.choice(self.rootTeams)
            child = Team()

            # child starts just like parent
            for learner in parent.learners:
                child.addLearner(learner)
            # then mutates
            child.mutate(self.pDelLrn, self.pAddLrn, self.pMutLrn, oLearners,
                        self.pMutProg, self.pMutAct, self.pActAtom,
                        self.actions, oTeams,
                        self.pDelInst, self.pAddInst, self.pSwpInst, self.pMutInst,
                        inputs=None, outputs=None, update=True)

            self.teams.append(child)
            self.rootTeams.append(child)

    def nextEpoch(self):
        # delete now unused learners
        for learner in list(self.learners):
            if learner.numTeamsReferencing == 0:
                self.learners.remove(learner)
                # dereference if action is team
                if not learner.isActionAtomic():
                    learner.action.numLearnersReferencing -= 1

        # add in newly added learners, and decide root teams
        self.rootTeams = []
        for team in self.teams:
            # add any new learners to the population
            for learner in team.learners:
                if learner not in self.learners:
                    self.learners.append(learner)

            # maybe make root team
            if team.numLearnersReferencing == 0:
                self.rootTeams.append(team)

    def countRootTeams(self):
        numRTeams = 0
        for team in self.teams:
            if team.numLearnersReferencing == 0:
                numRTeams += 1

        return numRTeams
