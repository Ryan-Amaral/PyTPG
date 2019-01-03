from tpg.team import Team

"""
Class that the client gets an instance of to control a team. Essentially just a
convenient wrapper around a (root) team.
"""
class TpgAgent:

    defTaskName = 'DefTaskName'

    """
    Creates an agent (what the client interfaces with), links to trainer if
    currently doing training.
    Args:
        team: (Team)
        trainer: (TpgTrainer) Only pass in if training.
    """
    def __init__(self, team, trainer=None):
        self.team = team
        self.trainer = trainer
        self.regDict = {}
        self.teamEnvVis = {} # times that team is visited in env
        self.teamVis = {} # times each team is visited, env not yet known
        self.envActions = {} # number of each action made in envs
        self.curEnvActions = {} # number of each action made in current env
        self.screenIndexed = None

    """
    Chooses an action to perform from the team based on the input space.
    Restricts actions to those deemed valid by providing validActions.
    Args:
        obs:
            (Float[]) The observation space. If None, action will be
            essentially random.
        valActs:
            (Int[]) Should be some subset of all actions that were
            initially provided to TPG, incase sub-environments have
            different action spaces. If None, the outputted action is
            not checked.
        defAct:
            (Int) Default action to perform if valid action not chosen
            by team.
        mem:
            (Bool) Use memory by maintaining registers.
    Returns:
        (Int or Float[]) The action to perform.
    """
    def act(self, obs, valActs=None, defAct=0, mem=False):
        regDict = None
        if mem:
            regDict = self.regDict

        if self.screenIndexed is None:
            self.screenIndexed = [0]*len(obs)

        vis = set() # teams visited
        action = self.team.getAction(obs, regDict=regDict, vis=vis, si=self.screenIndexed)

        for team in vis:
            if team not in self.teamVis:
                self.teamVis[team] = 1
            else:
                self.teamVis[team] += 1

        if action not in self.curEnvActions:
            self.curEnvActions[action] = 1
        else:
            self.curEnvActions[action] += 1

        if valActs is None:
            return action
        else:
            for act in valActs:
                if action == act:
                    return action

        return defAct # action from team not valid

    """
    Gives the team the reward amount at a certain tasks. Does not increment,
    only gives/overwrites final reward.
    Args:
        reward:
            (Float) The final reward value.
        task  :
            (Str) The task the reward is for. Leave as none for default value.
    """
    def reward(self, reward, task=None):
        if task is None:
            task = TpgAgent.defTaskName
        self.team.outcomes[task] = reward # track reward for task on team
        if self.trainer is not None:
            self.trainer.addTask(task)

        ###
        # all diagnostic stuff bellow
        for team in self.teamVis:
            if team not in self.teamEnvVis:
                self.teamEnvVis[team] = {} # new dictionary of team env visits

            if task not in self.teamEnvVis[team]:
                self.teamEnvVis[team][task] = self.teamVis[team]
            else:
                self.teamEnvVis[team][task] += self.teamVis[team]

        if task not in self.envActions:
            self.envActions[task] = self.curEnvActions
        else:
            for action in self.curEnvActions:
                if action not in self.envActions[task]:
                    self.envActions[task][action] = self.curEnvActions[action]
                else:
                    self.envActions[task][action] += self.curEnvActions[action]

        self.team.teamsEnvsVis = self.teamEnvVis
        self.team.envsActions = self.envActions

        self.teamVis = {}
        self.curEnvActions = {}

    """
    Gets Number of this agent from it's team, unique within generation.
    """
    def getAgentNum(self):
        return self.team.rootNum

    """
    Returns the UID of this agent's team.
    """
    def getUid(self):
        return self.team.uid

    """
    Returns boolean telling whether this agent completed the task already.
    Args:
        task  :
            (Str) The task to check for. Leave as none for default value.
    """
    def taskDone(self, task=None):
        if task is None:
            task = TpgAgent.defTaskName
        return task in self.team.outcomes

    """
    Gets the score/outcome of the specified task.
    Args:
        task  :
            (Str) The task to check for. Leave as none for default value.
    Returns:
        (Int) The score, or None if agent didn't do task.
    """
    def getOutcome(self, task=None):
        if task is None:
            task = TpgAgent.defTaskName

        if task in self.team.outcomes:
            return self.team.outcomes[task]
        else:
            return None

    """
    Returns the agent's team's outcomes dict.
    """
    def getOutcomes(self):
        return self.team.outcomes
