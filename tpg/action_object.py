from tpg.program import Program
import numpy as np
import random
from tpg.utils import flip

"""
Action  Object has a program to produce a value for the action, program doesn't
run if just a discrete action code.
"""
class ActionObject:

    def __init__(self, actionObj=None, program=None, actionCode=None,
            actionLength=0, teamAction=None, maxProgramLength=128, nRegisters=8):
        if actionObj is not None:
            # clone the other action object
            self.actionCode = actionObj.actionCode
            self.actionLength = actionObj.actionLength
            self.teamAction = actionObj.teamAction
            self.program = Program(instructions=actionObj.program.instructions)
        else:
            # no cloning
            self.actionCode = actionCode
            self.actionLength = actionLength
            self.teamAction = teamAction

            if program is None:
                # create new program
                self.program = Program(maxProgramLength=maxProgramLength)
            else:
                # copy program
                self.program = Program(instructions=program.instructions)

        # increase references to team
        if self.teamAction is not None:
            self.teamAction.numLearnersReferencing += 1

        self.registers = np.zeros(nRegisters)

    """
    Returns the action code, and if applicable corresponding real action(s).
    """
    def getAction(self, state, memMatrix, visited):
        if self.teamAction is not None:
            # action from team
            return self.teamAction.act(state, memMatrix, visited)
        else:
            # atomic action
            if self.actionLength == 0:
                return self.actionCode, None
            else:
                return self.actionCode, self.getRealAction(state, memMatrix)

    """
    Get the real valued portion of the action from the registers after program runs.
    """
    def getRealAction(self, state, memMatrix):
        Program.execute(state, self.registers,
                        self.program.instructions[:,0], self.program.instructions[:,1],
                        self.program.instructions[:,2], self.program.instructions[:,3],
                        memMatrix, memMatrix.shape[0], memMatrix.shape[1])

        return self.registers[:self.actionLength]

    """
    Returns true if the action is atomic, otherwise the action is a team.
    """
    def isAtomic(self):
        return self.teamAction is None

    """
    Either swap the action, or modify the program, depending on a flag.
    """
    def mutate(self, pMutProg, pDelInst, pAddInst, pSwpInst, pMutInst, uniqueProgThresh,
            inputs, outputs, pActAtom, parentTeam, actionCodes, actionLengths, teams, progMutFlag):
        if progMutFlag and self.actionLength > 0:
            # mutate program
            self.program.mutate(pMutProg, pDelInst, pAddInst, pSwpInst, pMutInst,
                len(self.registers), uniqueProgThresh, inputs=inputs, outputs=outputs)
        else:
            # dereference if old action is team
            if self.teamAction is not None:
                self.teamAction.numLearnersReferencing -= 1
                self.teamAction = None

            # mutate action
            if flip(pActAtom):
                # atomic
                self.actionCode = random.choice(actionCodes)
                self.actionLength = actionLengths[self.actionCode]
            else:
                # team action
                self.teamAction = random.choice([t for t in teams
                        if t is not self.teamAction and t is not parentTeam])
                self.teamAction.numLearnersReferencing += 1
