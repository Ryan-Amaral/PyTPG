from logging import fatal

import numpy as np
import random
import copy 
from tpg.utils import flip

"""
Action  Object has a program to produce a value for the action, program doesn't
run if just a discrete action code.
"""
class ActionObject:

    '''
    An action object can be initalized by:
        - Copying another action object
        - Passing an index into the action codes in initParams as the action
        - Passing a team as the action
    '''
    def __init__(self, initParams=None, action=None):

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
            return


    # def __init__(self, actionObj=None, actionIndex=None, teamAction=None,
    #         initParams=None):
    #     if actionObj is not None:
    #         # clone the other action object
    #         self.actionCode = actionObj.actionCode
    #         self.teamAction = actionObj.teamAction
    #     else:
    #         # no cloning
    #         '''
    #         TODO What happens when actionIndex is None?
    #         '''
    #         self.actionCode = initParams["actionCodes"][actionIndex]
    #         self.teamAction = teamAction

    #     # increase references to team
    #     if self.teamAction is not None:
    #         self.teamAction.numLearnersReferencing += 1

    '''
    An ActionObject is equal to another object if that object:
        - is an instance of the ActionObject class
        - has the same action code
        - has the same team action
    '''
    def __eq__(self, o:object)->bool:

        # The other object must be an instance of the ActionObject class
        if not isinstance(o, ActionObject):
            return False
        
        # The other object's action code must be equal to ours
        if self.actionCode != o.actionCode:
            return False
        
        # The other object's team action must be equal to ours
        if self.teamAction != o.teamAction:
            return False

        return True

    '''
    Negate __eq__
    '''
    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

    def __str__(self):
        return "TeamAction {} ActionCode: {}".format(
            self.teamAction if self.teamAction is not None else 'None',
            self.actionCode if self.actionCode is not None else 'None'
        )

    """
    Returns the action code, and if applicable corresponding real action(s).
    """
    def getAction(self, state, visited, actVars=None, path_trace=None):
        if self.teamAction is not None:
            # action from team
            return self.teamAction.act(state, visited, actVars=actVars, path_trace=path_trace)
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
    def mutate(self, mutateParams, parentTeam, teams, pActAtom, learner_id):
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
                print("Learner {} switching from Team {} to atomic action".format(learner_id, self.teamAction.id))
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
                oldTeam = None
                if not self.isAtomic():
                    oldTeam = self.teamAction
                    self.teamAction.inLearners.remove(str(learner_id))

                self.teamAction = random.choice(selection_pool)
                # Let the new team know we're pointing to them
                self.teamAction.inLearners.append(str(learner_id))

                if oldTeam != None:
                    print("Learner {} switched from Team {} to Team {}".format(learner_id, oldTeam.id, self.teamAction.id))
        
        return self
            

    """
    Ensures proper functions are used in this class as set up by configurer.
    """
    @classmethod
    def configFunctions(cls, functionsDict):
        from tpg.configuration.conf_action_object import ConfActionObject

        if functionsDict["init"] == "def":
            cls.__init__ = ConfActionObject.init_def
        elif functionsDict["init"] == "real":
            cls.__init__ = ConfActionObject.init_real

        if functionsDict["getAction"] == "def":
            cls.getAction = ConfActionObject.getAction_def
        elif functionsDict["getAction"] == "real":
            cls.getAction = ConfActionObject.getAction_real
        
        if functionsDict["getRealAction"] == "real":
            cls.getRealAction = ConfActionObject.getRealAction_real
        elif functionsDict["getRealAction"] == "real_mem":
            cls.getRealAction = ConfActionObject.getRealAction_real_mem

        if functionsDict["isAtomic"] == "def":
            cls.isAtomic = ConfActionObject.isAtomic_def

        if functionsDict["mutate"] == "def":
            cls.mutate = ConfActionObject.mutate_def
        elif functionsDict["mutate"] == "real":
            cls.mutate = ConfActionObject.mutate_real