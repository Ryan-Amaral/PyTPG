from tpg.program import Program
from tpg.action_object import ActionObject
import numpy as np
from tpg.utils import flip
import random

"""
A team has multiple learners, each learner has a program which is executed to
produce the bid value for this learner's action.
"""
class Learner:

    """
    Create a new learner, either copied from the original or from a program or
    action. Either requires a learner, or a program/action pair.
    """
    def __init__(self, initParams, learner=None, program=None, actionObj=None, numRegisters=8,
            nOperations=5, nDestinations=8, inputSize=30720):
        if learner is not None:
            self.program = Program(instructions=learner.program.instructions,
                nOperations=nOperations, nDestinations=nDestinations, inputSize=inputSize,
                initParams=initParams)
            self.actionObj = ActionObject(learner.actionObj, initParams=initParams)
            self.registers = np.zeros(len(learner.registers), dtype=float)
        elif program is not None and actionObj is not None:
            self.program = program
            self.actionObj = actionObj
            self.registers = np.zeros(numRegisters, dtype=float)

        self.states = []

        self.numTeamsReferencing = 0 # amount of teams with references to this

        self.id = initParams["idCountLearner"]
        initParams["idCountLearner"] += 1

        self.genCreate = initParams["generation"]

        self.frameNum = 0

    """
    Get the bid value, highest gets its action selected.
    """
    def bid(self, state, actVars=None):
        Program.execute(state, self.registers,
                        self.program.instructions[:,0], self.program.instructions[:,1],
                        self.program.instructions[:,2], self.program.instructions[:,3])

        return self.registers[0]

    """
    Returns the action of this learner, either atomic, or requests the action
    from the action team.
    """
    def getAction(self, state, visited, actVars=None):
        return self.actionObj.getAction(state, visited, actVars=actVars)

    """
    Gets the team that is the action of the learners action object.
    """
    def getActionTeam(self):
        return self.actionObj.teamAction

    """
    Returns true if the action is atomic, otherwise the action is a team.
    """
    def isActionAtomic(self):
        return self.actionObj.isAtomic()

    """
    Mutates either the program or the action or both.
    """
    def mutate(self, mutateParams, parentTeam, teams, pActAtom):

        changed = False
        while not changed:
            # mutate the program
            if flip(mutateParams["pProgMut"]):
                changed = True
                self.program.mutate(mutateParams)

            # mutate the action
            if flip(mutateParams["pActMut"]):
                changed = True
                self.actionObj.mutate(mutateParams, parentTeam, teams, pActAtom)
