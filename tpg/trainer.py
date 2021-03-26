from numba.types.scalars import Boolean
from tpg.action_object import ActionObject
from tpg.program import Program
from tpg.learner import Learner
from tpg.team import Team
from tpg.agent import Agent
from tpg.configuration import configurer
import random
import numpy as np
import pickle
from collections import namedtuple
import json

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

    memType: Type of memory distribution to use for writing. None or "None" if not
    using memory, otherwise "default", "cauchy1", or "cauchyHalf".

    rampancy: How often to do rampant mutation: (a, b) or (a, b, c). a is to do it every
    a'th generation (keep as zero to not do it), b and c are the range for how
    many times to repeat rampancy (b inclusive, c exclusive/not required).

    operationSet: "def" for ["ADD", "SUB", "MULT", "DIV", "NEG"], or "full" for
    ["ADD", "SUB", "MULT", "DIV", "NEG", "COS", "LOG", "EXP"]. "MEM_READ" and
    "MEM_WRITE" may be added in if applicable. May change to just including the
    list of desired operations in the future.

    traversal: "team" to traverse for an action without repeating any team visits.
    "learner" is similar but with repeat visits to teams and no repeat visits to
    learners.

    prevPops: Either a list of the the root teams from a previous population, or
    a dicitonary with the keys being the environment and the values being a list
    of root teams trained on that environment.

    doMutate: Whether to continue mutating newly created root teams below the team
    level. If true only mutates teams by changing up the learners, but doesn't
    mutate the learners or
    """
    def __init__(self, actions, teamPopSize=360, rootBasedPop=True, gap=0.5,
        inputSize=33600, nRegisters=8, initMaxTeamSize=5, initMaxProgSize=128,
        pLrnDel=0.7, pLrnAdd=0.7, pLrnMut=0.3, pProgMut=0.66, pActMut=0.33,
        pActAtom=0.5, pInstDel=0.5, pInstAdd=0.5, pInstSwp=1.0, pInstMut=1.0,
        doElites=True, memType=None, memMatrixShape=(100,8), rampancy=(0,0,0),
        operationSet="def", traversal="team", prevPops=None, mutatePrevs=True,
        initMaxActProgSize=64, nActRegisters=4):

        '''
        Validate inputs
        '''
        int_greater_than_zero = {
            "teamPopSize": teamPopSize,
            "inputSize": inputSize,
            "nRegisters": nRegisters,
            "initMaxTeamSize": initMaxTeamSize,
            "initMaxProgSize": initMaxProgSize,
        }

        for entry in int_greater_than_zero.items():
            self.must_be_integer_greater_than_zero(entry[0], entry[1])

        # Validate doElites
        if type(doElites) is not bool:
            raise Exception("Invalid doElites")

        # Validate rootBasedPop
        if type(rootBasedPop) is not bool:
            raise Exception("Invalid rootBasedPop")

        # Validate Traversal
        valid_traversals = ["team", "learner"]
        if traversal not in valid_traversals:
            raise Exception("Invalid traversal")
        
        '''
        Gap must be a float greater than 0 but less than or equal to 1
        '''
        if type(gap) is not float or gap == 0.0 or gap > 1.0:
            raise Exception("gap must be a float greater than 0 but less than or equal to 1")


        # Validate Operation Set
        valid_operation_sets = ["def", "full", "robo"]
        if operationSet not in valid_operation_sets:
            raise Exception("Invalid operation set")

        # Validate Probability parameters
        probabilities = {
            "pLrnDel": pLrnDel,
            "pLrnAdd": pLrnAdd,
            "pLrnMut": pLrnMut,
            "pProgMut": pProgMut,
            "pActMut": pActMut,
            "pActAtom": pActAtom,
            "pInstDel": pInstDel,
            "pInstAdd": pInstAdd,
            "pInstSwp": pInstSwp,
            "pInstMut": pInstMut
        }


        for entry in probabilities.items():
            self.validate_probability(entry[0],entry[1])

        # Validate rampancy
        if (
            len(rampancy) != 3 or
            rampancy[0] < 0 or
            rampancy[2] < rampancy[1] or 
            rampancy[1] < 0 or
            rampancy[2] < 0
            ):
            raise Exception("Invalid rampancy parameter!", rampancy)

        # store all necessary params

        # first store actions properly
        self.doReal = self.setUpActions(actions)

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

        # whether to keep elites
        self.doElites = doElites

        if memType == "None":
            self.memType = None
        self.memType = memType
        self.memMatrixShape = memMatrixShape

        self.rampancy = rampancy

        self.operationSet = operationSet

        self.traversal = traversal

        self.initMaxActProgSize = initMaxActProgSize
        # ensure nActRegisters is larger than the largest action length
        if self.doReal:
            nActRegisters = max(max(self.actionLengths), nActRegisters)
        self.nActRegisters = nActRegisters

        # core components of TPG
        self.teams = []
        self.rootTeams = []
        self.learners = []
        self.elites = [] # save best at each task

        self.generation = 0 # track this

        # these are to be filled in by the configurer after
        self.mutateParams = {}
        self.actVars = {}
        self.nOperations = None
        self.functionsDict = {}

        # configure tpg functions and variable appropriately now
        configurer.configure(self, Trainer, Agent, Team, Learner, ActionObject, Program,
            memType is not None, memType, self.doReal, operationSet, traversal)

        #print(self.mutateParams)
        #print(self.functionsDict)
        #print(1/0)

        self.initializePopulations()

    '''
    Validation Method
    '''
    def must_be_integer_greater_than_zero(self, name, value):
        if type(value) is not int or value <= 0:
            raise Exception(name + " must be integer greater than zero. Got " + str(value), name, value)

    '''
    Validation Method
    '''
    def validate_probability(self, name,  value):
        if type(value) is not float or value > 1.0 or value < 0.0:
            raise Exception(name + " is a probability, it must not be greater than 1.0 or less than 0.0", name, value)

    """
    Sets up the actions properly, splitting action codes, and if needed, action
    lengths. Returns whether doing real actions.
    """
    def setUpActions(self, actions):
        if isinstance(actions, int):
            # all discrete actions
            self.actionCodes = range(actions)
            doReal = False
        else: # list of lengths of each action
            # some may be real actions
            self.actionCodes = range(len(actions))
            self.actionLengths = list(actions)
            doReal = True

        return doReal

    """
    Initializes a popoulation of teams and learners generated randomly with only
    atomic actions.
    """
    def initializePopulations(self):
        for i in range(self.teamPopSize):
            a1 = 0

            l1 = Learner(self.mutateParams,
                        program=Program(maxProgramLength=self.initMaxProgSize,
                                         nOperations=self.nOperations,
                                         nDestinations=self.nRegisters,
                                         inputSize=self.inputSize,
                                         initParams=self.mutateParams),
                        actionObj=ActionObject(action=a1, initParams=self.mutateParams),
                        numRegisters=self.nRegisters)

            # save learner population
            self.learners.append(l1)

            # create team and add initial learners
            team = Team(initParams=self.mutateParams)
            team.addLearner(l1)

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
            return [Agent(team, self.functionsDict, num=i, actVars=self.actVars)
                    for i,team in enumerate(rTeams)]
        else:
            # apply scores/fitness to root teams
            self.scoreIndividuals(sortTasks, multiTaskType=multiTaskType, doElites=False)
            # return teams sorted by fitness
            return [Agent(team, self.functionsDict, num=i, actVars=self.actVars)
                    for i,team in enumerate(sorted(rTeams,
                                    key=lambda tm: tm.fitness, reverse=True))]

    """ 
    Gets the single best team at the given task, regardless of if its root or not.
    """
    def getEliteAgent(self, task):
        
        teams = [t for t in self.teams if task in t.outcomes]

        return Agent(max([tm for tm in teams],
                        key=lambda t: t.outcomes[task]),
                     self.functionsDict, num=0, actVars=self.actVars)

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
        #self.validate_graph() # validate the tpg (for debug only)
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
    Select a portion of the root team population to keep according to gap size.
    """
    def select(self):
        rankedTeams = sorted(self.rootTeams, key=lambda rt: rt.fitness, reverse=True)
        numKeep = len(self.rootTeams) - int(len(self.rootTeams)*self.gap)
        deleteTeams = rankedTeams[numKeep:]

        #print("BEFORE SELECTION:")        

        pre_orphans = [learner for learner in self.learners if learner.numTeamsReferencing() == 0]

        #print("Number of orphans before selection: {}".format(len(pre_orphans)))

        orphan_teams = [team for team in self.teams if len(team.inLearners) == 0 and team not in self.rootTeams]
        #print("Number of orphan teams before selection: {}".format(len(orphan_teams)))

        #print("Learners:")
        #for cursor in self.learners:
        #   print("Learner {} -> [{}]{} inTeams:".format( cursor.id, "Atomic" if cursor.isActionAtomic() else "Team", cursor.actionObj.actionCode if cursor.isActionAtomic() else cursor.actionObj.teamAction.id))
        #    for t_id in cursor.inTeams:
        #        print("\t{}".format(t_id ))

        #for cursor in self.teams:
        #    print("Team: {} inLearners:".format(cursor.id))
        #    for l_id in cursor.inLearners:
        #        print("\t{}".format(l_id))

        #print("-----------------------------------------------------")  

        # delete the team unless it is an elite (best at some task at-least)
        # don't delete elites because they may not be root - TODO: elaborate
        for team in [t for t in deleteTeams if t not in self.elites]:

    
            # remove learners from team and delete team from populations
            team.removeLearners()
            self.teams.remove(team)
            self.rootTeams.remove(team)

        #print("AFTER SELECTION:")
        # Find all learners that have no teams pointing to them
        orphans = [learner for learner in self.learners if learner.numTeamsReferencing() == 0]
        #print("Number of orphans after selection: {}".format(len(orphans)))

        #print("Orphans:")
        #for cursor in orphans:
        #    print("\t{}".format(cursor.id))

        #print("Learners:")
        #for cursor in self.learners:
        #    print("Learner {} -> [{}]{} inTeams:".format( cursor.id, "Atomic" if cursor.isActionAtomic() else "Team", cursor.actionObj.actionCode if cursor.isActionAtomic() else cursor.actionObj.teamAction.id))
        #    for t_id in cursor.inTeams:
        #        print("\t{}".format(t_id ))

        #for cursor in self.teams:
        #    print("Team: {} inLearners:".format(cursor.id))
        #    for l_id in cursor.inLearners:
        #        print("\t{}".format(l_id))

        #print("-----------------------------------------------------")  

        # These learners will be removed, but before we can do that, we should remove 
        # their ids from any team's inLearners that the orphans are pointing to.
        for cursor in orphans:
            if not cursor.isActionAtomic(): # If the orphan does NOT point to an atomic action
                # Get the team the orphan is pointing to and remove the orphan's id from the team's in learner list
                cursor.actionObj.teamAction.inLearners.remove(str(cursor.id))

        # Finaly, purge the orphans
        self.learners = [learner for learner in self.learners if learner.numTeamsReferencing() > 0]
                

    """
    Generates new rootTeams based on existing teams.
    """
    def generate(self):

        oLearners = list(self.learners)
        oTeams = list(self.teams)

        # update generation in mutateParams
        self.mutateParams["generation"] = self.generation

        # get all the current root teams to be parents
        while (len(self.teams) < self.teamPopSize or
                (self.rootBasedPop and self.countRootTeams() < self.teamPopSize)):
            # get parent root team, and child to be based on that
            parent = random.choice(self.rootTeams)
            child = Team(initParams=self.mutateParams)

            # child starts just like parent
            for learner in parent.learners:
                child.addLearner(learner)

            # then mutates
            child.mutate(self.mutateParams, oLearners, oTeams)

            self.teams.append(child)

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
                    print("Adding {} to trainer learners".format(learner.id))
                    self.learners.append(learner)

            # maybe make root team
            if team.numLearnersReferencing() == 0 or team in self.elites:
                self.rootTeams.append(team)

        self.generation += 1
    
    '''
    Go through all teams and learners and make sure their inTeams/inLearners correspond with 
    their team.learner/teamActions as expected.
    '''
    def validate_graph(self):
        print("Validating graph")

        print("Checking for broken learners")
        for cursor in self.learners:
            if cursor.isActionAtomic() and cursor.actionObj.actionCode == None:
                print("{} is an action atomic learner with no actionCode!".format(str(cursor.id)))
            if cursor.actionObj.teamAction == None and cursor.actionObj.actionCode == None:
                print("{} has no action!".format(str(cursor.id)))

        learner_map = {}
        for cursor in self.learners:
            if str(cursor.id) not in learner_map:
                learner_map[str(cursor.id)] = cursor.inTeams
            else:
                raise Exception("Duplicate learner id in trainer!")
        
        '''
        For every entry in the learner map check that the corresponding team has the learner 
        in its learners 
        '''
        for i,cursor in enumerate(learner_map.items()):
            for expected_team in cursor[1]:
                found_team = False
                for team in self.teams:
                    if str(team.id) == expected_team:
                        found_learner = 0
                        for learner in team.learners:
                            if str(learner.id) == cursor[0]:
                                found_learner += 1
                        if found_learner != 1:
                            print("found_learner = {} for learner {} in team {}".format(found_learner, cursor[0], str(team.id)))
                        found_team = True
                        break
                if found_team == False:
                    print("Could not find expected team {} in trainer".format(expected_team))
            print("learner {} inTeams valid [{}/{}]".format(cursor[0], i, len(learner_map.items())-1))

        '''
        Verify that for every inLearner in a team, the learner exists in the trainer, pointing to that team
        '''
        team_map = {}
        for cursor in self.teams:
            if str(cursor.id) not in team_map:
                team_map[str(cursor.id)] = cursor.inLearners
            else:
                raise Exception("Duplicate team id in trainer!")

        for i,cursor in enumerate(team_map.items()):
            for expected_learner in cursor[1]:
                found_learner = False
                points_to_team = False
                for learner in self.learners:
                    if str(learner.id) == expected_learner:
                        found_learner = True
                        if str(learner.actionObj.teamAction.id) == cursor[0]:
                            points_to_team = True
                            break
                if found_learner == False:
                    print("Could not find learner {} from team {} inLearners in trainer.".format(expected_learner, cursor[0]))
                if points_to_team == False:
                    print("Learner {} does not point to team {}".format(expected_learner, cursor[0]))
            print("team {} inLearners valid [{}/{}]".format(cursor[0], i, len(team_map.items())-1))
    """
    Get the number of root teams currently residing in the teams population.
    """
    def countRootTeams(self):
        numRTeams = 0
        for team in self.teams:
            if team.numLearnersReferencing() == 0:
                numRTeams += 1

        return numRTeams


    def get_graph(self):


        result = {
            "nodes":[],
            "links":[]
        }

        # First add action codes as nodes
        for actionCode in self.actionCodes:
            result["nodes"].append(
                {
                    "id": str(actionCode),   
                    "type": "action"
                }
            )
        
        # Then add teams as nodes
        for team in self.teams:
            result["nodes"].append(
                {
                    "id": str(team.id),
                    "type": "rootTeam" if team in self.rootTeams else "team"
                }
            )

        # Then add learners as nodes
        for learner in self.learners:
            result["nodes"].append(
                {
                    "id": str(learner.id),
                    "type": "learner"
                }
            )


        # Then add links from learners to teams
        for team in self.teams:
            for learner in team.inLearners:
                result["links"].append(
                    {
                        "source": learner,
                        "target": str(team.id)
                    }
                )
        
        # Then add links from teams to learners
        for learner in self.learners:
            for team in learner.inTeams:
                result["links"].append(
                    {
                        "source": team,
                        "target": str(learner.id)
                    }
                )
            
            # Also add links to action codes
            if learner.isActionAtomic():
                result["links"].append(
                    {
                        "source": str(learner.id),
                        "target": str(learner.actionObj.actionCode)
                    }
                )

        # with open("tpg_{}.json".format(self.generation), 'w') as out_file:
        #     json.dump(result, out_file)
        return result


    """
    Function to cleanup anything that may interfere with another trainer run in
    the same thread of execution. Currently just sets tpg module functions to defaults.
    """
    def cleanup(self):
        configurer.configureDefaults(self, Trainer, Agent, Team, Learner, ActionObject, Program)

    """
    Ensures proper functions are in place for all classes. Ran after loading from a file,
    and may need to be ran in other cases such as multiprocessing (though in out typical use
    that is done at the agent level).
    """
    def configFunctions(self):
        # first set up Agent functions
        Agent.configFunctions(self.functionsDict["Agent"])

        # set up Team functions
        Team.configFunctions(self.functionsDict["Team"])

        # set up Learner functions
        Learner.configFunctions(self.functionsDict["Learner"])

        # set up ActionObject functions
        ActionObject.configFunctions(self.functionsDict["ActionObject"])

        # set up Program functions
        Program.configFunctions(self.functionsDict["Program"])

    """
    Save the trainer to the file, saving any class values to the instance.
    """
    def saveToFile(self, fileName):
        pickle.dump(self, open(fileName, 'wb'))

"""
Load some trainer from the file, returning it and repopulate class values.
"""
def loadTrainer(fileName):
    trainer = pickle.load(open(fileName, 'rb'))
    trainer.configFunctions()
    return trainer

