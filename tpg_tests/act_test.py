from tpg_tests.test_utils import create_dummy_team, getStateALE
import unittest
import xmlrunner
import numpy as np

class ActTest(unittest.TestCase):

    '''
    Ensure act picks the learner with the top bid to produce the action
    '''
    #@unittest.skip
    def test_act(self):
        
        # Test that the top bid is selected during an action
        '''
        Create a random state. Note the random state should be run through
        getStateALE as it would during an actual atari game, and must follow
        the format (screen_width, screen_height, num_color_channels) where
        num_color channels should always be 3.
        '''
        random_state = np.random.randint(20, size=(5,5,3), dtype=np.int32)
        state = getStateALE(random_state)

        team, learners = create_dummy_team()

        '''
        The learner with the highest bid must be selected.
        If the highest bid is produced by multiple learners any of them are 
        valid selections.
        '''
        actVars = {"frameNum":1} # Frame number, used to avoid recomputing same frame
        top_bid = None
        top_learner = None
        valid_selection = list()
        for cursor in learners:
            bid = cursor.bid(state=state, actVars=actVars)

            print("learner: {} bid: {} action: {}".format(str(cursor.id), bid, cursor.actionObj.actionCode))
            if top_bid == None:
                top_bid = bid
                top_learner = cursor
                valid_selection.append(cursor)
                continue

            if top_bid < bid:
                valid_selection = list() # Reset the selection list
                top_bid = bid
                top_learner = cursor
                valid_selection.append(cursor)
            
            if top_bid == bid: # If the bid is equal to the top bid
                valid_selection.append(cursor) # Add the learner to the list of valid selections
        
        
        valid_actions = list()
        for cursor in valid_selection:
            valid_actions.append(team.act(state=state, actVars=actVars,visited=list()))

        # Ensure the chosen action is in the list of valid actions
        self.assertIn(top_learner.getAction(state=state, visited=list()), valid_actions)

    '''
    Create a simple cycle with three teams:

    T1: 
        L1->T2
        L2->T3
    T2:
        L1->T1
        L2->T3
    T3:
        L1->T2
        L1->T1

    This should throw a value error as eventually no valid action should be found.
    '''
    #@unittest.skip
    def test_simple_cycle_act(self):

        t1,l1 = create_dummy_team()
        t2,l2 = create_dummy_team()
        t3,l3 = create_dummy_team()

        # Wire everthing together as described
        l1[0].actionObj.teamAction = t2
        l1[0].actionObj.actionCode = None

        l1[1].actionObj.teamAction = t3
        l1[1].actionObj.actionCode = None

        l2[0].actionObj.teamAction = t1
        l2[0].actionObj.actionCode = None

        l2[1].actionObj.teamAction = t3
        l2[1].actionObj.actionCode = None

        l3[0].actionObj.teamAction = t2
        l3[0].actionObj.actionCode = None

        l3[1].actionObj.teamAction = t1
        l3[1].actionObj.actionCode = None

        random_sate = np.random.randint(20, size=(5,5,3), dtype=np.int32)
        state = getStateALE(random_sate)
        actVars = {"frameNum":1}

        # Ensure a value error is raised, as there should be no possible action
        with self.assertRaises(ValueError) as expected:
            visited = list()

            action = t1.act(state=state, visited=visited, actVars=actVars)

            # Ensure error is raised
            self.assertIsNotNone(expected.exception)

            # Ensure all teams string uuid appears in visited set
            self.assertIn(str(t1.id), visited)
            self.assertIn(str(t2.id), visited)
            self.assertIn(str(t3.id), visited)

            # Ensure visited is length 3
            self.assertEqual(3, len(visited)) 

    '''
    Recursive act with no final action, should raise value error
    '''
    #@unittest.skip
    def test_recursive_act(self):

        # Test that act doesn't revisit teams
        team_1, learners_1 = create_dummy_team()
        team_2, learners_2 = create_dummy_team()


        # Every learner in team 1 must point to team_2
        for cursor in learners_1:
            cursor.actionObj.teamAction = team_2
            cursor.actionObj.actionCode = None
        
        # Every learner in team 2 must point to team_1
        for cursor in learners_2:
            cursor.actionObj.teamAction = team_1
            cursor.actionObj.actionCode = None

        # No atomic actions anywhere
        self.assertEqual(0,team_1.numAtomicActions())
        self.assertEqual(0,team_2.numAtomicActions())

        '''
        Create a random state. Note the random state should be run through
        getStateALE as it would during an actual atari game, and must follow
        the format (screen_width, screen_height, num_color_channels) where
        num_color channels should always be 3.
        '''
        random_state = np.random.randint(20, size=(5,5,3), dtype=np.int32)
        state = getStateALE(random_state)
        actVars = {"frameNum":1} # Frame number, used to avoid recomputing same frame

        # Ensure a value error is raised, as there should be no possible action here.
        with self.assertRaises(ValueError) as expected:

            visited = list()

            action = team_1.act(state=state, visited=visited, actVars=actVars)

            # Ensure error is raised
            self.assertIsNotNone(expected.exception)

            # Ensure team_1 string uuid appears in visited set
            self.assertIn(str(team_1.id), visited)

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
