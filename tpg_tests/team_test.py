import unittest
import copy
import xmlrunner
from tpg.team import Team
from tpg_tests.test_utils import create_dummy_program, dummy_init_params
from tpg_tests.test_utils import create_dummy_learner

class TeamTest(unittest.TestCase):



    def test_create_team(self):
        original_id_count = dummy_init_params['idCountTeam']

        # Create the team
        team = Team(dummy_init_params)

        # Verify instance variables and id
        self.assertIsNotNone(team.learners)
        self.assertIsNotNone(team.outcomes)
        self.assertIsNone(team.fitness)
        self.assertEqual(0,team.numLearnersReferencing)
        self.assertEqual(original_id_count, team.id)
        self.assertEqual(original_id_count+1, dummy_init_params['idCountTeam'])
        self.assertEqual(dummy_init_params['generation'], team.genCreate)


    '''
    Add a learner to a team
    '''
    def test_add_learners(self):

        team = Team(dummy_init_params)

        original_learners = team.learners

        l1 = create_dummy_learner()
        l2 = create_dummy_learner()

        l1_original_team_references = l1.numTeamsReferencing
        l2_original_team_references = l2.numTeamsReferencing

        team.addLearner(l1)
        team.addLearner(l2)

        #Ensure learner ref counts incremented
        self.assertEqual(l1_original_team_references + 1, l1.numTeamsReferencing)
        self.assertEqual(l2_original_team_references + 1, l2.numTeamsReferencing)

        #Ensure learner list grew
        self.assertEqual(2, len(team.learners))

    '''
    Verify that a team does not add a learner with the same program
    '''
    def test_no_duplicate_learners(self):

        program = create_dummy_program()
        l1 = create_dummy_learner()
        l2 = create_dummy_learner()

        # Set the program to be the same for both learners
        l1.program = copy.deepcopy(program)
        l2.program = copy.deepcopy(program)

        # Create a team
        team = Team(dummy_init_params)

        # Add the first learner
        team.addLearner(l1)

        # Assert that the second learner isn't added as it has an identical program
        self.assertFalse(team.addLearner(l2))


if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
