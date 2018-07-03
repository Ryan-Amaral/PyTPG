"""
A Learner.
"""
class Learner:

    import random

    idCount = 0 # counter for id

    def __init__(self, action, maxProgSize, randSeed=0 learner=None,
            birthGen=0):

        if randSeed == 0:
            random.seed(int(round(time.time())))
        else:
            random.seed(randSeed)

        # reconstruct a learner
        if learner is not None:
            self.id = learner.id
            self.birthGen = learner.birthGen
            self.action = learner.action
            self.teamRefCount = learner.teamRefCount
            self.program = [i for i in learner.program]
            return

        # or make a brand new one
        self.id = Learner.idCount
        Learner.idCount += 1
        self.birthGen = birthGen
        self.action = Action(action)
        self.teamRefCount = 0
        self.program = [] # program is list of instructions

        # amount of instruction in program
        progSize = random.randint(1, maxProgSize)
        for i in range(progSize):
            ins = Instruction()
            self.program.append(ins)
