# tpg-python
A python implementation of Tangled Program Graphs. A graph based genetic programming algorithm.

## Recent API changes
**Trainer Parameters:** rTeamPopSize removed, just use teamPopSize and use the rootBasedPop parameter (boolean) to affect whether the population is based on all teams or just root teams.

## Setup

### Requirements (automatically installed with with PyTPG)
- numba
- numpy

### Installing PyTPG
- clone this repo
- install with `pip install -e .`

## How to use
We will go over basic usage here. For more examples and details go to [the examples page](./tpg_examples.ipynb).

For practically all uses, you must import [Trainer](./tpg/trainer.py) and [Agent](./tpg/agent.py).

```python
from tpg.trainer import Trainer
from tpg.agent import Agent
```

**Trainer** is the class used for training, to do all the standard tasks of an evolutionary algorithm. Such as getting individuals, evolving, and reporting stats. **Agent** is essentially a wrapper for an individual of the population that the user (you) gets access to. Its API allows for things like selecting an action based on the world state, and giving a reward.

Create an instance of the trainer, which initializes the necessary populations for the algorithm. There are many parameters to choose for the initializer, `actions` is the only required one, which is a list of actions available to you from the chosen environment, or an int representing the number of continuous action ranging from
0-1.

```python
trainer = Trainer(actions=range(7))
```

Withdraw the agents from the population to be used in some task.

```python
agents = trainer.getAgents()
```

Some agent can act on the current state of the environment by the act method.

```python
action = agent.act(state) # call every timestep
```

TPG works with final score only (for now), so track the score of whatever environment is being used, and reward it to the agent after the episode.

```python
agent.reward(score, environmentName)
```

After all agents performed, call evolution on the trainer, and repeat for next generation if desired. `environmentName` must be in a list because there is support for multiple environments/tasks to consider when evolving.

```python
trainer.evolve([environmentName])
```

### Other ways to use
The above were just some of the important functions, and left out some necessary code for the environment, and a few other ways to use this API (some perhaps better). There are different ways to do things like withdrawing agents, rewarding agents, and evolving. And things become a bit tricky if you wish to work with multiprocessing, but its relatively straight forward to make it work. See [the examples page](./tpg_examples.ipynb) for details.

# Docker 

Use the following command to run PyTPG as a standalone docker container

```
sudo docker run --hostname <host> -d nimslab/tpg-v2:latest "<environment-name>" <generations> <episodes> <max frames> <threads> <teamStartPop> <useMemory> <traversalType> "<results path>" <outputName> "<ms graph config path>" "<email list path>"
```
Example:
```
sudo docker run --hostname harry-docker -d nimslab/tpg-v2:latest "Boxing-v0" 25 1 18000 40 600 true team "./harry25test/" harry_tpg_boxing_25 "conf.json" "notify.json"
```

# MS Graph Integration
PyTPG will automatically upload results to your one drive account and send email notifications to desired addresses. 

To use this feature provide an json config file with the following:

```
{
    "authority":"<your_authority_uri>",
    "client_id":"<your_client_id>",
    "scope":["https://graph.microsoft.com/.default"],
    "secret":"<client secret>",
    "endpoint":"https://graph.microsoft.com/v1.0/users",
    "tenant_id":"<your_tenant_id>",
    "drive_id":"<your_drive_id>",
    "tpg_runs_folder_id":"<folder_id_on_onedrive_where_you_want_your_results>",
    "user_id":"<user_principle_from_whom_email_notifications_will_be_sent>"
}
```

Additionally provide the list of people you'd like notified in a json file like this:

```
["email@example.com","importantFellow@gmail.com"]
```

PyTPG must be registered as a Daemon Application in your Active Directory, for more info see:
- https://docs.microsoft.com/en-us/azure/active-directory/develop/authentication-flows-app-scenarios#scenarios-and-supported-authentication-flows
- https://docs.microsoft.com/en-us/azure/active-directory/develop/scenario-daemon-overview

PyTPG uses the Microsoft Graph API to achieve this functionality, for more info on that, and to play around with Microsoft Graph checkout:

https://developer.microsoft.com/en-us/graph/graph-explorer/preview



## TODO
- Implement a sort of memory module with some learners reading and some writing.
- Add convenience code to the utils file, such a simple method to run an agent in a gym environment with certain parameters, a method to transform the state, etc.

## Some Projects PyTPG was Used in
- https://github.com/Ryan-Amaral/general-game-playing-tpg (old API version)
- https://github.com/Ryan-Amaral/prosthetic-challenge-tpg (old API version)
- https://github.com/Ryan-Amaral/nips-l2m-2019 (private untill competition end)
- Send me a message or a pull request for your projects to be included.

## Other TPG implementations:
- https://github.com/skellco/Tangled-Program-Graphs
- https://github.com/LivinBreezy/TPG-J

## Aknowledgements
- Dr. Malcolm Heywood: My undergrad and Masters research supervisor.
- Robert Smith: Provided an initial Java implementation of TPG, whiched I based this version on.
- [Richard Wardin](https://github.com/Shalmezad): Helped fix a few bugs in early development.
