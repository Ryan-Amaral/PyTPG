from collections import namedtuple

"""
Contains the ability to swap out different functions and add arbitrary variables
to different classes willy nilly to support whatever functionality is desired.
Such as Memory or real actions. Default configuration is no memory and discrete
actions.
"""

def configure(trainer, Trainer, Agent, Team, Learner, ActionObject, Program,
        doMemory, memType, doReal):



    if doMemory:
        trainer.memoryMatrix = [1,2,3,4,5]
        actVarKeys = ["memoryMatrix"]
        trainer.actVarVals = [trainer.memoryMatrix]

        global ActVars
        ActVars = namedtuple("ActVars", " ".join(actVarKeys))

"""
Struct to hold variables used in action selection, stored in Agent instances.
"""
ActVars = namedtuple("ActVars", "")
