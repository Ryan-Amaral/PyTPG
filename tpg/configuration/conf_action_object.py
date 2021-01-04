from tpg.program import Program
import numpy as np
import random
from tpg.utils import flip
from tpg.action_object import ActionObject

"""
Action  Object has a program to produce a value for the action, program doesn't
run if just a discrete action code.
"""
class ConfActionObject:

    def init_def(self, initParams=None, action = None):


        '''
        Defer importing the Team class to avoid circular dependency.
        This may require refactoring to fix properly
        '''
        from tpg.team import Team

        # The action is a team
        '''
        TODO handle team references somehow
        '''
        if isinstance(action, Team):
            self.teamAction = action
            self.actionCode = None
            print("chose team action")
            return
    

        # The action is another action object
        if isinstance(action, ActionObject):
            self.actionCode = action.actionCode
            self.teamAction = action.teamAction
            return

        # An int means the action is an index into the action codes in initParams
        if isinstance(action, int):
            
            if "actionCodes" not in initParams:
                raise Exception('action codes not found in init params', initParams)

            try:
                self.actionCode = initParams["actionCodes"][action]
                self.teamAction = None
            except IndexError as err:
                '''
                TODO log index error
                '''
                print("Index error")
            return

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
    def mutate_def(self, mutateParams, parentTeam, teams, pActAtom, learner_id):
        # mutate action
        if flip(pActAtom):
            # atomic
            '''
            If we already have an action code make sure not to pick the same one.
            TODO handle case where there is only 1 action code.
            '''
            if self.actionCode is not None:
                options = list(filter(lambda code: code != self.actionCode,mutateParams["actionCodes"]))
            else:
                options = mutateParams["actionCodes"]

            # let our current team know we won't be pointing to them anymore
            if not self.isAtomic():
                self.teamAction.inLearners.remove(str(learner_id))

            self.actionCode = random.choice(options)
            self.teamAction = None
        else:
            # team action
            selection_pool = [t for t in teams
                    if t is not self.teamAction and t is not parentTeam]

            # If we have a valid set of options choose from them
            if len(selection_pool) > 0:
                # let our current team know we won't be pointing to them anymore
                if not self.isAtomic():
                    self.teamAction.inLearners.remove(str(learner_id))

                self.teamAction = random.choice(selection_pool)
                # Let the new team know we're pointing to them
                self.teamAction.inLearners.append(str(learner_id))

        
        return self

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
