from tpg.configuration.conf_program import ConfProgram
from tpg.configuration.conf_learner import ConfLearner

from collections import namedtuple
import numpy as np

"""
Contains the ability to swap out different functions and add arbitrary variables
to different classes willy nilly to support whatever functionality is desired.
Such as Memory or real actions. Default configuration is no memory and discrete
actions.
"""

def configure(trainer, Trainer, Agent, Team, Learner, ActionObject, Program,
        doMemory, doReal):

    # make keys global to be accessed by other modele to create namedtuple
    global mutateParamKeys
    global actVarKeys

    # keys and values used in key value pairs for suplementary function args
    # for mutation and creation
    mutateParamKeys = ["pLrnDel", "pLrnAdd", "pLrnMut",
        "pProgMut", "pActMut", "pActAtom", "pInstDel", "pInstAdd", "pInstSwp", "pInstMut",
        "actionCodes", "nOperations", "nDestinations", "inputSize"]
    mutateParamVals = [trainer.pLrnDel, trainer.pLrnAdd, trainer.pLrnMut,
        trainer.pProgMut, trainer.pActMut, trainer.pActAtom, trainer.pInstDel, trainer.pInstAdd, trainer.pInstSwp, trainer.pInstMut,
        trainer.actionCodes, trainer.nOperations, trainer.nRegisters, trainer.inputSize]

    # additional stuff for act, like memory matrix possible
    actVarKeys = []
    actVarVals = []

    # configure stuff for using the memory module
    if doMemory:
        configureMemory(trainer, Learner, Program, trainer.memMatrixShape, actVarKeys, actVarVals)

    # configure stuff for using real valued actions
    if doReal:
        configureRealAction(trainer, mutateParamKeys, mutateParamVals)

    # save values to trainer so it can crete the extra parameters
    trainer.mutateParamVals = mutateParamVals
    trainer.actVarVals = actVarVals

    import tpg.configuration.extra_params

def configureMemory(trainer, Learner, Program, memMatrixShape, actVarKeys, actVarVals):
    # change functions as needed
    Program.execute = ConfProgram.execute_mem
    Learner.bid = ConfLearner.bid_mem

    # change other needed params
    trainer.nOperations = 7

    # trainer needs to have memory
    trainer.memMatrix = np.zeros(shape=memMatrixShape)
    # agents need access to memory too, and to pass through act
    actVarKeys += ["memMatrix"]
    actVarVals += [trainer.memMatrix]

def configureRealAction(trainer, mutateParamKeys, mutateParamVals):

    # mutateParams needs to have lengths of actions
    mutateParamKeys += ["actionLengths"]
    mutateParamVals += [trainer.actionLengths]
