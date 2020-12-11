from tpg.program import Program
from tpg.action_object import ActionObject
import numpy as np
from tpg.utils import flip
import random
import collections

"""
A team has multiple learners, each learner has a program which is executed to
produce the bid value for this learner's action.
"""
class Learner:

    def __init__(self, initParams, program, actionObj, numRegisters):
        self.program = program
        self.actionObj = actionObj
        self.registers = np.zeros(numRegisters, dtype=float)

        '''
        TODO What's self.states? 
        '''
        self.states = []


        self.inTeams = [] # Store a list of teams that reference this learner, incoming edges
        

        self.genCreate = initParams["generation"] # Store the generation that this learner was created on

        '''
        TODO should this be -1 before it sees any frames?
        '''
        self.frameNum = 0 # Last seen frame is 0

        # Assign id from initParams counter
        self.id = initParams["idCountLearner"]
        '''
        TODO is this thread safe?
        '''
        initParams["idCountLearner"] += 1 # increment learner params

    def numTeamsReferencing(self):
        return len(self.inTeams)

    '''
    A learner is equal to another object if that object:
        - is an instance of the learner class
        - was created on the same generation
        - has an identical program
        - has the same action object
        - has the same inTeams

    '''
    def __eq__(self, o: object) -> bool:
        
        # Object must be an instance of Learner
        if not isinstance(o, Learner):
            return False

        # The object must have been created the same generation as us
        if self.genCreate != o.genCreate:
            return False

        # The object's program must be equal to ours
        if self.program != o.program:
            return False
        
        # The object's action object must be equal to ours
        if self.actionObj != o.actionObj:
            return False
        
        '''
        The other object's inTeams must match our own, therefore:
            - len(inTeams) must be equal
            - every id that appears in our inTeams must appear in theirs (order doesn't matter)
        '''
        if len(self.inTeams) != len(o.inTeams):
            return False

        '''
        Collection comparison via collection counters
        https://www.journaldev.com/37089/how-to-compare-two-lists-in-python
        '''
        if collections.Counter(self.inTeams) != collections.Counter(o.inTeams):
            return False
        
        return True

    '''
    Negation of __eq__
    '''
    def __ne__(self, o:object)-> bool:
        return not self.__eq__(o)

    '''
    String representation of a learner
    '''
    def __str__(self):
        return (
            "id: " + str(self.id) + 
            " created_at_gen: " + str(self.genCreate)
            )

    """
    Create a new learner, either copied from the original or from a program or
    action. Either requires a learner, or a program/action pair.
    """
    # def __init__(self, initParams, learner=None, program=None, actionObj=None, numRegisters=8,
    #         nOperations=5, nDestinations=8, inputSize=30720):

    #     if learner is not None:
    #         self.program = Program(instructions=learner.program.instructions,
    #             nOperations=nOperations, nDestinations=nDestinations, inputSize=inputSize,
    #             initParams=initParams)
    #         self.actionObj = ActionObject(learner.actionObj, initParams=initParams)
    #         self.registers = np.zeros(len(learner.registers), dtype=float)
    #     elif program is not None and actionObj is not None:
    #         self.program = program
    #         self.actionObj = actionObj
    #         self.registers = np.zeros(numRegisters, dtype=float)

    #     '''
    #     TODO What's self.states? 
    #     '''
    #     self.states = []

    #     self.numTeamsReferencing = 0 # amount of teams with references to this

    #     self.id = initParams["idCountLearner"]
    #     initParams["idCountLearner"] += 1

    #     self.genCreate = initParams["generation"]

    #     self.frameNum = 0

    """
    Get the bid value, highest gets its action selected.
    """
    def bid(self, state, actVars=None):
        Program.execute(state, self.registers,
                        self.program.instructions[:,0], self.program.instructions[:,1],
                        self.program.instructions[:,2], self.program.instructions[:,3])

        return self.registers[0]

    """
    Returns the action of this learner, either atomic, or requests the action
    from the action team.
    """
    def getAction(self, state, visited, actVars=None):
        return self.actionObj.getAction(state, visited, actVars=actVars)

    """
    Gets the team that is the action of the learners action object.
    """
    def getActionTeam(self):
        return self.actionObj.teamAction

    """
    Returns true if the action is atomic, otherwise the action is a team.
    """
    def isActionAtomic(self):
        return self.actionObj.isAtomic()

    """
    Mutates either the program or the action or both.
    """
    def mutate(self, mutateParams, parentTeam, teams, pActAtom):

        changed = False
        while not changed:
            # mutate the program
            if flip(mutateParams["pProgMut"]):
                changed = True
                self.program.mutate(mutateParams)

            # mutate the action
            if flip(mutateParams["pActMut"]):
                changed = True
                self.actionObj.mutate(mutateParams, parentTeam, teams, pActAtom)
