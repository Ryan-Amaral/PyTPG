import random
import numpy as np
from numba import njit
import math

"""
A program that is executed to help obtain the bid for a learner.
"""
class Program:

    # max amount of instructions each program can have
    maxProgLen = 128

    """
    bits for:
    mode   op    dest       src
    1      111   11111...   11111111111...
    Mode: Always 1 bit, whether to use register or input.
    Op: Always 3 bits, one of 8 math operations (add, sub, mult, div, cos, log,
        exp, neg).
    Dest: At-least # of bits to store # of registers. The register to place the
        result of the instruction into.
    Src: At-least # of bits to store size of input. The index to take from
        input, or a register depending on Mode.
    """
    instLens   = [1,3,3,23]

    idCount = 0 # unique id of each program

    def __init__(self, insts=None):
        if insts is not None: # copy from existing
            self.insts = list(insts)
        else: # create random new
            maxInst = 2**sum(Program.instLens)-1
            self.insts = [random.randint(0, maxInst) for _ in
                                   range(random.randint(1, Program.maxProgLen))]

        self.id = Program.idCount
        Program.idCount += 1

        self.update()


    """
    Executes the program which returns a single final value.
    """
    @njit
    def execute(inpt, regs, modes, ops, dsts, srcs):
        regSize = len(regs)
        inptLen = len(inpt)
        for i in range(len(modes)):
            # first get source
            if modes[i] == False:
                src = regs[srcs[i]%regSize]
            else:
                src = inpt[srcs[i]%inptLen]

            # do operation
            op = ops[i]
            x = regs[dsts[i]]
            y = src
            dest = dsts[i]%regSize
            if op == 0:
                regs[dest] = x+y
            elif op == 1:
                regs[dest] = x-y
            elif op == 2:
                regs[dest] = x*y
            elif op == 3:
                if y != 0:
                    regs[dest] = x/y
            elif op == 4:
                regs[dest] = math.cos(y)
            elif op == 5:
                if y > 0:
                    regs[dest] = math.log(y)
            elif op == 6:
                regs[dest] = math.exp(y)
            elif op == 7:
                if x < y:
                    regs[dest] = x*(-1)

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
    def mutate(self, inpts=None, outs=None, update=True):
        # mutation code here

        if update:
            self.update()

    """
    Takes instructions and converts them into np arrays for easier more
    efficient execution.
    """
    def update(self):
        totalLen = sum(Program.instLens)
        instsData = np.array([
            [
                getIntSegment(inst, 0, Program.instLens[0], totalLen),
                getIntSegment(inst, Program.instLens[0],
                        Program.instLens[1], totalLen),
                getIntSegment(inst, sum(Program.instLens[:2]),
                        Program.instLens[2], totalLen),
                getIntSegment(inst, sum(Program.instLens[:3]),
                        Program.instLens[3], totalLen)
            ]
            for inst in self.insts])

        self.modes = np.array(instsData[:,0], dtype = bool)
        self.ops = np.array(instsData[:,1], dtype = np.int8)
        self.dsts = np.array(instsData[:,2], dtype = np.int8)
        self.srcs = np.array(instsData[:,3], dtype = np.int32)

def getIntSegment(num, bitStart, bitLen, totalLen):
    binStr = format(num, 'b').zfill(totalLen)
    return int(binStr[bitStart:bitStart+bitLen], 2)
