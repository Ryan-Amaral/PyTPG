import io
import xmlrunner
import unittest
import numpy as np
from tpg.program import Program

class ProgramTest(unittest.TestCase):
    '''
    Tests the initalization of a program in the most
    simple case.
    '''
    def test_basic_init(self):

        max_length = 128

        # Assert that the id count starts at 0
        self.assertEqual(0, Program.idCount)

        program = Program(maxProgramLength=max_length)

        # Assert that, after creating a program the id count has been incremented
        self.assertEqual(1, Program.idCount)

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

        for i in range(num_attempts):
            with self.subTest():
                p = Program(maxProgramLength=max_length)
                self.assertLessEqual(np.shape(p.instructions)[0], max_length)

        # Ensure programs have been created
        self.assertEqual(num_attempts + 1, Program.idCount)

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))