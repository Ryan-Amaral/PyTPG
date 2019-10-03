import numpy as np
from tpg.utils import flip

"""
A persistent memory module to exist all through evolution and execution, shared
between all agents.
"""
class Memory:

    """
    Creates the memory matrix of specified size (columns should be the number
    of registers used by program). Initialized to all 0.0.
    """
    def __init__(self, rows=100, columns=8):
        self.rows = rows
        self.columns = columns
        self.memMatrix = np.zeros((rows, columns))

    """
    Returns the value at a single cell in the memory matrix.
    """
    def read(self, index):
        index %= (self.rows*self.columns)
        row = int(index / self.rows)
        col = index % self.columns

        return self.memMatrix[row, col]

    """
    Writes the values into the memory matrix. More central values have a higher
    success rate of being written, to create a gradient of short to longer term
    memory. The length of values should be equivalent to the number of
    columns/registers.
    """
    def write(self, values):
        # row offset (start from center, go to edges)
        for i in range(int(self.rows/2)):
            # probability to write (gets smaller as i increases)
            # need to modify to be more robust with different # of rows
            writeProb = 0.25 - (0.01*i)**2
            # column to maybe write corresponding value into
            for col in range(self.columns):
                # try write to lower half
                if flip(writeProb):
                    row = (int(self.rows/2) - i) - 1
                    self.memMatrix[row,col] = values[col]
                # try write to upper half
                if flip(writeProb):
                    row = int(self.rows/2) + i
                    self.memMatrix[row,col] = values[col]
