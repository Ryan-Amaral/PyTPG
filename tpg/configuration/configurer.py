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
        doMemory, memType, memMatrixShape, doReal):

    # keys and values used in key value pairs for suplementary function args
    global MutateParams
    mutateParamKeys = []
    mutateParamVals = []
    global ActVars
    actVarKeys = []
    actVarVals = []

    # configure stuff for using the memory module
    if doMemory:
        # change functions as needed
        Program.execute = ConfProgram.execute_mem
        Learner.bid = ConfLearner.bid_mem

        # change other needed params
        trainer.nOperations = 7

        # trainer needs to have memory
        trainer.memMatrix = np.zeros(shape=memMatrixShape)
        # agents need access to memory too, and to pass through act
        actVarKeys += ["memMatrix"]
        trainer.actVarVals += [trainer.memMatrix]
        ActVars = namedtuple("ActVars", " ".join(actVarKeys))

    # configure stuff for using real valued actions
    if doReal:
        

"""
Struct to hold parameters used in mutation to not clutter function calls.
"""
MutateParams = namedtuple("MutateParams", """pLrnDel pLrnAdd pLrnMut
    pProgMut pActMut pActAtom pInstDel pInstAdd pInstSwp pInstMut
    actionCodes nOperations nDestinations inputSize"""
)

"""
Struct to hold variables used in action selection, stored in Agent instances.
"""
ActVars = namedtuple("ActVars", "")
