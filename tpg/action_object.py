import numpy as np
import random
from tpg.utils import flip

"""
Action  Object has a program to produce a value for the action, program doesn't
run if just a discrete action code.
"""
class ActionObject:

    def __init__(self, actionObj=None, actionIndex=None, teamAction=None,
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

    """
    Returns the action code, and if applicable corresponding real action(s).
    """
    def getAction(self, state, visited, actVars=None):
        if self.teamAction is not None:
            # action from team
            return self.teamAction.act(state, visited, actVars=actVars)
        else:
            # atomic action
            return self.actionCode

    """
    Returns true if the action is atomic, otherwise the action is a team.
    """
    def isAtomic(self):
        return self.teamAction is None

    """
    Change action to team or atomic action.
    """
    def mutate(self, mutateParams, parentTeam, teams, pActAtom):
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
