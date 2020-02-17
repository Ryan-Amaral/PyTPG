import random
import numpy as np
from numba import njit
import math
from tpg.utils import flip

"""
A program that is executed to help obtain the bid for a learner.
"""
class Program:

    # operation is some math or memory operation
    operationRange = 6 # 8 if memory
    # destination is the register to store result in for each instruction
    destinationRange = 8 # or however many registers there are
    # the source index of the registers or observation
    sourceRange = 30720 # should be equal to input size (or larger if varies)

    idCount = 0 # unique id of each program

    def __init__(self, instructions=None, maxProgramLength=128):
        if instructions is not None: # copy from existing
            self.instructions = np.array(instructions, dtype=np.int32)
        else: # create random new
            self.instructions = np.array([
                (random.randint(0,1),
                    random.randint(0, Program.operationRange-1),
                    random.randint(0, Program.destinationRange-1),
                    random.randint(0, Program.sourceRange-1))
                for _ in range(random.randint(1, maxProgramLength))], dtype=np.int32)

        self.id = Program.idCount
        Program.idCount += 1


    """
    Executes the program which returns a single final value.
    """
    @njit
    def execute(inpt, regs, modes, ops, dsts, srcs, memMatrix, memRows, memCols):
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
                regs[dest] = math.cos(y)
            elif op == 5:
                if x < y:
                    regs[dest] = x*(-1)
            elif op == 6:
                index = srcs[i]
                index %= (memRows*memCols)
                row = int(index / memRows)
                col = index % memCols
                regs[dest] = memMatrix[row, col]
            elif op == 7:
                # row offset (start from center, go to edges)
                for i in range(int(memRows/2)):
                    # probability to write (gets smaller as i increases)
                    # need to modify to be more robust with different # of rows
                    writeProb = 0.25 - (0.01*i)**2
                    # column to maybe write corresponding value into
                    for col in range(memCols):
                        # try write to lower half
                        if np.random.rand(1)[0] < writeProb:
                            row = (int(memRows/2) - i) - 1
                            memMatrix[row,col] = regs[col]
                        # try write to upper half
                        if np.random.rand(1)[0] < writeProb:
                            row = int(memRows/2) + i
                            memMatrix[row,col] = regs[col]

            if math.isnan(regs[dest]):
                regs[dest] = 0
            elif regs[dest] == np.inf:
                regs[dest] = np.finfo(np.float64).max
            elif regs[dest] == np.NINF:
                regs[dest] = np.finfo(np.float64).min


    """
    Mutates the program, by performing some operations on the instructions. If
    inpts, and outs (parallel) not None, then mutates until this program is
    distinct. If update then calls update when done.
    """
    def mutate(self, pMutRep, pDelInst, pAddInst, pSwpInst, pMutInst,
                regSize, uniqueProgThresh, inputs=None, outputs=None,
                maxMuts=100):
        if inputs is not None and outputs is not None:
            # mutate until distinct from others
            unique = False
            while not unique:
                if maxMuts <= 0:
                    break # too much
                maxMuts -= 1

                unique = True # assume unique until shown not
                self.mutateInstructions(pDelInst, pAddInst, pSwpInst, pMutInst)

                # check unique on all inputs from all learners outputs
                # input and outputs of i'th learner
                for i, lrnrInputs in enumerate(inputs):
                    lrnrOutputs = outputs[i]

                    for j, input in enumerate(lrnrInputs):
                        output = lrnrOutputs[j]
                        regs = np.zeros(regSize)
                        Program.execute(input, regs,
                            self.instructions[:,0], self.instructions[:,1],
                            self.instructions[:,2], self.instructions[:,3])
                        myOut = regs[0]
                        if abs(output-myOut) < uniqueProgThresh:
                            unique = False
                            break

                    if unique == False:
                        break
        else:
            # mutations repeatedly, random probably small amount
            mutated = False
            while not mutated or flip(pMutRep):
                self.mutateInstructions(pDelInst, pAddInst, pSwpInst, pMutInst)
                mutated = True

    """
    Potentially modifies the instructions in a few ways.
    """
    def mutateInstructions(self, pDel, pAdd, pSwp, pMut):
        changed = False

        while not changed:
            # maybe delete instruction
            if len(self.instructions) > 1 and flip(pDel):
                # delete random row/instruction
                self.instructions = np.delete(self.instructions,
                                    random.randint(0, len(self.instructions)-1),
                                    0)

                changed = True

            # maybe mutate an instruction (flip a bit)
            if flip(pMut):
                # index of instruction and part of instruction
                idx1 = random.randint(0, len(self.instructions)-1)
                idx2 = random.randint(0,3)

                # change max value depending on part of instruction
                if idx2 == 0:
                    maxVal = 1
                elif idx2 == 1:
                    maxVal = Program.operationRange-1
                elif idx2 == 2:
                    maxVal = Program.destinationRange-1
                elif idx2 == 3:
                    maxVal = Program.sourceRange-1

                # change it
                self.instructions[idx1, idx2] = random.randint(0, maxVal)

                changed = True

            # maybe swap two instructions
            if len(self.instructions) > 1 and flip(pSwp):
                # indices to swap
                idx1, idx2 = random.sample(range(len(self.instructions)), 2)

                # do swap
                tmp = np.array(self.instructions[idx1])
                self.instructions[idx1] = np.array(self.instructions[idx2])
                self.instructions[idx2] = tmp

                changed = True

            # maybe add instruction
            if flip(pAdd):
                # insert new random instruction
                self.instructions = np.insert(self.instructions,
                        random.randint(0,len(self.instructions)),
                            (random.randint(0,1),
                            random.randint(0, Program.operationRange-1),
                            random.randint(0, Program.destinationRange-1),
                            random.randint(0, Program.sourceRange-1)),
                        0)

                changed = True
