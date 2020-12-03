# tpg-python
A python implementation of Tangled Program Graphs. A graph based genetic programming algorithm.

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

**Trainer** is the class used for training, to do all the standard tasks of an evolutionary algorithm.
Such as getting individuals, evolving, and reporting stats.
**Agent** is essentially a wrapper for an individual of the population that the user (you) gets access to.
Its API allows for things like selecting an action based on the world state, and giving it a reward.

Create an instance of the trainer, which initializes the necessary populations for the algorithm.
There are many parameters to choose for the initializer, `actions` is the only required one, which is either an integer representing the number of discrete actions (e.g. Atari), or a list of integers representing the size of a real valued vector for each action (0 for discrete).

```python
# 7 different discrete actions
trainer = Trainer(actions=7)

### OR

# 3 different actions, 2 being real valued vectors of size 2, 1 being a single discrete action
trainer = Trainer(actions=[2,2,0])
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

The test files and `extras.py` file shows more examples, those files are used for testing.

## Testing
`coverage run --source=. -m xmlrunner tpg_tests/*_test.py`
`coverage html`

## Some Projects PyTPG was Used in
- https://github.com/Ryan-Amaral/general-game-playing-tpg (old API version)
- https://github.com/Ryan-Amaral/prosthetic-challenge-tpg (old API version)
- https://github.com/Ryan-Amaral/nips-l2m-2019

## Other TPG implementations:
- https://github.com/skellco/Tangled-Program-Graphs
- https://github.com/LivinBreezy/TPG-J

## Aknowledgements
- Dr. Malcolm Heywood: My undergrad and Masters research supervisor.
- Robert Smith: Provided an initial Java implementation of TPG, whiched I based this version on.
- [Richard Wardin](https://github.com/Shalmezad): Helped fix a few bugs in early development.
