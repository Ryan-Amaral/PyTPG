import numpy as np
import gym
import multiprocessing as mp
import time
from tpg.trainer import Trainer

"""
Transform visual input from ALE to flat vector.
inState should be made int32 before passing in.
"""
def getStateALE(inState):
    # each row is all 1 color
    rgbRows = np.reshape(inState,(len(inState[0])*len(inState), 3)).T

    # add each with appropriate shifting
    # get RRRRRRRR GGGGGGGG BBBBBBBB
    return np.add(np.left_shift(rgbRows[0], 16),
        np.add(np.left_shift(rgbRows[1], 8), rgbRows[2]))

"""
Run each agent in this method for parallization.
See example in tpg_examples.ipynb.
Args:
    args: (TpgAgent, envName, scoreList, numEpisodes, numFrames)
"""
def runAgentParallel(args):
    agent = args[0] # the agent
    envName = args[1] # name of OpenAI environment
    scoreList = args[2] # track scores of all agents
    numEpisodes = args[3] # number of times to repeat game
    numFrames = args[4] # frames to play for
    nRandFrames = args[5]

    # skip if task already done by agent
    if agent.taskDone(envName):
        #print('Agent #' + str(agent.agentNum) + ' can skip.')
        scoreList.append((agent.team.id, agent.team.outcomes))
        return

    env = gym.make(envName)
    valActs = range(env.action_space.n) # valid actions, some envs are less

    scoreTotal = 0 # score accumulates over all episodes
    for ep in range(numEpisodes): # episode loop
        state = env.reset()
        scoreEp = 0

        for i in range(numFrames): # frame loop
            if i < nRandFrames:
                env.step(env.action_space.sample())
                continue

            act = agent.act(getStateALE(np.array(state, dtype=np.int32)))

            # feedback from env
            state, reward, isDone, debug = env.step(act)
            scoreEp += reward # accumulate reward in score
            if isDone:
                break # end early if losing state

        #print('Agent #' + str(agent.agentNum) +
        #      ' | Ep #' + str(ep) + ' | Score: ' + str(scoreEp))
        scoreTotal += scoreEp

    scoreTotal /= numEpisodes
    env.close()
    agent.reward(scoreTotal, envName)
    scoreList.append((agent.team.id, agent.team.outcomes))

"""
Uses the runAgentParallel function to run a whole population of TPG agents
for however many generations on the supplied environmental parameters.
On an OpenAI gym environment.
"""
def runPopulationParallel(envName="Boxing-v0", gens=1000, popSize=360, reps=3,
        frames=18000, processes=4, nRandFrames=30):
    tStart = time.time()

    # get num actions
    env = gym.make(envName)
    acts = env.action_space.n
    del env

    trainer = Trainer(actions=range(acts), teamPopSize=popSize)

    man = mp.Manager()
    pool = mp.Pool(processes=processes, maxtasksperchild=1)

    allScores = [] # track all scores each generation

    for gen in range(gens): # do generations of training
        scoreList = man.list()

        agents = trainer.getAgents() # swap out agents only at start of generation

        # run the agents
        pool.map(runAgentParallel,
            [(agent, envName, scoreList, reps, frames, nRandFrames)
            for agent in agents])

        # prepare population for next gen
        teams = trainer.applyScores(scoreList)
        trainer.evolve(tasks=[envName]) # go into next gen

        # track stats
        scoreStats = trainer.fitnessStats
        allScores.append((scoreStats['min'], scoreStats['max'], scoreStats['average']))

        #print('Time Taken (Hours): ' + str((time.time() - tStart)/3600))
        #print('Gen: ' + str(gen))
        #print('Results so far: ' + str(allScores))
        print(f"Gen: {gen}, Best Score: {scoreStats['max']}, Time: {str((time.time() - tStart)/3600)}")

    print('Time Taken (Hours): ' + str((time.time() - tStart)/3600))
    print('Results:\nMin, Max, Avg')
    for score in allScores:
        print(score[0],score[1],score[2])

    return trainer, allScores[-1]

def runPopulation(envName="Boxing-v0", gens=1000, popSize=360, reps=3,
        frames=18000, nRandFrames=30):
    # get num actions
    env = gym.make(envName)
    acts = env.action_space.n

    trainer = Trainer(actions=range(acts), teamPopSize=popSize)

    tStart = time.time()

    allScores = [] # track scores per gen
    for gen in range(gens): # do generations of training
        agents = trainer.getAgents()

        while True: # loop through agents of current generation
            if len(agents) == 0:
                break

            agent = agents.pop()
            if agent.taskDone(envName):
                continue

            score = 0
            for i in range(reps): # repetitions of game
                state = env.reset()
                for j in range(frames): # frames of game
                    # start random for stochasticity
                    if j < nRandFrames:
                        state, reward, isDone, debug = env.step(env.action_space.sample())
                        continue

                    act = agent.act(getStateALE(np.array(state, dtype=np.int32)))
                    state, reward, isDone, debug = env.step(act)

                    score += reward # accumulate reward in score
                    if isDone:
                        break # end early if losing state

            agent.reward(score/reps, envName)

            print('Agent #' + str(agent.agentNum) +
                ' | Score: ' + str(score/reps))

        # current generation done
        trainer.evolve(tasks=[envName])

        # track stats
        scoreStats = trainer.fitnessStats
        allScores.append((scoreStats['min'], scoreStats['max'], scoreStats['average']))

        print('Time Taken (Hours): ' + str((time.time() - tStart)/3600))
        print('Gen: ' + str(gen))
        print('Results so far: ' + str(allScores))

    print('Time Taken (Hours): ' + str((time.time() - tStart)/3600))
    print('Results:\nMin, Max, Avg')
    for score in allScores:
        print(score[0],score[1],score[2])

    return trainer, allScores[-1]
