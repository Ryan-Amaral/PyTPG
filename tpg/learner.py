from tpg.program import Program
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
    def __init__(self, learner=None, program=None, action=None, numRegisters=8):
        if learner is not None:
            self.program = Program(instructions=learner.program.instructions)
            self.action = learner.action
            self.registers = np.zeros(len(learner.registers), dtype=float)
        elif program is not None and action is not None:
            self.program = program
            self.action = action
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
    def bid(self, state, memMatrix):
        Program.execute(state, self.registers,
                        self.program.instructions[:,0], self.program.instructions[:,1],
                        self.program.instructions[:,2], self.program.instructions[:,3],
                        memMatrix, memMatrix.shape[0], memMatrix.shape[1])

        return self.registers[0]

    """
    Returns the action of this learner, either atomic, or requests the action
    from the action team.
    """
    def getAction(self, state, memMatrix, visited):
        if self.isActionAtomic():
            return self.action
        else:
            return self.action.act(state, memMatrix, visited)


    """
    Returns true if the action is atomic, otherwise the action is a team.
    """
    def isActionAtomic(self):
        return isinstance(self.action, (int, list))

    """
    Mutates either the program or the action or both.
    """
    def mutate(self, pMutProg, pMutAct, pActAtom, atomics, parentTeam, allTeams,
                pDelInst, pAddInst, pSwpInst, pMutInst,
                multiActs, pSwapMultiAct, pChangeMultiAct,
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
                self.mutateAction(pActAtom, atomics, allTeams, parentTeam,
                                  multiActs, pSwapMultiAct, pChangeMultiAct)

    """
    Changes the action, into an atomic or team.
    """
    def mutateAction(self, pActAtom, atomics, allTeams, parentTeam,
                     multiActs, pSwapMultiAct, pChangeMultiAct):
        if not self.isActionAtomic(): # dereference old team action
            self.action.numLearnersReferencing -= 1

        if flip(pActAtom): # atomic action
            if multiActs is None:
                self.action = random.choice(
                                [a for a in atomics if a is not self.action])
            else:
                swap = flip(pSwapMultiAct)
                if swap or not self.isActionAtomic(): # totally swap action for another
                    self.action = list(random.choice(multiActs))

                # change some value in action
                if not swap or flip(pChangeMultiAct):
                    changed = False
                    while not changed or flip(pChangeMultiAct):
                        index = random.randint(0, len(self.action)-1)
                        self.action[index] += random.gauss(0, .15)
                        self.action = list(np.clip(self.action, 0, 1))
                        changed = True

        else: # Team action
            self.action = random.choice([t for t in allTeams
                    if t is not self.action and t is not parentTeam])

        if not self.isActionAtomic(): # add reference for new team action
            self.action.numLearnersReferencing += 1

    """
    Saves visited states for mutation uniqueness purposes.
    """
    def saveState(self, state, numStates=50):
        self.states.append(state)
        self.states = self.states[-numStates:]
