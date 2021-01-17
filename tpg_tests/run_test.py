import io
import xmlrunner
import unittest
from extras import runPopulationParallel
from tpg.trainer import Trainer
from tpg.team import Team
from tpg.learner import Learner



#@unittest.skip
class RunTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # do a quick test run to get results

        cls.trainer, _ = runPopulationParallel(
            envName="Boxing-v0", gens=100, popSize=2, reps=1,
            frames=1000, processes=23, nRandFrames=10, rootBasedPop=True,
            memType=None, operationSet="full", rampancy=(5,5,5), traversal="team")


    '''
    Runs tpg for a while measuring the reference counts on teams and learners,
    comparing tracked and actual amounts.
    '''
    def test_reference_counts(self):

        # iterate through all learners to see if any mistrack team referencing
        for lrnr in self.trainer.learners:
            refs=0
            for team in self.trainer.teams:
                if lrnr in team.learners:
                    refs += 1

            # ensure tracked amount and actual amount matches
            self.assertEqual(refs, lrnr.numTeamsReferencing())

        # iterate through all teams to see if any mistrack learners referencing
        for team in self.trainer.teams:
            refs = 0
            for lrnr in self.trainer.learners:
                if lrnr.getActionTeam() == team:
                    refs += 1

            # ensure tracked amount and actual amount matches
            self.assertEqual(refs, team.numLearnersReferencing())

    '''
    Checks to make sure the team has at-least 2 learners and at-least one atomic
    action learner, and no learners self-reference the team after mutations.
    '''

    def test_team_learner_constraints(self):
        # make sure ever team in population follows these rules
        for team in self.trainer.teams:
            self.assertGreaterEqual(len(team.learners), 2)
            self.assertGreaterEqual(team.numAtomicActions(), 1)
            for lrnr in team.learners:
                self.assertNotEqual(team, lrnr.getActionTeam())

    '''
    Make sure the numAtomicActions function on teams properly counts the amount.
    '''
    def test_team_numAtomicActions(self):

        # get actual count of atomic actions and compare for each team
        for team in self.trainer.teams:
            atomics = 0
            for lrnr in team.learners:
                if lrnr.actionObj.teamAction is None:
                    atomics += 1

            self.assertEqual(atomics, team.numAtomicActions())

    @classmethod
    def tearDownClass(cls):
        cls.trainer.cleanup()


if __name__ == '__main__':

    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
