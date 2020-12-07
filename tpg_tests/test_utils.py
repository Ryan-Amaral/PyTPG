import random

from tpg.learner import Learner
from tpg.action_object import ActionObject
from tpg.program import Program


dummy_init_params = {
    'generation': 0,
    'actionCodes':[
        0,1,2,3,4,5,6,7,8,9,10,11
    ]
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
        inputSize=30720,
        initParams = dummy_init_params
    )
    return program

'''
Create a dummy action object
'''
def create_dummy_action_object():
    action_object = ActionObject(actionIndex=random.randint(0,10), initParams=dummy_init_params)
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
