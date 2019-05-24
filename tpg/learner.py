from __future__ import division

import random
import math
from bitarray import bitarray
import numpy as np
from numba import njit # for optimizing program running

from tpg.instruction import Instruction
import tpg.action

"""
A Learner. Contains a program that makes a bid to use its action, based on the
current input and perhaps previous outcomes.
"""
class Learner:

    learnerIdCounter = 0 # counter for id
    registerSize = 8 # size of registers

    def __init__(self, action=0, maxProgSize=8, randSeed=0, learner=None,
            makeNew=False, birthGen=0):

        self.randSeed = randSeed
        self.rand = random.Random()
        if randSeed == 0:
            self.rand.seed()
        else:
            self.rand.seed(randSeed)

        # reconstruct a learner
        if learner is not None:
            if makeNew: # make new from existing
                self.id = Learner.learnerIdCounter
                Learner.learnerIdCounter += 1
                self.birthGen = birthGen
                self.teamRefCount = 0
            else: # remake existing
                self.id = learner.id
                self.birthGen = learner.birthGen
                self.teamRefCount = learner.teamRefCount

            # these copied either way
            self.action = tpg.action.Action(learner.action.act)
            self.program = [Instruction(inst=i) for i in learner.program]
        else:
            # or make a brand new one
            self.id = Learner.learnerIdCounter
            Learner.learnerIdCounter += 1
            self.birthGen = birthGen
            self.action = tpg.action.Action(action)
            self.teamRefCount = 0
            self.program = [] # program is list of instructions

            # amount of instruction in program
            progSize = self.rand.randint(1, maxProgSize)
            for i in range(progSize):
                ins = Instruction(randSeed=randSeed)
                self.program.append(ins)

        self.extractProgramData(self.program) # get data in form for optimized running

    def extractProgramData(self, program):
        progData = np.array(
            [[
                Instruction.getIntVal(inst.getBitArraySeg(Instruction.slcMode)),
                Instruction.getIntVal(inst.getBitArraySeg(Instruction.slcOp)),
                Instruction.getIntVal(inst.getBitArraySeg(Instruction.slcDest)),
                Instruction.getIntVal(inst.getBitArraySeg(Instruction.slcSrc))
            ]
            for inst in program])

        self.modes = np.array(progData[:,0], dtype = bool)
        self.ops = np.array(progData[:,1], dtype = np.int8)
        self.dests = np.array(progData[:,2], dtype = np.int8)
        self.srcs = np.array(progData[:,3], dtype = np.int32)


    """
    Gets the bid from this learner based on the observation, bid being the
    weight this learner has in decision making (roughly).
    Args:
        obs:
            (Float[]) The current state of the environment.
        regDict:
            (Dict<Int,Float[]>) Dictionary of registers, find the registers of
            this learner with the key self.id. If None, uses default (all 0)
            register.
    Returns:
        (Float) The bid value.
    """
    def bid(self, obs, regDict=None, si=None):
        # choose register appropriately
        if regDict is None:
            #registers = [0]*Learner.registerSize
            registers = np.zeros(Learner.registerSize)
        else:
            if self.id not in regDict:
                regDict[self.id] = np.zeros(Learner.registerSize)
            registers = regDict[self.id]

        # math overflow error happens sometimes
        try:
            if si is not None: # visual debug
                progResult = runProgram2(obs, registers, self.modes,
                        self.ops, self.dests, self.srcs, Learner.registerSize, si)
            else:
                progResult = runProgram1(obs, registers, self.modes,
                        self.ops, self.dests, self.srcs, Learner.registerSize)

            return progResult
        except:
            return 0

    """
    Mutates this learners program.
    Returns:
        (Bool) Whether actually mutated.
    """
    def mutateProgram(self, pProgramDelete, pProgramAdd, pProgramSwap,
            pProgramMutate, maxProgramSize):

        changed = False # whether a change occured

        # maybe delete instruction
        if (len(self.program) > 1 and self.rand.uniform(0,1) < pProgramDelete):
            del self.program[self.rand.choice(range(len(self.program)))]
            changed = True

        # maybe insert instruction
        if (len(self.program) < maxProgramSize and
                self.rand.uniform(0,1) < pProgramAdd):
            ins = Instruction(randSeed=self.randSeed)
            self.program.insert(self.rand.choice(range(len(self.program))), ins)
            changed = True

        # maybe flip an instruction's bit
        if self.rand.uniform(0,1) < pProgramMutate:
            self.program[self.rand.choice(range(len(self.program)))].flip(
                    self.rand.choice(range(Instruction.instructionSize)))
            changed = True

        # maybe swap two instructions
        if len(self.program) > 1 and self.rand.uniform(0,1) < pProgramSwap:
            # indices to swap
            idx1 = self.rand.choice(range(len(self.program)))
            idx2 = self.rand.choice(
                    [x for x in range(len(self.program)) if x != idx1])
            # do swap
            tmp = self.program[idx1]
            self.program[idx1] = self.program[idx2]
            self.program[idx2] = tmp
            changed = True

        self.extractProgramData(self.program) # get data in form for optimized running

        return changed

    """
    Changes the learners action to the argument action.
    Args:
        action:
            (Action) an Action object.
    Returns:
        (Bool) Whether the action is different after mutation.
    """
    def mutateAction(self, action):
        # set action to new but keep reference
        act = self.action
        self.action = action

        # dereference if team in original action
        if not act.isAtomic():
            act.act.learnerRefCount -= 1
        # add reference if team in new action
        if not self.action.isAtomic():
            self.action.act.learnerRefCount += 1

        return not act.equals(action)

"""
Run program without screen indexing, for regular non-debug/vizualizing use.
"""
@njit
def runProgram1(obs, registers, modes, ops, dsts, srcs, regSize):

    for i in range(len(modes)):
        # first get source
        if modes[i] == False:
            src = registers[srcs[i]%regSize]
        else:
            src = obs[srcs[i]%len(obs)]

        # do operation
        op = ops[i]
        x = registers[dsts[i]]
        y = src
        if op == 0:
            registers[dsts[i]] = x+y
        elif op == 1:
            registers[dsts[i]] = x-y
        elif op == 2:
            registers[dsts[i]] = x*y
        elif op == 3:
            if y != 0:
                registers[dsts[i]] = x/y
        elif op == 4:
            registers[dsts[i]] = math.cos(y)
        elif op == 5:
            if y > 0:
                registers[dsts[i]] = math.log(y)
        elif op == 6:
            registers[dsts[i]] = math.exp(y)
        elif op == 7:
            if x < y:
                registers[dsts[i]] = x*(-1)

        if math.isnan(registers[dsts[i]]):
            registers[dsts[i]] = 0
        elif registers[dsts[i]] == np.inf:
            registers[dsts[i]] = np.finfo(np.float64).max
        elif registers[dsts[i]] == np.NINF:
            registers[dsts[i]] = np.finfo(np.float64).min

    return registers[0]

"""
Run program with screen indexing, for debug/vizualizing use.
"""
@njit
def runProgram2(obs, registers, modes, ops, dsts, srcs, regSize, si):

    for i in range(len(modes)):
        # first get source
        if modes[i] == False:
            src = registers[srcs[i]%regSize]
        else:
            idx = srcs[i]%len(obs)
            src = obs[idx]
            if si is not None:
                si[idx] = 1 # mark location as visited

        # do operation
        op = ops[i]
        x = registers[dsts[i]]
        y = src
        if op == 0:
            registers[dsts[i]] = x+y
        elif op == 1:
            registers[dsts[i]] = x-y
        elif op == 2:
            registers[dsts[i]] = x*y
        elif op == 3:
            if y != 0:
                registers[dsts[i]] = x/y
        elif op == 4:
            registers[dsts[i]] = math.cos(y)
        elif op == 5:
            if y > 0:
                registers[dsts[i]] = math.log(y)
        elif op == 6:
            registers[dsts[i]] = math.exp(y)
        elif op == 7:
            if x < y:
                registers[dsts[i]] = x*(-1)

        if math.isnan(registers[dsts[i]]):
            registers[dsts[i]] = 0
        elif registers[dsts[i]] == np.inf:
            registers[dsts[i]] = np.finfo(np.float64).max
        elif registers[dsts[i]] == np.NINF:
            registers[dsts[i]] = np.finfo(np.float64).min

    return registers[0]
