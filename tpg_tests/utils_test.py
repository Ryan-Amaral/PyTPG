import io
import xmlrunner
import unittest
from extras import runPopulationParallel
from tpg.trainer import Trainer
from tpg.team import Team
from tpg.learner import Learner
from tpg.utils import pathDepths
from tpg_tests.test_utils import create_dummy_team, create_dummy_learners



#@unittest.skip
class RunTest(unittest.TestCase):


    '''
    makes sure the pathDepths util function works.
    '''
    def test_pathDepths(self):
        """ first try a simple single team"""
        team, _ = create_dummy_team(num_learners=2)

        self.assertEqual(pathDepths(team), [1])

        """ A team with 2 children """

        # create 2 new teams
        team1, _ = create_dummy_team()
        team2, _ = create_dummy_team()

        # make them children of first team
        team.learners[0].actionObj.teamAction = team1
        team.learners[1].actionObj.teamAction = team2

        self.assertEqual(pathDepths(team), [1,2,2])

        """ A team with 2 children where the children also reference each other """
        team1.learners[0].actionObj.teamAction = team2
        team2.learners[0].actionObj.teamAction = team1

        self.assertEqual(pathDepths(team), [1,2,3,2,3])
        
        """ A team with 2 children where the children also reference each other and back to the root"""
        team1.learners[1].actionObj.teamAction = team
        team2.learners[1].actionObj.teamAction = team

        self.assertEqual(pathDepths(team), [1,2,3,2,3])




if __name__ == '__main__':

    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
