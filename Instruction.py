"""
An Instruction
"""
class Instruction:

    from bitarray import bitarray
    import random

    # bits correspond to: mode + op + dest + src
    instructionSize = 1 + 3 + 3 + 16
    modeSlice = slice(0,1)
    opSlice = slice(1,4)
    destSlice = slice(4,7)
    srcSlice = slice(7,23)

    def __init__(self, randInit=True, randSeed=0):
        if randSeed == 0:
            random.seed(int(round(time.time())))
        else:
            random.seed(randSeed)

        if randInit: # random bits
            self.instruction = bitarray([random.choice([True,False])
                    for i in range(instructionSize)])
        else: # all 0's
            self.instruction = bitarray([0]*instructionSize)
