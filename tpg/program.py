import random
import numpy as np
from numba import njit
import math
from tpg.utils import flip

"""
A program that is executed to help obtain the bid for a learner.
"""
class Program:

    def __init__(self, instructions=None, maxProgramLength=128, nOperations=5,
            nDestinations=8, inputSize=30720, initParams=None):
        """

        if instructions is not None: # copy from existing
            self.instructions = np.array(instructions, dtype=np.int32)
        else: # create random new
            self.instructions = np.array([
                (random.randint(0,1),
                    random.randint(0, nOperations-1),
                    random.randint(0, nDestinations-1),
                    random.randint(0, inputSize-1))
                for _ in range(random.randint(1, maxProgramLength))], dtype=np.int32)

        self.id = initParams["idCountProgram"]
        initParams["idCountProgram"] += 1
        """
        pass

    def __eq__(self, object):
        
        # If the other object's class name isn't Program it's not a program
        if type(object).__name__ != "Program":
            return False

        # Compare instructions

        # If we don't have the same number of instructions we're not the same
        if len(object.instructions) != len(self.instructions):
            return False

        # Check that our instructions match one for one, otherwise we're not equal
        return np.array_equal(self.instructions, object.instructions)


    """
    Executes the program which returns a single final value.
    """
    @njit
    def execute(inpt, regs, modes, ops, dsts, srcs):
        """
        regSize = len(regs)
        inptLen = len(inpt)
        for i in range(len(modes)):
            # first get source
            if modes[i] == 0:
                src = regs[srcs[i]%regSize]
            else:
                src = inpt[srcs[i]%inptLen]

            # get data for operation
            op = ops[i]
            x = regs[dsts[i]]
            y = src
            dest = dsts[i]%regSize

            # do an operation
            if op == 0:
                regs[dest] = x+y
            elif op == 1:
                regs[dest] = x-y
            elif op == 2:
                regs[dest] = x*2
            elif op == 3:
                regs[dest] = x/2
            elif op == 4:
                if x < y:
                    regs[dest] = x*(-1)

            if math.isnan(regs[dest]):
                regs[dest] = 0
            elif regs[dest] == np.inf:
                regs[dest] = np.finfo(np.float64).max
            elif regs[dest] == np.NINF:
                regs[dest] = np.finfo(np.float64).min
        """
        pass


    """
    Mutates the program, by performing some operations on the instructions.
    """
    def mutate(self, mutateParams):
        """
        # mutations repeatedly, random probably small amount
        mutated = False
        while not mutated or flip(mutateParams["pProgMut"]):
            self.mutateInstructions(mutateParams)
            mutated = True
        """
        pass

    """
    Potentially modifies the instructions in a few ways.
    """
    def mutateInstructions(self, mutateParams):
        """

        changed = False

        while not changed:
            # maybe delete instruction
            if len(self.instructions) > 1 and flip(mutateParams["pInstDel"]):
                # delete random row/instruction
                self.instructions = np.delete(self.instructions,
                                    random.randint(0, len(self.instructions)-1),
                                    0)

                changed = True

            # maybe mutate an instruction (flip a bit)
            if flip(mutateParams["pInstMut"]):
                # index of instruction and part of instruction
                idx1 = random.randint(0, len(self.instructions)-1)
                idx2 = random.randint(0,3)

                # change max value depending on part of instruction
                if idx2 == 0:
                    maxVal = 1
                elif idx2 == 1:
                    maxVal = mutateParams["nOperations"]-1
                elif idx2 == 2:
                    maxVal = mutateParams["nDestinations"]-1
                elif idx2 == 3:
                    maxVal = mutateParams["inputSize"]-1

                # change it
                self.instructions[idx1, idx2] = random.randint(0, maxVal)

                changed = True

            # maybe swap two instructions
            if len(self.instructions) > 1 and flip(mutateParams["pInstSwp"]):
                # indices to swap
                idx1, idx2 = random.sample(range(len(self.instructions)), 2)

                # do swap
                tmp = np.array(self.instructions[idx1])
                self.instructions[idx1] = np.array(self.instructions[idx2])
                self.instructions[idx2] = tmp

                changed = True

            # maybe add instruction
            if flip(mutateParams["pInstAdd"]):
                # insert new random instruction
                self.instructions = np.insert(self.instructions,
                        random.randint(0,len(self.instructions)),
                            (random.randint(0,1),
                            random.randint(0, mutateParams["nOperations"]-1),
                            random.randint(0, mutateParams["nDestinations"]-1),
                            random.randint(0, mutateParams["inputSize"]-1)),0)

                changed = True
        """
        pass
