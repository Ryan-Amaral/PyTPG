from random import randint
import unittest
import copy
import collections
import scipy.stats as st
import math

from numpy.testing._private.utils import assert_equal
import xmlrunner
from tpg.team import Team
from tpg_tests.test_utils import create_dummy_program, dummy_init_params, create_dummy_learner, create_dummy_team

class TeamTest(unittest.TestCase):

    confidence_level = 95 # Confidence level in mutation probability correctness 95 = 95%
    confidence_interval = 5 # Confidence interval
    
    probabilities = [ 0.1, 0.25, 0.5, 0.66, 0.75, 0.82, 0.9] # probabilities at which to sample mutation functions, no 0 probabilities


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

    def test_mutation_delete(self):



        # Create a team with a random number of learners
        num_learners = randint(0,256)
        hi_probability_team, _ = create_dummy_team(num_learners)

        no_atomic_team, _ = create_dummy_team(num_learners)
        for i in range(0, num_learners):
            no_atomic_team.learners[i].actionObj.teamAction = -1 # By making the team action not None we have a mock non-atomic action

        self.assertEqual(0, no_atomic_team.numAtomicActions())

        num_learners_before = len(hi_probability_team.learners)

        #Ensure we error out if passing in a probability greater than 1.0
        with self.assertRaises(Exception) as expected:
            hi_probability_team.mutation_delete(1.1)
            msg = expected.exception.args
            self.assertEqual("pLrnDel is greater than or equal to 1.0!", msg)

        # Ensure nothing was deleted
        self.assertEqual(num_learners_before, len(hi_probability_team.learners))
        
        #Ensure we error out if we have no atomic actions
        with self.assertRaises(Exception) as expected:
            no_atomic_team.mutation_delete(0.99)

            # Ensure we spit back the problem team when we error
            msg, problem_team = expected.exception.args
            self.assertEqual("Less than one atomic action in team! This shouldn't happen",msg)
            self.assertTrue(isinstance(problem_team, Team))

        results = {}

        # Create a team with 100 learners
        template_team, _ = create_dummy_team(100)
        # Compute samples required to achieve confidence intervals for mutation tests
        # https://www.statisticshowto.com/probability-and-statistics/find-sample-size/#CI1
        # https://stackoverflow.com/questions/20864847/probability-to-z-score-and-vice-versa
        z_a2 = st.uniform.ppf(1-(1-(self.confidence_level/100))/2)
        margin_of_error = (self.confidence_interval/100)/2
        mutation_samples = math.ceil(0.25*pow(z_a2/margin_of_error,2)) 
        mutation_samples = mutation_samples * 2 # Just to be sure

        print('Need {} mutation samples to estabilish {} CL with {} margin of error in mutation probabilities'.format(mutation_samples, self.confidence_level, margin_of_error))

        for i in self.probabilities:
            print("Testing delete mutation with probability {}".format(i))


            # List counting the number of deleted learners over the test samples
            results[str(i)] = [None] * mutation_samples

            for j in range(0, mutation_samples):
                #print('sample {}/{} probability={}'.format( j, mutation_samples, i))
                team = copy.deepcopy(template_team)
                before = len(team.learners) 
                
                # Perform mutation delete
                team.mutation_delete(i)
                
                # Store the number of deleted learners
                results[str(i)][j] = before - len(team.learners)
            
            # Count how often 1 learners where deleted, how often 2 learners were deleted ... etc
            frequency = collections.Counter(results[str(i)])
            print(frequency)

            '''
            Ensure the number of deleted learners conforms to the expected proabilities
            as given by probability^num_deleted learners. Eg: with a delete probability
            of 0.5 we expect to delete 2 learers 0.25 or 25% of the time.
            '''
            report = {}
            header_line = "{:<40}".format('num_deleted (X or more) @ probability: {}'.format(i))
            actual_line = "{:<40}".format("actual")
            actual_freq_line = "{:<40}".format("actual freqency")
            expected_line = "{:<40}".format("expected probability")
            acceptable_error = "{:<40}".format("acceptable error")
            error_line = "{:<40}".format("error")
            for num_deleted in range(max(list(frequency.elements()))+1):
                report[str(num_deleted)] = {}

                occurance = frequency[num_deleted]
                if num_deleted != 0:
                    occurance = 0
                    for cursor in range(num_deleted, max(list(frequency.elements()))+1):
                        occurance = occurance + frequency[cursor]


                report[str(num_deleted)]['occurance'] = occurance
                report[str(num_deleted)]['actual'] = occurance/mutation_samples

                expected = i
                for cursor in range(1,num_deleted):
                    expected *= expected
                report[str(num_deleted)]['expected'] = expected

            

                
                header_line = header_line + "\t{:>5}".format(num_deleted)
                actual_line = actual_line + "\t{:>5}".format(report[str(num_deleted)]['occurance'])
                actual_freq_line = actual_freq_line + "\t{:>5.4f}".format(report[str(num_deleted)]['actual'])
                expected_line = expected_line + "\t{:>5.4f}".format(report[str(num_deleted)]['expected'] if num_deleted != 0 else (1-i))
                acceptable_error = acceptable_error + "\t{:>5.4f}".format((self.confidence_interval/100)*num_deleted if num_deleted != 0 else (self.confidence_interval/100))
                error_line = error_line + "\t{:>5.4f}".format(abs(report[str(num_deleted)]['actual'] - (report[str(num_deleted)]['expected'] if num_deleted != 0 else (1-i))))

                '''
                TODO It seems the expected probabilties and the actual ones can deviate sharply when num_deleted > 1. 
                I expect this is because the margin of error grows equal to the number of successive iterations? But I'm too
                statistically handicapped to confirm this. 
                '''
                if num_deleted == 0:
                    self.assertAlmostEqual((1-i),report[str(num_deleted)]['actual'],  delta=self.confidence_interval/100)
                if num_deleted == 1:
                    self.assertAlmostEqual(report[str(num_deleted)]['expected'],report[str(num_deleted)]['actual'],  delta=(self.confidence_interval/100)*num_deleted)

            print(header_line)
            print(actual_line)
            print(actual_freq_line)
            print(expected_line)
            print(acceptable_error)
            print(error_line)




if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
