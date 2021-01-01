import io
import uuid
import xmlrunner
import unittest
import numpy as np
from tpg.program import Program
from extras import runPopulationParallel

class ProgramTest(unittest.TestCase):

    '''
    Tests the initalization of a program in the most
    simple case.
    '''
    def test_basic_init(self):

        max_length = 128

        # Assert that the id count starts at 0
        #self.assertEqual(0, Program.idCount)

        # needed for mutation and initialization
        mutateParams = {
            'idCountProgram': 0
        }

        program = Program(maxProgramLength=max_length, initParams=mutateParams)

        # Assert that, after creating a program the id count has been incremented
        self.assertTrue(isinstance(program.id, uuid.UUID))

        print(np.shape(program.instructions))

        # Assert that the first dimension of the instruction nparray, corresponding to
        # the number of instructions in the program is less than the max program
        # length.
        self.assertLessEqual(np.shape(program.instructions)[0], max_length)

    '''
    Verify that a program's instructions never exceed the maximum length specified
    during initialization. Run over many iterations to ensure this holds even
    as program length is randomly defined.
    '''
    def test_max_length(self):

        # Define the number of programs to create and the maximum length of
        # these programs.
        num_attempts = 1000
        max_length = 128

        # needed for mutation and initialization
        mutateParams = {
            'idCountProgram': 0
        }

        for i in range(num_attempts):
            with self.subTest():
                p = Program(maxProgramLength=max_length, initParams=mutateParams)
                self.assertLessEqual(np.shape(p.instructions)[0], max_length)
                self.assertTrue(isinstance(p.id, uuid.UUID))
        

    '''
    Checks if a program is still valid after numerous mutations are done.
    '''
    def test_mutate(self):

        # vars for the test and defining programs
        progs = 100
        muts = 100
        prog_len = 100
        ops = 5
        dests = 8
        inputs = 10000

        # needed for mutation and initialization
        mutateParams = {
            'pProgMut': 0.5,
            'nOperations': ops,
            'nDestinations': dests,
            'inputSize': inputs,
            'pInstDel': 0.5,
            'pInstMut': 0.5,
            'pInstSwp': 0.5,
            'pInstAdd': 0.5,
            'idCountProgram': 0
        }

        # mutate all the progs many times
        for i in range(progs):
            p = Program(maxProgramLength=100,
                nOperations=ops, nDestinations=dests, inputSize=inputs,
                initParams=mutateParams)
            for i in range(muts):
                p.mutate(mutateParams)

            # check for program validity
            # atleast 1 instruction
            self.assertGreaterEqual(len(p.instructions), 1)
            # make sure each value in each intex within proper range
            for inst in p.instructions:
                # mode
                self.assertGreaterEqual(inst[0], 0)
                self.assertLessEqual(inst[0], 1)
                # op
                self.assertGreaterEqual(inst[1], 0)
                self.assertLessEqual(inst[1], ops-1)
                # dest
                self.assertGreaterEqual(inst[2], 0)
                self.assertLessEqual(inst[2], dests-1)
                # input
                self.assertGreaterEqual(inst[3], 0)
                self.assertLessEqual(inst[3], inputs-1)

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
