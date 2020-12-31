import unittest
from tpg import trainer
import xmlrunner
from tpg.trainer import Trainer
from tpg.trainer import loadTrainer

class TrainerTest(unittest.TestCase):

    # Initalization variables to test
    dummy_actions = 20 # Number of actions

    
    '''
    Lists of tuples containing the value to test with and whether the value 
    is valid (True) or invalid (False). Invalid values should throw an exception.
    '''

    probability_pool = [
        (0.1, True),
        (0.5, True),
        (1.24, False),
        (-2.3, False),
        ("a string", False)]

    teamPopSize = [
        (10,True),
        (25,True),
        (100, True),
        (-1, False),
        (2.45, False),
        (0,False)]

    rootBasedPop = [
        (True, True),
        (False, True),
        (-1, False)]

    gap = [
        (0.25,True),
        (0.5, True),
        (0.75, True),
        (1.0, True),
        (-1, False),
        (1.24, False)]

    inputSize = [
        (0, False),
        (1000, True),
        (-50, False),
        ( 2.523, False)]

    nRegisters = [
        (8, True),
        (-1, False), 
        (2.43, False)]
    
    initMaxTeamSize = [
        (10, True),
        (-1, False),
        (2.52, False)]

    initMaxProgSize = [
        (20,True),
        (128, True),
        (-1, False),
        (2.4532, False)]
    
    doElites = [
        (True, True),
        (False,True),
        (-1, False)]

    rampancy = [
        ((-1,0,1), False),
        ((1,1,5), True),
        ((0, 0, 0), True),
        ((0), False),
        ((1), False),
        ((0, 3, 2), False)]

    operationSet = [
        ("def",True),
        ("full", True), 
        ("wtf", False)]

    traversal = [
        ("team", True),
        ("learner", True),
        ("garbage", False)]

    def test_init(self):

        # Test team pop sizes
        for cursor in self.teamPopSize:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, teamPopSize=cursor[0])
                self.assertEqual(cursor[0], trainer.teamPopSize)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,teamPopSize=cursor[0])
                    self.assertIsNotNone(expected.exception)
        
        # Test Root Based Pop
        for cursor in self.rootBasedPop:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, rootBasedPop=cursor[0])
                self.assertEqual(cursor[0], trainer.rootBasedPop)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,rootBasedPop=cursor[0])
                    self.assertIsNotNone(expected.exception)
        
        # Test Gap
        for cursor in self.gap:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, gap=cursor[0])
                self.assertEqual(cursor[0], trainer.gap)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,gap=cursor[0])
                    self.assertIsNotNone(expected.exception)
        
        # Test Input Size
        for cursor in self.inputSize:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, inputSize=cursor[0])
                self.assertEqual(cursor[0], trainer.inputSize)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,inputSize=cursor[0])
                    self.assertIsNotNone(expected.exception)
        
        # Test nRegisters
        for cursor in self.nRegisters:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, nRegisters=cursor[0])
                self.assertEqual(cursor[0], trainer.nRegisters)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,nRegisters=cursor[0])
                    self.assertIsNotNone(expected.exception)

        # Test initMaxTeamSize
        for cursor in self.initMaxTeamSize:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, initMaxTeamSize=cursor[0])
                self.assertEqual(cursor[0], trainer.initMaxTeamSize)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,initMaxTeamSize=cursor[0])
                    self.assertIsNotNone(expected.exception)

        # Test initMaxProgSize
        for cursor in self.initMaxProgSize:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, initMaxProgSize=cursor[0])
                self.assertEqual(cursor[0], trainer.initMaxProgSize)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,initMaxProgSize=cursor[0])
                    self.assertIsNotNone(expected.exception)

        # Test doElites
        for cursor in self.doElites:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, doElites=cursor[0])
                self.assertEqual(cursor[0], trainer.doElites)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,doElites=cursor[0])
                    self.assertIsNotNone(expected.exception)

        # Test rampancy
        for cursor in self.rampancy:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, rampancy=cursor[0])
                self.assertEqual(cursor[0], trainer.rampancy)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,rampancy=cursor[0])
                    self.assertIsNotNone(expected.exception)

        # Test operation set
        for cursor in self.operationSet:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, operationSet=cursor[0])
                self.assertEqual(cursor[0], trainer.operationSet)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,operationSet=cursor[0])
                    self.assertIsNotNone(expected.exception)
        
        # Test traversal
        for cursor in self.traversal:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, traversal=cursor[0])
                self.assertEqual(cursor[0], trainer.traversal)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,traversal=cursor[0])
                    self.assertIsNotNone(expected.exception)

        # Test pLrnDel
        for cursor in self.probability_pool:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, pLrnDel=cursor[0])
                self.assertEqual(cursor[0], trainer.pLrnDel)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,pLrnDel=cursor[0])
                    self.assertIsNotNone(expected.exception)
        
        # Test pLrnAdd
        for cursor in self.probability_pool:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, pLrnAdd=cursor[0])
                self.assertEqual(cursor[0], trainer.pLrnAdd)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,pLrnAdd=cursor[0])
                    self.assertIsNotNone(expected.exception)
        
        # Test pLrnMut
        for cursor in self.probability_pool:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, pLrnMut=cursor[0])
                self.assertEqual(cursor[0], trainer.pLrnMut)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,pLrnMut=cursor[0])
                    self.assertIsNotNone(expected.exception)

        # Test pProgMut
        for cursor in self.probability_pool:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, pProgMut=cursor[0])
                self.assertEqual(cursor[0], trainer.pProgMut)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,pProgMut=cursor[0])
                    self.assertIsNotNone(expected.exception)
        
        # Test pActMut
        for cursor in self.probability_pool:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, pActMut=cursor[0])
                self.assertEqual(cursor[0], trainer.pActMut)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,pActMut=cursor[0])
                    self.assertIsNotNone(expected.exception)
        
        # Test pActAtom
        for cursor in self.probability_pool:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, pActAtom=cursor[0])
                self.assertEqual(cursor[0], trainer.pActAtom)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,pActAtom=cursor[0])
                    self.assertIsNotNone(expected.exception)
        # Test pInstDel
        for cursor in self.probability_pool:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, pInstDel=cursor[0])
                self.assertEqual(cursor[0], trainer.pInstDel)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,pInstDel=cursor[0])
                    self.assertIsNotNone(expected.exception)
                    
        # Test pInstAdd
        for cursor in self.probability_pool:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, pInstAdd=cursor[0])
                self.assertEqual(cursor[0], trainer.pInstAdd)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,pInstAdd=cursor[0])
                    self.assertIsNotNone(expected.exception)
        
        # Test pInstSwp
        for cursor in self.probability_pool:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, pInstSwp=cursor[0])
                self.assertEqual(cursor[0], trainer.pInstSwp)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,pInstSwp=cursor[0])
                    self.assertIsNotNone(expected.exception)
        
        # Test pInstMut
        for cursor in self.probability_pool:
            if cursor[1]: # If this input is valid
                trainer = Trainer(actions = self.dummy_actions, pInstMut=cursor[0])
                self.assertEqual(cursor[0], trainer.pInstMut)
            else: # This input is invalid, ensure it throws an exception
                with self.assertRaises(Exception) as expected:
                    trainer = Trainer(actions=self.dummy_actions,pInstMut=cursor[0])
                    self.assertIsNotNone(expected.exception)

        trainer = Trainer(actions=self.dummy_actions)

        # Ensure the right inital team pop size was created
        self.assertEqual(trainer.teamPopSize, len(trainer.teams))
        # Ensure there are learners
        self.assertGreater(len(trainer.learners), 0)

    def test_pickle(self):
        
        trainer = Trainer(actions = self.dummy_actions)

        trainer.saveToFile("test_trainer_save")

        loaded_trainer = loadTrainer("test_trainer_save")

        '''
        Ensure loaded trainer has all the same teams and learners
        '''
        self.assertEqual(len(trainer.teams), len(loaded_trainer.teams))
        for cursor in trainer.teams:
            self.assertIn(cursor, loaded_trainer.teams)

        self.assertEqual(len(trainer.learners), len(loaded_trainer.learners))
        for cursor in trainer.learners:
            self.assertIn(cursor, loaded_trainer.learners)
    


if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
