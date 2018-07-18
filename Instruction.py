"""
An Instruction
"""
class Instruction:

    from bitarray import bitarray
    from bitarray import bitdiff
    import random

    # bits correspond to: mode + op + dest + src
    instructionSize = 1 + 3 + 3 + 16

    # offsets and sizes of segments
    modeOffset = 0
    modeSize = 1

    opOffset = 1
    opSize = 3

    destOffset = 4
    destSize = 3

    srcOffset = 7
    srcSize = 16


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
        if randSeed == 0:
            random.seed(int(round(time.time())))
        else:
            random.seed(randSeed)

        if randInit: # random bits
            self.inst = bitarray([random.choice([True,False])
                    for i in range(instructionSize)])
        else: # all 0's
            self.inst = bitarray([0]*instructionSize)

    """
    Gets a segment of the bitarray that makes up this instruction.
    Args:
        offset:
            (int) Offset to start of the segment.
        size:
            (int) Size of the segment wanted.
    Returns:
        (bitarray): The bitarray that makes up the desired segment.
    """
    def getBitArraySegment(self, offset, size):
        return self.inst[offset, offset + size]

    """
    Returns the int val of the bitarray that is passed in.
    """
    def getIntVal(self, ba):
        return int(ba.to01(), 2)

    """
    Checks if two bitarrays are equal.
    """
    def equalBitArrays(ba1, ba2):
        return bitdiff(ba1, ba2) == 0:

    """
    Flips the bit at the index.
    """
    def flip(self, index):
        self.inst[index] = not self.inst[index]
