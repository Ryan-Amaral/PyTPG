from tpg.program import Program
import pickle
from random import random

"""
Simplified wrapper around a (root) team for easier interface for user.
"""
class ConfAgent:

    """
    Create an agent with a team.
    """
    def init_def(self, team, num=1, actVars=None):
        self.team = team
        self.agentNum = num
        self.actVars = actVars

    """
    Gets an action from the root team of this agent / this agent.
    """
    def act_def(self, state):
        # track framenum so learners don't re-bid in the same frame
        self.actVars["frameNum"] = random()
        visited = list() #Create a new list to track visited team/learners each time
        return self.team.act(state, visited=visited, actVars=self.actVars)

    """
    Give this agent/root team a reward for the given task
    """
    def reward_def(self, score, task='task'):
        self.team.outcomes[task] = score

    """
    Check if agent completed this task already, to skip.
    """
    def taskDone_def(self, task):
        return task in self.team.outcomes

    """
    Save the agent to the file, saving any relevant class values to the instance.
    """
    def saveToFile_def(self, fileName):
        pickle.dump(self, open(fileName, 'wb'))
