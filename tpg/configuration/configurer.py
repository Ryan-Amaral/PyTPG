from tpg.configuration.conf_learner import ConfLearner
from tpg.configuration.conf_action_object import ConfActionObject
from tpg.configuration.conf_program import ConfProgram

from collections import namedtuple
import numpy as np

"""
Contains the ability to swap out different functions and add arbitrary variables
to different classes willy nilly to support whatever functionality is desired.
Such as Memory or real actions. Default configuration is no memory and discrete
actions.
"""

def configure(trainer, Trainer, Agent, Team, Learner, ActionObject, Program,
        doMemory, memType, doReal):

    # make keys global to be accessed by other modele to create namedtuple
    global mutateParamKeys
    global actVarKeys

    # keys and values used in key value pairs for suplementary function args
    # for mutation and creation
    mutateParamKeys = ["generation", "pLrnDel", "pLrnAdd", "pLrnMut",
        "pProgMut", "pActMut", "pActAtom", "pInstDel", "pInstAdd", "pInstSwp", "pInstMut",
        "actionCodes", "nOperations", "nDestinations", "inputSize", "initMaxProgSize",
        "rampantGen", "rampantMin", "rampantMax"]
    mutateParamVals = [trainer.generation, trainer.pLrnDel, trainer.pLrnAdd, trainer.pLrnMut,
        trainer.pProgMut, trainer.pActMut, trainer.pActAtom, trainer.pInstDel, trainer.pInstAdd, trainer.pInstSwp, trainer.pInstMut,
        trainer.actionCodes, trainer.nOperations, trainer.nRegisters, trainer.inputSize, trainer.initMaxProgSize,
        trainer.rampancy[0], trainer.rampancy[1], trainer.rampancy[2]]

    # additional stuff for act, like memory matrix possible
    actVarKeys = []
    actVarVals = []

    # configure stuff for using the memory module
    if doMemory:
        configureMemory(trainer, Learner, Program, actVarKeys, actVarVals, memType)

    # configure stuff for using real valued actions
    if doReal:
        configureRealAction(trainer, ActionObject, mutateParamKeys, mutateParamVals,
                            doMemory)

    # save values to trainer so it can crete the extra parameters
    trainer.mutateParamVals = mutateParamVals
    trainer.actVarVals = actVarVals

    import tpg.configuration.extra_params

def configureMemory(trainer, Learner, Program, actVarKeys, actVarVals, memType):
    # change functions as needed
    Program.execute = ConfProgram.execute_mem
    if memType == "cauchy1":
        Program.memWriteProbFunc = ConfProgram.memWriteProb_cauchy1
    elif memType == "cauchyHalf":
        Program.memWriteProbFunc = ConfProgram.memWriteProb_cauchyHalf
    else:
        Program.memWriteProbFunc = ConfProgram.memWriteProb_def
    Learner.bid = ConfLearner.bid_mem

    # change other needed params
    trainer.nOperations = 7

    # trainer needs to have memory
    trainer.memMatrix = np.zeros(shape=trainer.memMatrixShape)
    # agents need access to memory too, and to pass through act
    actVarKeys += ["memMatrix"]
    actVarVals += [trainer.memMatrix]

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
