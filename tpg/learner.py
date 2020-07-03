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
    lastFrame = -1

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

        self.states = []

        self.numTeamsReferencing = 0 # amount of teams with references to this

        self.id = Learner.idCount
        Learner.idCount += 1
    
    '''
    Learner class string representation method. For use with str(..).
    '''
    def __str__(self):
        return "L" + str(self.id)
    
    '''
    Learner class object representation method. Typically used for 
    debugging. In this case, it simply returns the string representation.
    '''
    def __repr__(self):
        return self.__str__()
    
    '''
    Learner class equality method. Returns True if this == other.
    '''
    def __eq__(self, other):
        return self.id == other.id
    
    def __hash__(self):
        return self.id

    """
    Get the bid value, highest gets its action selected.
    """
    def bid(self, state, memMatrix, frameNumber):

        if self.lastFrame == -1 or self.lastFrame < frameNumber:
            Program.execute(state, self.registers,
                            self.program.instructions[:,0], self.program.instructions[:,1],
                            self.program.instructions[:,2], self.program.instructions[:,3],
                            memMatrix, memMatrix.shape[0], memMatrix.shape[1])
            return self.registers[0]
        else:
            self.lastFrame = frameNumber
            return self.registers[0]

    """
    Returns the action of this learner, either atomic, or requests the action
    from the action team.
    """
    def getAction(self, state, memMatrix, frameNumber, visited ):
        return self.actionObj.getAction(state, memMatrix, visited, frameNumber)


    """
    Returns true if the action is atomic, otherwise the action is a team.
    """
    def isActionAtomic(self):
        return self.actionObj.isAtomic()

    """
    Mutates either the program or the action or both.
    """
    def mutate(self, pMutProg, pMutAct, pActAtom, actionCodes, actionLengths,
            teams, parentTeam, progMutFlag, pDelInst, pAddInst, pSwpInst, pMutInst,
            uniqueProgThresh, inputs=None, outputs=None):

        changed = False
        while not changed:
            # mutate the program
            if flip(pMutProg):
                changed = True
                self.program.mutate(pMutProg, pDelInst, pAddInst, pSwpInst, pMutInst,
                    len(self.registers), uniqueProgThresh,
                    inputs=inputs, outputs=outputs)

            # mutate the action
            if flip(pMutAct):
                changed = True
                self.actionObj.mutate(pMutProg, pDelInst, pAddInst, pSwpInst, pMutInst,
                    uniqueProgThresh, inputs, outputs, pActAtom, parentTeam, actionCodes,
                    actionLengths, teams, progMutFlag)

    """
    Saves visited states for mutation uniqueness purposes.
    """
    def saveState(self, state, numStates=50):
        self.states.append(state)
        self.states = self.states[-numStates:]

if __name__ == "__main__":
    print("This is Learner!")