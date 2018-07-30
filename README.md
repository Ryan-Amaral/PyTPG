# tpg-python
A python implementation of Tangled Program Graphs.

## Setup

### Requirements
- bitarray: [PyPI](https://pypi.org/project/bitarray/), [Anaconda](https://anaconda.org/anaconda/bitarray).

### Installing PyTPG
- clone this repo
- install with `pip install -e .`

## How to use
I will describe basic usage here. For more examples and details go to [the examples page](./tpg_examples.ipynb).

For practically all uses, you must import [TpgTrainer](./tpg/tpg_trainer.py) and [TpgAgent](./tpg/tpg_agent.py).

```python
from tpg.tpg_trainer import TpgTrainer
from tpg.tpg_agent import TpgAgent
```

**TpgTrainer** is the class used for training, to do all the standard tasks of an evolutionary algorithm. Such as getting individuals, evolving, and reporting stats. **TpgAgent** is essentially a wrapper for an individual of the population that the user (you) gets access to. Its API allows for things like selecting an action based on the world state, and giving a reward.

Create an instance of the trainer, which initialized the necessary populations for the algorithms. There are many parameters to choose for the initializer. `actions` is the only required one, which is the number of actions available to you from the chosen environment.

```python
trainer = TpgTrainer(actions=range(7))
```

Withdraw an agent from the population to be used in some task.

```python
agent = trainer.getNextAgent()
```

The agent can act on the current state of the environment by the act method.

```python
action = agent.act(state) # call every timestep
```

TPG works with final score only (for now), so track the score of whatever environment is being used and, reward it to the agent after the episode.

```python
agent.reward(score)
```

After all agents went, perform evolution on the trainer, and repeat for next generation if desired.

```python
trainer.evolve()
```

### Other ways to use
The above were just some of the important functions, and left out some necessary code for the environment, and a few other small details. There are different ways to do things like withdrawing agents, rewarding agents, and evolving. And things become a bit tricky if you wish to work with multiprocessing, but we have some example workarounds for such things to make it work. See [the examples page](./tpg_examples.ipynb) for details.

## Aknowledgements
- Dr. Malcolm Heywood: My supervisor on the (current) summer I learned about TPG.
- Robert Smith: Provided an initial Java implementation of TPG.

## Other implementations:
- https://github.com/skellco/Tangled-Program-Graphs
- Based on a yet unreleased Java version created by Robert Smith.
