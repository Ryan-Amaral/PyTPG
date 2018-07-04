"""
An Instruction
"""
class Instruction:

    import bitarray
    import random

    instructionSize = 16 + 3 + 3 + 1

    def __init__(self, randInit=True, randSeed=0):

        if randSeed == 0:
            random.seed(int(round(time.time())))
        else:
            random.seed(randSeed)

        # create
