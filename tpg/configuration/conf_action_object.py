from tpg.program import Program
import numpy as np
import random
from tpg.utils import flip

"""
Action  Object has a program to produce a value for the action, program doesn't
run if just a discrete action code.
"""
class ConfActionObject:

    def init_def(self, actionObj=None, actionIndex=None, teamAction=None,
            initParams=None):
            
        if actionObj is not None:
            # clone the other action object
            self.actionCode = actionObj.actionCode
            self.teamAction = actionObj.teamAction
        else:
            # no cloning
            self.actionCode = initParams["actionCodes"][actionIndex]
            self.teamAction = teamAction

        # increase references to team
        if self.teamAction is not None:
            self.teamAction.numLearnersReferencing += 1

    def init_real(self, actionObj=None, program=None, actionIndex=None, teamAction=None,
            initParams=None):

        if actionObj is not None:
            # clone the other action object
            self.actionCode = actionObj.actionCode
            self.actionLength = actionObj.actionLength
            self.teamAction = actionObj.teamAction
            self.program = Program(instructions=actionObj.program.instructions,
                                    initParams=initParams)
        else:
            # no cloning
            self.actionCode = initParams["actionCodes"][actionIndex]
            self.actionLength = initParams["actionLengths"][actionIndex]
            self.teamAction = teamAction

            if program is None:
                # create new program
                self.program = Program(maxProgramLength=initParams["initMaxProgSize"])
            else:
                # copy program
                self.program = Program(instructions=program.instructions)

        # increase references to team
        if self.teamAction is not None:
            self.teamAction.numLearnersReferencing += 1

        self.registers = np.zeros(initParams["nDestinations"])

    """
    Returns the action code, and if applicable corresponding real action.
    """
    def getAction_def(self, state, visited, actVars=None):
        if self.teamAction is not None:
            # action from team
            return self.teamAction.act(state, visited, actVars=actVars)
        else:
            # atomic action
            return self.actionCode

    """
    Returns the action code, and if applicable corresponding real action(s).
    """
    def getAction_real(self, state, visited, actVars=None):
        if self.teamAction is not None:
            # action from team
            return self.teamAction.act(state, visited, actVars=actVars)
        else:
            # atomic action
            if self.actionLength == 0:
                return self.actionCode, None
            else:
                return self.actionCode, self.getRealAction(state, actVars=actVars)

    """
    Gets the real action from a register.
    """
    def getRealAction_real(self, state, actVars=None):
        Program.execute(state, self.registers,
                        self.program.instructions[:,0], self.program.instructions[:,1],
                        self.program.instructions[:,2], self.program.instructions[:,3])

        return self.registers[:self.actionLength]

    """
    Gets the real action from a register. With memory.
    """
    def getRealAction_real_mem(self, state, actVars=None):
        Program.execute(state, self.registers,
                        self.program.instructions[:,0], self.program.instructions[:,1],
                        self.program.instructions[:,2], self.program.instructions[:,3],
                        actVars["memMatrix"], actVars["memMatrix"].shape[0], actVars["memMatrix"].shape[1])

        return self.registers[:self.actionLength]

    """
    Returns true if the action is atomic, otherwise the action is a team.
    """
    def isAtomic_def(self):
        return self.teamAction is None

    """
    Change action to team or atomic action.
    """
    def mutate_def(self, mutateParams, parentTeam, teams, pActAtom):
        # dereference if old action is team
        if self.teamAction is not None:
            self.teamAction.numLearnersReferencing -= 1

        # mutate action
        if flip(pActAtom):
            # atomic
            self.actionCode = random.choice(mutateParams["actionCodes"])
            self.teamAction = None
        else:
            # team action
            self.teamAction = random.choice([t for t in teams
                    if t is not self.teamAction and t is not parentTeam])
            self.teamAction.numLearnersReferencing += 1

    """
    Change action to team or atomic action.
    """
    def mutate_real(self, mutateParams, parentTeam, teams, pActAtom):
        if self.actionLength > 0 and flip(0.5):
            # mutate program
            self.program.mutate(mutateParams)
        else:
            # dereference if old action is team
            if self.teamAction is not None:
                self.teamAction.numLearnersReferencing -= 1

            # mutate action
            if flip(mutateParams["pActAtom"]):
                # atomic
                self.actionCode = random.choice(mutateParams["actionCodes"])
                self.actionLength = mutateParams["actionLengths"][self.actionCode]
                self.teamAction = None
            else:
                # team action
                self.teamAction = random.choice([t for t in teams
                        if t is not self.teamAction and t is not parentTeam])
                self.teamAction.numLearnersReferencing += 1
