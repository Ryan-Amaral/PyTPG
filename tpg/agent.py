from tpg.program import Program
import pickle

"""
Simplified wrapper around a (root) team for easier interface for user.
"""
class Agent:

    """
    Create an agent with a team.
    """
    def __init__(self, team, num=1):
        self.team = team
        self.agentNum = num

    """
    Gets an action from the root team of this agent / this agent.
    """
    def act(self, state):
        return self.team.act(state)

    """
    Give this agent/root team a reward for the given task
    """
    def reward(self, score, task='task'):
        self.team.outcomes[task] = score

    """
    Check if agent completed this task already, to skip.
    """
    def taskDone(self, task):
        return task in self.team.outcomes

    """
    Save the agent to the file, saving any relevant class values to the instance.
    """
    def saveToFile(self, fileName):
        pickle.dump(self, open(fileName, 'wb'))

"""
Load some agent from the file, returning it and repopulate class values.
"""
def loadAgent(fileName):
    return pickle.load(open(fileName, 'rb'))
