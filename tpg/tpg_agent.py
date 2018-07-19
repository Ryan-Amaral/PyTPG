"""
Class the the client gets an instance of to control a team.
"""
class TpgAgent:

    from team import Team
    from tpg_trainer import TpgTrainer

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
        (Int) The action to perform.
    """
    def act(self, obs, valActs=None, defAct=0L, mem=False):
        regDict = None
        if mem:
            regDict = self.regDict

        action = self.team.getAction(obs, regDict=regDict)
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
        task  :
            (Str) The task the reward is for.
        reward:
            (Float) The final reward value.
    """
    def reward(self, task, reward):
        self.team.outcomes[task] = reward # track reward for task on team
        if self.trainer is not None:
            self.trainer.addTask(task)
