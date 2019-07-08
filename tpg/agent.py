"""
Simplified wrapper around a (root) team for easier interface for user.
"""
class Agent:

    """
    Gets an action from the root team of this agent / this agent.
    """
    def act(self, obs):
        pass

    """
    Give this agent/root team a reward for the given task
    """
    def reward(self, score, task):
        pass
