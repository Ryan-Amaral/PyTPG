from tpg.configuration.conf_agent import ConfAgent
from tpg.configuration.conf_team import ConfTeam
from tpg.configuration.conf_learner import ConfLearner
from tpg.configuration.conf_action_object import ConfActionObject
from tpg.configuration.conf_program import ConfProgram

import numpy as np

"""
Contains the ability to swap out different functions and add arbitrary variables
to different classes willy nilly to support whatever functionality is desired.
Such as Memory or real actions. Default configuration is no memory and discrete
actions.
"""

def configure(trainer, Trainer, Agent, Team, Learner, ActionObject, Program,
        doMemory, memType, doReal, operationSet, traversal):

    # keys and values used in key value pairs for suplementary function args
    # for mutation and creation
    mutateParamKeys = ["generation", "pLrnDel", "pLrnAdd", "pLrnMut",
        "pProgMut", "pActMut", "pActAtom", "pInstDel", "pInstAdd", "pInstSwp", "pInstMut",
        "actionCodes", "nDestinations", "inputSize", "initMaxProgSize",
        "rampantGen", "rampantMin", "rampantMax", "idCountTeam", "idCountLearner", "idCountProgram"]
    mutateParamVals = [trainer.generation, trainer.pLrnDel, trainer.pLrnAdd, trainer.pLrnMut,
        trainer.pProgMut, trainer.pActMut, trainer.pActAtom, trainer.pInstDel, trainer.pInstAdd, trainer.pInstSwp, trainer.pInstMut,
        trainer.actionCodes, trainer.nRegisters, trainer.inputSize, trainer.initMaxProgSize,
        trainer.rampancy[0], trainer.rampancy[1], trainer.rampancy[2], 0, 0, 0]

    # additional stuff for act, like memory matrix possible
    actVarKeys = ["frameNum"]
    actVarVals = [0]

    # before doing any special configuration, set all methods to defaults
    configureDefaults(trainer, Trainer, Agent, Team, Learner, ActionObject, Program)

    # configure Program execution stuff, affected by memory and operations set
    configureProgram(trainer, Learner, Program, actVarKeys, actVarVals,
            mutateParamKeys, mutateParamVals, doMemory, memType, operationSet)

    # configure stuff for using real valued actions
    if doReal:
        configureRealAction(trainer, ActionObject, mutateParamKeys, mutateParamVals,
                            doMemory)

    # do learner traversal
    if traversal == "learner":
        configureLearnerTraversal(Agent, Team, actVarKeys, actVarVals)

    trainer.mutateParams = dict(zip(mutateParamKeys, mutateParamVals))
    trainer.actVars = dict(zip(actVarKeys, actVarVals))

"""
For each class in TPG, sets the functions to their defaults.
"""
def configureDefaults(trainer, Trainer, Agent, Team, Learner, ActionObject, Program):
    # set trainer functions
    # TODO: add learner configurable

    # set agent functions
    Agent.__init__ = ConfAgent.init_def
    Agent.act = ConfAgent.act_def
    Agent.reward = ConfAgent.reward_def
    Agent.taskDone = ConfAgent.taskDone_def
    Agent.saveToFile = ConfAgent.saveToFile_def

    # set team functions
    Team.__init__ = ConfTeam.init_def
    Team.act = ConfTeam.act_def
    Team.addLearner = ConfTeam.addLearner_def
    Team.removeLearner = ConfTeam.removeLearner_def
    Team.removeLearners = ConfTeam.removeLearners_def
    Team.numAtomicActions = ConfTeam.numAtomicActions_def
    Team.mutate = ConfTeam.mutate_def

    # set learner functions
    Learner.__init__ = ConfLearner.init_def
    Learner.bid = ConfLearner.bid_def
    Learner.getAction = ConfLearner.getAction_def
    Learner.getActionTeam = ConfLearner.getActionTeam_def
    Learner.isActionAtomic = ConfLearner.isActionAtomic_def
    Learner.mutate = ConfLearner.mutate_def

    # set action object functions
    ActionObject.__init__ = ConfActionObject.init_def
    ActionObject.getAction = ConfActionObject.getAction_def
    ActionObject.isAtomic = ConfActionObject.isAtomic_def
    ActionObject.mutate = ConfActionObject.mutate_def

    # set program functions
    Program.__init__ = ConfProgram.init_def
    Program.execute = ConfProgram.execute_def
    Program.mutate = ConfProgram.mutate_def
    #No longer need this after refactorAndTest merge
    #Program.mutateInstructions = ConfProgram.mutateInstructions_def

"""
Decides the operations and functions to be used in program execution.
"""
def configureProgram(trainer, Learner, Program, actVarKeys, actVarVals,
        mutateParamKeys, mutateParamVals, doMemory, memType, operationSet):
    # change functions as needed
    if doMemory:
        # default (reduced) or full operation set
        if operationSet == "def":
            Program.execute = ConfProgram.execute_mem
            trainer.nOperations = 7
            trainer.operations = ["ADD", "SUB", "MULT", "DIV", "NEG", "MEM_READ", "MEM_WRITE"]
        elif operationSet == "full":
            Program.execute = ConfProgram.execute_mem_full
            trainer.nOperations = 10
            trainer.operations = ["ADD", "SUB", "MULT", "DIV", "NEG", "COS", "LOG", "EXP", "MEM_READ", "MEM_WRITE"]

        # select appropriate memory write function
        if memType == "cauchy1":
            Program.memWriteProbFunc = ConfProgram.memWriteProb_cauchy1
        elif memType == "cauchyHalf":
            Program.memWriteProbFunc = ConfProgram.memWriteProb_cauchyHalf
        else:
            Program.memWriteProbFunc = ConfProgram.memWriteProb_def

        # change bid function to accomodate additional parameters needed for memory
        Learner.bid = ConfLearner.bid_mem

        # trainer needs to have memory
        trainer.memMatrix = np.zeros(shape=trainer.memMatrixShape)
        # agents need access to memory too, and to pass through act
        actVarKeys += ["memMatrix"]
        actVarVals += [trainer.memMatrix]

    else:
        # default (reduced) or full operation set
        if operationSet == "def":
            Program.execute = ConfProgram.execute_def
            trainer.nOperations = 5
            trainer.operations = ["ADD", "SUB", "MULT", "DIV", "NEG"]
        elif operationSet == "full":
            Program.execute = ConfProgram.execute_full
            trainer.nOperations = 8
            trainer.operations = ["ADD", "SUB", "MULT", "DIV", "NEG", "COS", "LOG", "EXP"]

        Learner.bid = ConfLearner.bid_def

    mutateParamKeys += ["nOperations"]
    mutateParamVals += [trainer.nOperations]

"""
Make the appropriate changes needed to be able to use real actions.
"""
def configureRealAction(trainer, ActionObject, mutateParamKeys, mutateParamVals, doMemory):
    # change functions as needed
    ActionObject.__init__ = ConfActionObject.init_real
    ActionObject.getAction = ConfActionObject.getAction_real
    if doMemory:
        ActionObject.getRealAction = ConfActionObject.getRealAction_real_mem
    else:
        ActionObject.getRealAction = ConfActionObject.getRealAction_real
    ActionObject.mutate = ConfActionObject.mutate_real

    # mutateParams needs to have lengths of actions
    mutateParamKeys += ["actionLengths"]
    mutateParamVals += [trainer.actionLengths]

"""
Switch to learner traversal.
"""
def configureLearnerTraversal(Agent, Team, actVarKeys, actVarVals):
    Team.act = ConfTeam.act_learnerTrav
