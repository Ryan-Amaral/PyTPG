"""
A Learner.
"""
class Learner:

    import random
    from __future__ import division
    from math import exp
    from bitarray import bitarray

    idCount = 0L # counter for id
    registerSize = 8 # size of registers

    def __init__(self, action, maxProgSize=8, randSeed=0 learner=None,
            makeNew=False, birthGen=0):

        if randSeed == 0:
            random.seed(int(round(time.time())))
        else:
            random.seed(randSeed)

        # reconstruct a learner
        if learner is not None:
            if makeNew: # make new from existing
                self.id = idCount
                idCount += 1
                self.birthGen = birthGen
                self.teamRefCount = 0
            else: # remake existing
                self.id = learner.id
                self.birthGen = learner.birthGen
                self.teamRefCount = learner.teamRefCount

            # these copied either way
            self.action = learner.action
            self.program = [i for i in learner.program]
            return

        # or make a brand new one
        self.id = idCount
        idCount += 1
        self.birthGen = birthGen
        self.action = Action(action)
        self.teamRefCount = 0
        self.program = [] # program is list of instructions

        # amount of instruction in program
        progSize = random.randint(1, maxProgSize)
        for i in range(progSize):
            ins = Instruction(randSeed=randSeed)
            self.program.append(ins)

    """
    Gets the bid from this learner based on the observation, bid being the
    weight this learner has in decision making (roughly).
    Args:
        obs:
            (Float[]) The current state of the environment.
        regDict:
            (Dict<Long,Float[]>) Dictionary of registers, find the register of
            this learner with the key self.id. If None, uses default (all 0)
            register.
    Returns:
        (Float) The bid value.
    """
    def bid(self, obs, regDict=None):
        # choose register appropriately
        registers = None
        if regDict is None:
            registers = [0]*registerSize
        else:
            if self.id not in regDict:
                regDict[self.id] = [0]*registerSize
            registers = regDict[self.id]

        return 1 / (1 + exp(-runProgram(obs,registers)))

    """
    Runs this learner's program.
    Args:
        obs:
            (Float[]) The current state of the environment.
        registers:
            (Float[]) Registers to be used for doing calculations with.
    Returns:
        (Float) What the destination register's value is at the end.
    """
    def runProgram(self, obs, registers):
        # iterate over instructions in the program
        for inst in program:


    """
    Mutates this learners program.
    Returns:
        (Bool) Whether actually mutated.
    """
    def mutateProgram(self, pProgramDelete, pProgramAdd, pProgramSwap,
            pProgramMutate, maxProgramSize):

        changed = False # whether a change occured

        # maybe delete instruction
        if (len(self.program) > 1 and random.uniform(0,1) < pProgramDelete):
            del self.program[random.choice(range(len(self.program)-1))]
            changed = True

        # maybe insert instruction
        if (len(self.program) < maxProgramSize and
                random.uniform(0,1) < pProgramAdd):
            ins = Instruction(randSeed=randSeed)
            self.program.insert(random.choice(range(len(self.program))))
            changed = True

        # maybe flip an instruction's bit
        if random.uniform(0,1) < pProgramMutate:
            self.program[random.choice(range(len(self.program)-1))].flip(
                    random.choice(range(Instruction.instructionSize-1)))
            changed = True

        # maybe swap two instructions
        if len(self.program) > 1 and random.uniform(0,1) < pProgramSwap:
            # indices to swap
            idx1 = random.choice(range(len(self.program)-1))
            idx2 = random.choice(
                    [x for x in range(len(self.program)-1) if x != idx1])
            # do swap
            tmp = self.program[idx1]
            self.program[idx1] = self.program[idx2]
            self.program[idx2] = tmp
            changed = True

        return changed

    """
    Changes the learners action to the argument action.
    Returns:
        (Bool) Whether the action is different after mutation.
    """
    def mutateAction(self, action):
        act = self.action
        self.action = action
        return act.equals(action)
