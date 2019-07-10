from tpg.program import Program
import numpy as np

"""
A team has multiple learners, each learner has a program which is executed to
produce the bid value for this learner's action.
"""
class Learner:

    numRegisters = 8

    idCount = 0 # unique learner id

    """
    Create a new learner, either copied from the original or from a program or
    action. Either requires a learner, or a program/action pair.
    """
    def __init__(self, learner=None, program=None, action=None):
        if learner is not None:
            self.program = learner.program
            self.action = learner.action
        elif program is not None and action is not None:
            self.program = program
            self.action = action

        self.registers = np.zeros(Learner.numRegisters, dtype=float)

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
    Mutates either the program or the action.
    """
    def mutate(self):
        # if mutate program, must reinstance program
        pass
