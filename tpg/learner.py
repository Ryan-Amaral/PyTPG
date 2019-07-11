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
            self.program = learner.program
            self.action = learner.action
            self.registers = np.zeros(len(learner.registers), dtype=float)
        elif program is not None and action is not None:
            self.program = program
            self.action = action
            self.registers = np.zeros(numRegisters, dtype=float)

        self.id = Learner.idCount

    """
    Get the bid value, highest gets its action selected.
    """
    def bid(self, state):
        Program.execute(state, self.registers,
                        self.program.modes, self.program.operations,
                        self.program.destinations, self.program.sources)

        return self.registers[0]

    """
    Returns the action of this learner, either atomic, or requests the action
    from the action team.
    """
    def getAction(self, state, visited):
        if self.isActionAtomic():
            return self.action
        else:
            return self.action.act(state, visited)


    """
    Returns true if the action is atomic, otherwise the action is a team.
    """
    def isActionAtomic(self):
        return isinstance(self.action, int)

    """
    Mutates either the program or the action. Returns the new mutated Learner,
    or original if no mutation.
    """
    def mutate(self, pMutProg, pMutAct, pActAtom, atomics, parentTeam, allTeams,
                pInstDel, pInstAdd, pInstSwp, pInstMut,
                inputs=None, outputs=None, update=True):

        learner = self # fallback if no mutation

        # mutate the program
        if flip(pMutProg):
            # clone learner and program before mutate
            learner = Learner(program=Program(instructions=self.program.instructions),
                              action = self.action, numRegisters=len(self.registers))
            learner.program.mutate(pInstDel, pInstAdd, pInstSwp, pInstMut,
                                   inputs=inputs, outputs=outputs, update=update)

        # mutate the action
        if flip(pMutAct):
            # clone learner before mutate
            if learner == self:
                learner = Learner(self)

            if flip(pActAtom): # atomic action
                actions = [a for a in atomics if a is not learner.action]
            else: # Team action
                actions = [t for t in allTeams
                        if t is not learner.action and t is not parentTeam]
            learner.action = random.choice(actions)

        return learner
