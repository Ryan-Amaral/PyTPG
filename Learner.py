"""
A Learner.
"""
class Learner:

    idCount = 0 # counter for id

    def __init__(self, action, maxProgSize, birthGen=0):
        self.id = Learner.idCount
        Learner.idCount += 1
        self.birthGen = birthGen
        self.action = Action(action)
        self.teamRefCount = 0

        # amount of instruction in program
        progSize = TpgTrainer.getRandInt(1, maxProgSize)
        for i in range(progSize):
            ins = Instruction()
            # initialize instruction by making random bit flips

            program.
