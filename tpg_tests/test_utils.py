import random
import numpy as np


from tpg.learner import Learner
from tpg.action_object import ActionObject
from tpg.program import Program
from tpg.team import Team


dummy_init_params = {
    'generation': 0,
    'actionCodes':[
        0,1,2,3,4,5,6,7,8,9,10,11
    ]
}

dummy_mutate_params = {
    'pProgMut': 0.5,
    'pActMut': 0.5,
    'pActAtom': 0.5,
    'pProgMut': 0.5,
    'pInstDel': 0.5,
    'pInstMut': 0.5,
    'pInstAdd': 0.5,
    'pLrnDel': 0.5,
    'pLrnAdd': 0.5,
    'pLrnMut': 0.5,
    'nOperations': 8,
    'nDestinations': 8,
    'inputSize': 8,
    'actionCodes':[
        0,1,2,3,4,5,6,7,8,9,10,11
    ],
    'pInstSwp':0.5,
    'generation': 1
}

'''
Dummy Creates
    These should be used to test constructs other than the ones
    being created by the function. For example, to test a Team
    you would create dummy programs and learners. But you wouldn't
    use the create_dummy_team function to test the creation of a team.

    This is because these methods verify nothing about the init procedure
    of the class they're returning an object of.
'''

'''
Create a dummy program with some preset values
'''
def create_dummy_program():
    program = Program(
        maxProgramLength=128,
        nOperations=7,
        nDestinations=8,
        inputSize=100,
        initParams = dummy_init_params
    )
    return program

'''
Create dummy team with some number of learners.
Returns the team and the learners added to it
'''
def create_dummy_team(num_learners=2):

    team = Team(dummy_init_params)
    learners = []

    for x in range(0, num_learners):
        learner = create_dummy_learner()
        learners.append(learner)
        team.addLearner(learner)
    
    return team, learners

'''
Create a dummy action object
'''
def create_dummy_action_object():
    action_object = ActionObject(action=random.randint(0,10), initParams=dummy_init_params)
    return action_object

'''
Create a dummy action object with a given team
'''
def create_dummy_team_action(team):
    action_object = ActionObject(team, initParams=dummy_init_params)
    return action_object

'''
Create a dummy learner with some preset values
'''
def create_dummy_learner():
    learner = Learner(
        dummy_init_params,
        program=create_dummy_program(),
        actionObj=create_dummy_action_object(),
        numRegisters=8
    )
    return learner

'''
Create a list of dummy learners
'''
def create_dummy_learners(num_learners=100):
    learners = []
    for i in range(num_learners):
        learners.append(create_dummy_learner())
    return learners

"""
Transform visual input from ALE to flat vector.
inState should be made int32 before passing in.
"""
def getStateALE(inState):
    # each row is all 1 color
    rgbRows = np.reshape(inState,(len(inState[0])*len(inState), 3)).T

    # add each with appropriate shifting
    # get RRRRRRRR GGGGGGGG BBBBBBBB
    return np.add(np.left_shift(rgbRows[0], 16),
        np.add(np.left_shift(rgbRows[1], 8), rgbRows[2]))
