import io
import xmlrunner
import unittest
from extras import runPopulationParallel
from tpg.trainer import Trainer
from tpg.team import Team
from tpg.learner import Learner

class TrainerTest(unittest.TestCase):

    '''
    Runs tpg for a while measuring the reference counts on teams and learners,
    comparing tracked and actual amounts.
    '''
    def long_test_reference_counts(self):

        # do a quick test run to get results
        trainer, _ = runPopulationParallel(
            envName="Boxing-v0", gens=100, popSize=50, reps=1,
            frames=1000, processes=4, nRandFrames=5)

        # iterate through all learners to see if any mistrack team referencing
        for lrnr in trainer.learners:
            refs=0
            for team in trainer.teams:
                if lrnr in team.learners:
                    refs += 1

            # ensure tracked amount and actual amount matches
            assertEqual(refs, lrnr.numTeamsReferencing)

        # iterate through all teams to see if any mistrack learners referencing
        for team in trainer.teams:
            refs = 0
            for lrnr in trainer.learners:
                if lrnr.getActionTeam() == team:
                    refs += 1

            # ensure tracked amount and actual amount matches
            assertEqual(refs, team.numLearnersReferencing)

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
