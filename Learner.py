"""
A Learner.
"""
class Learner:

    import random

    idCount = 0 # counter for id

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
    Mutates this learners program.
    Returns:
        (Bool) Whether actually mutated.
    """
    def mutateProgram(self, pProgramDelete, pProgramAdd, pProgramSwap,
            pProgramMutate, maxProgramSize):
        pass

    """
    Changes the learners action to the argument action.
    Returns:
        (Bool) Whether the action is different after mutation.
    """
    def mutateAction(self, action):
        act = self.action
        self.action = action
        return act.equals(action)
