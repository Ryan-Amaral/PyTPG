from bitarray import bitarray
from bitarray import bitdiff
import random

"""
An Instruction
"""
class Instruction:

    # bits correspond to: mode + op + dest + src
    instructionSize = 1 + 3 + 3 + 16

    # offsets and sizes of segments
    slcMode = slice(0,1)
    slcOp = slice(1,4)
    slcDest = slice(4,7)
    slcSrc = slice(7,23)

    # modes
    mode0 = bitarray([0])
    mode1 = bitarray([1])

    # operations
    opSum  = bitarray([0,0,0])
    opDiff = bitarray([0,0,1])
    opProd = bitarray([0,1,0])
    opDiv  = bitarray([0,1,1])
    opCos  = bitarray([1,0,0])
    opLog  = bitarray([1,0,1])
    opExp  = bitarray([1,1,0])
    opCond = bitarray([1,1,1])

    def __init__(self, randInit=True, randSeed=0):
        self.rand = random.Random()
        if randSeed == 0:
            self.rand.seed()
        else:
            self.rand.seed(randSeed)

        if randInit: # random bits
            self.inst = bitarray([self.rand.choice([True,False])
                    for i in range(Instruction.instructionSize)])
        else: # all 0's
            self.inst = bitarray([False]*Instruction.instructionSize)

    """
    Gets a segment of the bitarray that makes up this instruction.
    Args:
        slc:
            (slice) From the static attributes of this class. Ex: slcMode.
    Returns:
        (bitarray): The bitarray that makes up the desired segment.
    """
    def getBitArraySeg(self, slc):
        return self.inst[slc]

    """
    Returns the int val of the bitarray that is passed in.
    """
    def getIntVal(ba):
        return int(ba.to01(), 2)

    """
    Checks if two bitarrays are equal.
    """
    def equalBitArrays(ba1, ba2):
        return bitdiff(ba1, ba2) == 0

    """
    Flips the bit at the index.
    """
    def flip(self, index):
        self.inst[index] = not self.inst[index]
