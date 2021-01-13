from tpg.program import Program
import pickle
from random import random
import time

"""
Simplified wrapper around a (root) team for easier interface for user.
"""
class Agent:

    """
    Create an agent with a team.
    """
    def __init__(self, team, num=1, actVars=None):
        self.team = team
        self.agentNum = num
        self.actVars = actVars

    """
    Gets an action from the root team of this agent / this agent.
    """
    def act(self, state, path_trace=None):
        #print("What the fuck is this dumb ass bullshit")
        start_execution_time = time.time()*1000.0
        self.actVars["frameNum"] = random()
        visited = list() #Create a new list to track visited team/learners each time
        
        result = None
        path = None
        if path_trace != None:
            path = list()
            result = self.team.act(state, visited=visited, actVars=self.actVars, path_trace=path)
        else:
            result = self.team.act(state, visited=visited, actVars=self.actVars)

        end_execution_time = time.time()*1000.0
        execution_time = end_execution_time - start_execution_time
        if path_trace != None:

            path_trace['execution_time'] = execution_time
            path_trace['execution_time_units'] = 'milliseconds'
            path_trace['root_team_id'] = str(self.team.id)
            path_trace['final_action'] = result
            path_trace['path'] = path 
            path_trace['depth'] = len(path)
            
        return result

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
    Should be called when the agent is loaded from a file or when loaded into 
    another process/thread, to ensure proper function used in all classes.
    """
    def configFunctions(self):

        # first set functions for Agent
        from tpg.configuration.conf_agent import ConfAgent

        if self.functionsDict["init"] == "def":
            Agent.__init__ = ConfAgent.init_def

        if self.functionsDict["act"] == "def":
            Agent.act = ConfAgent.act_def

        if self.functionsDict["reward"] == "def":
            Agent.reward = ConfAgent.reward_def

        if self.functionsDict["taskDone"] == "def":
            Agent.taskDone = ConfAgent.taskDone_def

        if self.functionsDict["saveToFile"] == "def":
            Agent.saveToFile = ConfAgent.saveToFile_def

        # then set functions for other classes
        from tpg.action_object import ActionObject
        from tpg.program import Program
        from tpg.learner import Learner
        from tpg.team import Team

    """
    Ensures proper functions are used in this class as set up by configurer.
    """
    @classmethod
    def configFunctions(cls, functionsDict):
        from tpg.configuration.conf_agent import ConfAgent

        if functionsDict["init"] == "def":
            cls.__init__ = ConfAgent.init_def

        if functionsDict["act"] == "def":
            cls.act = ConfAgent.act_def

        if functionsDict["reward"] == "def":
            cls.reward = ConfAgent.reward_def

        if functionsDict["taskDone"] == "def":
            cls.taskDone = ConfAgent.taskDone_def

        if functionsDict["saveToFile"] == "def":
            cls.saveToFile = ConfAgent.saveToFile_def

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
