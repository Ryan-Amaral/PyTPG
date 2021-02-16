
import multiprocessing as mp
import os
import time
from multiprocessing import set_start_method
import inspect
import math

import gym
import numpy as np

from tpg.trainer import Trainer
from tpg.utils import getLearners, getTeams, learnerInstructionStats, actionInstructionStats, pathDepths

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
    try:
        agent = args[0] # the agent
        envName = args[1] # name of OpenAI environment
        scoreList = args[2] # track scores of all agents
        numEpisodes = args[3] # number of times to repeat game
        numFrames = args[4] # frames to play for
        nRandFrames = args[5]
        do_real = args[6]
        
        agent.configFunctionsSelf()

        # skip if task already done by agent
        if agent.taskDone(envName):
            print('Agent #' + str(agent.agentNum) + ' can skip.')
            scoreList.append((agent.team.id, agent.team.outcomes))
            return

        env = gym.make(envName)
        valActs = range(env.action_space.n) # valid actions, some envs are less
        acts = env.action_space.n


        scoreTotal = 0 # score accumulates over all episodes

        if do_real:
            for ep in range(numEpisodes): # episode loop
                state = env.reset()
                scoreEp = 0
                for i in range(numFrames): # frame loop
                    if i < nRandFrames:
                        env.step(env.action_space.sample())
                        continue

                    act = agent.act(getStateALE(np.array(state, dtype=np.int32)))
                    act = int(math.floor(act[1]) % acts)
                    #print(act)

                    # feedback from env
                    state, reward, isDone, debug = env.step(act)
                    scoreEp += reward # accumulate reward in score
                    if isDone:
                        break # end early if losing state

                print('Agent #' + str(agent.agentNum) +
                    ' | Ep #' + str(ep) + ' | Score: ' + str(scoreEp))
                scoreTotal += scoreEp
        else:
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
                    #' | Ep #' + str(ep) + ' | Score: ' + str(scoreEp))
                scoreTotal += scoreEp

        scoreTotal /= numEpisodes
        env.close()
        agent.reward(scoreTotal, envName)
        scoreList.append((agent.team.id, agent.team.outcomes))

    except Exception as playException:
        print("Exception occured while Agent {} was playing {}".format(args[0].agentNum, args[1] ))
        raise playException
"""
Uses the runAgentParallel function to run a whole population of TPG agents
for however many generations on the supplied environmental parameters.
On an OpenAI gym environment.
"""
def runPopulationParallel(envName="Boxing-v0", gens=1000, popSize=360, reps=3,
        frames=18000, processes=4, nRandFrames=30, rootBasedPop=True,
        memType=None, operationSet="full", rampancy=(5,5,5), traversal="team",
        do_real=False):
    tStart = time.time()

    '''
    Python really is something special... sometimes it just deadlocks...¯\_(ツ)_/¯
    https://pythonspeed.com/articles/python-multiprocessing/
    '''
    set_start_method("spawn")

    print("creating atari environment")
    # get num actions
    env = gym.make(envName)
    acts = env.action_space.n
    del env

    print("creating trainer")
    if do_real:
        trainer = Trainer(actions=[1,1], teamPopSize=popSize, rootBasedPop=rootBasedPop,
            memType=memType, operationSet=operationSet, rampancy=rampancy,
            traversal=traversal)
    else:
        trainer = Trainer(actions=acts, teamPopSize=popSize, rootBasedPop=rootBasedPop,
            memType=memType, operationSet=operationSet, rampancy=rampancy,
            traversal=traversal)

    trainer.configFunctions()
    #print(1/0)

    man = mp.Manager()
    pool = mp.Pool(processes=processes, maxtasksperchild=1)

    allScores = [] # track all scores each generation

    print("running generations")
    for gen in range(gens): # do generations of training
        print("doing generation {}".format(gen))
        scoreList = man.list()

        agents = trainer.getAgents() # swap out agents only at start of generation
        agent = agents[0]

        try:
            
            # run the agents
            pool.map(runAgentParallel,
                [(agent, envName, scoreList, reps, frames, nRandFrames, do_real)
                for agent in agents]
            )


        except Exception as mpException:
            print("Exception occured while running multiprocessing via pool.map!")
            print(mpException)
            raise mpException

        # prepare population for next gen
        print("Applying gen {} scores to agents".format(gen))
        teams = trainer.applyScores(scoreList)
        print("Getting champion")
        champ = trainer.getAgents(sortTasks=[envName])[0].team
        print("Evolving population")
        trainer.evolve(tasks=[envName]) # go into next gen

        # track stats
        scoreStats = trainer.fitnessStats
        allScores.append((scoreStats['min'], scoreStats['max'], scoreStats['average']))

        #print('Time Taken (Hours): ' + str((time.time() - tStart)/3600))
        #print('Gen: ' + str(gen))
        #print('Results so far: ' + str(allScores))

        print("teams: {}, rTeams: {}, learners: {}, Champ Teams: {}, Champ Learners: {}, Champ Instructions: {}."
            .format(len(trainer.teams), len(trainer.rootTeams), len(trainer.learners),
                len(getTeams(champ)), len(getLearners(champ)), learnerInstructionStats(getLearners(champ), trainer.operations)))
        #print(actionInstructionStats(getLearners(champ), trainer.operations))
        #print(1/0)

        print(f"Gen: {gen}, Best Score: {scoreStats['max']}, Avg Score: {scoreStats['average']}, Time: {str((time.time() - tStart)/3600)}")
        

    print(pathDepths(champ))

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

    trainer = Trainer(actions=acts, teamPopSize=popSize, memType=None,
        operationSet="full", rampancy=(5,5,10), traversal="learner")

    tStart = time.time()

    allScores = [] # track scores per gen
    for gen in range(gens): # do generations of training
        agents = trainer.getAgents()

        while True: # loop through agents of current generation
            if len(agents) == 0:
                break

            agent = agents.pop()
            team = agent.team
            #print("in runPopulation!")
            #print(inspect.getsource(team.act))
            #print(1/0)
            
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


if __name__ == "__main__":
    runPopulationParallel(envName="BankHeist-v0", do_real=False, popSize=360, memType=None, gens=1000, reps=5, processes=23)
