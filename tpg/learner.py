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

        if not self.isActionAtomic():
            self.action.numLearnersReferencing += 1

        self.numTeamsReferencing = 0 # amount of teams with references to this

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
    Mutates either the program or the action or both.
    """
    def mutate(self, pMutProg, pMutAct, pActAtom, atomics, parentTeam, allTeams,
                pDelInst, pAddInst, pSwpInst, pMutInst,
                inputs=None, outputs=None, update=True):

        changed = False
        while not changed:
            # mutate the program
            if flip(pMutProg):
                changed = True
                self.program.mutate(pDelInst, pAddInst, pSwpInst, pMutInst,
                                       inputs=inputs, outputs=outputs, update=update)

            # mutate the action
            if flip(pMutAct):
                changed = True
                self.mutateAction(pActAtom, atomics, allTeams, parentTeam)

    """
    Changes the action, into an atomic or team.
    """
    def mutateAction(self, pActAtom, atomics, allTeams, parentTeam):
        if not self.isActionAtomic(): # dereference old team action
            self.action.numLearnersReferencing -= 1

        if flip(pActAtom): # atomic action
            actions = [a for a in atomics if a is not self.action]
        else: # Team action
            actions = [t for t in allTeams
                    if t is not self.action and t is not parentTeam]
        self.action = random.choice(actions)

        if not self.isActionAtomic(): # add reference for new team action
            self.action.numLearnersReferencing += 1
