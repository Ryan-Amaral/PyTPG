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

    idCount = 0 # unique learner id

    """
    Create a new learner, either copied from the original or from a program or
    action. Either requires a learner, or a program/action pair.
    """
    def __init__(self, learner=None, program=None, actionObj=None, numRegisters=8):
        if learner is not None:
            self.program = Program(instructions=learner.program.instructions)
            self.actionObj = ActionObject(learner.actionObj)
            self.registers = np.zeros(len(learner.registers), dtype=float)
        elif program is not None and actionObj is not None:
            self.program = program
            self.actionObj = actionObj
            self.registers = np.zeros(numRegisters, dtype=float)

        if not self.isActionAtomic():
            self.action.numLearnersReferencing += 1

        self.states = []

        self.numTeamsReferencing = 0 # amount of teams with references to this

        self.id = Learner.idCount
        Learner.idCount += 1

    """
    Get the bid value, highest gets its action selected.
    """
    def bid(self, state):
        Program.execute(state, self.registers,
                        self.program.instructions[:,0], self.program.instructions[:,1],
                        self.program.instructions[:,2], self.program.instructions[:,3])

        return self.registers[0]

    """
    Returns the action of this learner, either atomic, or requests the action
    from the action team.
    """
    def getAction(self, state, visited):
        return self.actionObj.getAction(state, visited)

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
    def mutate(self, pProgMut, pActMut, pActAtom, atomics, parentTeam, allTeams,
                pInstDel, pInstAdd, pInstSwp, pInstMut):

        changed = False
        while not changed:
            # mutate the program
            if flip(pProgMut):
                changed = True
                self.program.mutate(pProgMut, pInstDel, pInstAdd, pInstSwp, pInstMut,
                    len(self.registers))

            # mutate the action
            if flip(pActMut):
                changed = True
                self.actionObj.mutate(pMutProg, pDelInst, pAddInst, pSwpInst, pMutInst,
                    uniqueProgThresh, inputs, outputs, pActAtom, parentTeam, actionCodes,
                    actionLengths, teams, progMutFlag)
