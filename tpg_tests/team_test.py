from random import randint
import unittest
import copy

from numpy.testing._private.utils import assert_equal
import xmlrunner
from tpg.team import Team
from tpg_tests.test_utils import create_dummy_program, dummy_init_params, create_dummy_learner, create_dummy_team

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

        l1_original_team_references = l1.numTeamsReferencing()
        l2_original_team_references = l2.numTeamsReferencing()

        team.addLearner(l1)
        team.addLearner(l2)

        #Ensure learner ref counts incremented
        self.assertEqual(l1_original_team_references + 1, l1.numTeamsReferencing())
        self.assertEqual(l2_original_team_references + 1, l2.numTeamsReferencing())

        #Ensure learner list grew
        self.assertEqual(2, len(team.learners))

        #Ensure no incomming learners appear in the team's inlearner list 
        self.assertEqual(0, len(team.inLearners))

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
        with self.assertRaises(Exception) as expected:
            team.addLearner(l2)

            # Ensure the raised exception contains the correct message and the learner that triggered it
            msg, dupLearner = expected.exception.args
            self.assertEqual("Attempted to add learner whose program already exists in our learner pool", msg)
            self.assertEqual(dupLearner, l2)
    
    '''
    Verify that the team removes a given learner
    '''
    def test_remove_learner(self):

        # Create a team with a random number of learners
        num_learners = randint(0, 256)
        random_index_in_learners = randint(0, num_learners-1)
        team, learners = create_dummy_team(num_learners)

        # Ensure the right number of learners appear in the team
        self.assertEqual(num_learners, len(team.learners))

        print("len(team.learners) before remove: {}".format(len(team.learners)))

        # Remove a randomly selected learner
        selected_learner = copy.deepcopy(team.learners[random_index_in_learners])
        print("selected learner: {}".format(selected_learner))
        print("learners[random_index_in_learners]: {}".format(learners[random_index_in_learners]) )
        
        print("selected and learners[random_index_in_learners] equal?: {}".format(selected_learner == learners[random_index_in_learners]))
        
        # Ensure the learner about to be removed has the team removing it in its inTeams list
        reference_to_removed_learner = team.learners[random_index_in_learners]
        self.assertTrue(team.id in reference_to_removed_learner.inTeams)

        team.removeLearner(selected_learner)

        print("len(team.learners) after remove: {}".format(len(team.learners)))

        # Ensure the list the team's learners shrunk by 1
        self.assertEqual(num_learners-1, len(team.learners))
        

        # Ensure the learner at the randomly selected index is no longer the selected learner
        if random_index_in_learners < len(team.learners): # If we deleted from the end of the list this assert would IndexError
            self.assertNotEqual(selected_learner, team.learners[random_index_in_learners])

        # Ensure nothing is removed if we ask to remove the same learner again
        team.removeLearner(selected_learner)
        self.assertEqual(num_learners - 1, len(team.learners))

        # Ensure the referenced learner was not deleted outright
        print("removed learner: {}".format(reference_to_removed_learner))
        self.assertIsNotNone(reference_to_removed_learner)

        # Ensure the learner that has been removed from the team no longer has the team's id in it's inTeams list
        print("reference to removed inTeams: {}".format(reference_to_removed_learner.inTeams))
        self.assertFalse(team.id in reference_to_removed_learner.inTeams)

    '''
    Verify that removing all learners from a team does so, without 
    destroying the underlying learner objects
    '''
    def test_remove_all_learner(self):

        # Create a team with a random number of learners
        num_learners = randint(0, 256)
        team, learners = create_dummy_team(num_learners)

        team.removeLearners()

        # Ensure learners were deleted
        self.assertEqual(0, len(team.learners))
        self.assertEqual(num_learners, len(learners))

        # Ensure deleted learner's inTeams list reflects this
        for learner in learners:
            self.assertEqual(0, len(learner.inTeams))

    def test_num_atomic_actions(self):

        # Create a team with a random number of learners
        num_learners = randint(0, 256)
        team, learners = create_dummy_team(num_learners)

        # Pick a random number smaller than the number of learners on the team to make non-atomic
        random_subset_bound = randint(0, num_learners-1)

        for i in range(0, random_subset_bound):
            team.learners[i].actionObj.teamAction = -1 # By making the team action not None we have a mock non-atomic action
        
        print("made {}/{} action objects non-atomic".format(random_subset_bound, len(team.learners)))

        # Ensure the number of atomic actions reported by the team is the total - those we made non-atomic
        self.assertEqual(num_learners - random_subset_bound, team.numAtomicActions())

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
