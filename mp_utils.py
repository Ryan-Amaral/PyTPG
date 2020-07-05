import time
import numpy as np
import gym
import random
from pathlib import Path
import multiprocessing as mp
import matplotlib.pyplot as plt
import pandas as pd
import math

from tpg.trainer import Trainer
from tpg.trainer import loadTrainer
from tpg.agent import Agent
from tpg.program import Program

from ms_graph_utils import processPartialResults
from graph_utils import generateGraphs

# To transform pixel matrix to a single vector.
def getState(inState):
    # each row is all 1 color
    rgbRows = np.reshape(inState,(len(inState[0])*len(inState), 3)).T

    # add each with appropriate shifting
    # get RRRRRRRR GGGGGGGG BBBBBBBB
    return np.add(np.left_shift(rgbRows[0], 16),
        np.add(np.left_shift(rgbRows[1], 8), rgbRows[2]))

"""
Run each agent in this method for parallization.
Args:
    args: (TpgAgent, envName, scoreList, numEpisodes, numFrames)
"""
def runAgent(args):
    agent = args[0]
    envName = args[1]
    scoreList = args[2]
    numEpisodes = args[3] # number of times to repeat game
    numFrames = args[4]
    mode = args[5] # whether to run in train or test (random skip 30 frames @start) mode

    # skip if task already done by agent
    if agent.taskDone(envName):
        print('Agent #' + str(agent.agentNum) + ' can skip.')
        scoreList.append((agent.team.id, agent.team.outcomes))
        return

    env = gym.make(envName)
    valActs = range(env.action_space.n) # valid actions, some envs are less

    scoreTotal = 0 # score accumulates over all episodes
    for ep in range(numEpisodes): # episode loop
        state = env.reset()
        scoreEp = 0
        numRandFrames = 0
        if numEpisodes > 1:
            numRandFrames = random.randint(0,30)
        for i in range(numFrames): # frame loop
            if mode == 'test' and i < numRandFrames: # Only skip frame on start in test mode
                env.step(env.action_space.sample())
                continue

            act = agent.act(frameNumber=i,state=getState(np.array(state, dtype=np.int32)))[1][0]
            act = min(env.action_space.n - 1 , math.floor(act % env.action_space.n))

            # feedback from env
            state, reward, isDone, debug = env.step(act)
            scoreEp += reward # accumulate reward in score
            if isDone:
                break # end early if losing state

        print('Agent #' + str(agent.agentNum) +
              ' | Ep #' + str(ep) + ' | Score: ' + str(scoreEp))
        scoreTotal += scoreEp

    scoreTotal /= numEpisodes
    env.close()
    agent.reward(scoreTotal, envName)
    scoreList.append((agent.team.id, agent.team.outcomes))

def doRun(runInfo):

    #get num actions
    env = gym.make(runInfo['environmentName'])
    numActions = env.action_space.n
    del env


    # Load trainer if one was passed
    if runInfo['loadPath'] is not None:
        trainer = loadTrainer(runInfo['loadPath'])
    else:
        trainer = Trainer(actions=[1,1], teamPopSize=runInfo['teamPopulationSize'],
        sharedMemory=runInfo['useMemory'], traversal=runInfo['traversalType'])


    runInfo['trainer'] = trainer #Save the trainer for run details later
    man = mp.Manager()
    pool = mp.Pool(processes=runInfo['numThreads'], maxtasksperchild=1)

    allScores = [] #Track all scores each generation

    #Notify counter
    notifyCounter = 0 # Sends notifications with partial results every time it is 0.

    rangeStart = 0

    if runInfo['resumeGen'] != None:
        rangeStart = runInfo['resumeGen']
        print('resuming from gen ' + str(runInfo['resumeGen']))

    for gen in range(rangeStart,runInfo['maxGenerations'] + 1): #do maxGenerations of training, + 1 as it's exclusive
        scoreList = man.list()

        # get agents, noRef to not hold reference to trainer in each one
        # don't need reference to trainer in multiprocessing
        agents = trainer.getAgents()

        if runInfo['numThreads'] > 1:
            # run in parallel with multiprocessing pool

            #run the agents
            pool.map(runAgent,
                [(agent, runInfo['environmentName'], scoreList, runInfo['episodes'], runInfo['numFrames'], runInfo['mode'])
                for agent in agents])

            # apply scores, must do this when multiprocessing
            # because agents can't refer to trainer
            teams = trainer.applyScores(scoreList)
        else:
            # run one at a time in the current process
            for agent in agents:
                runAgent((agent, runInfo['environmentName'], scoreList, runInfo['episodes'], runInfo['numFrames'], runInfo['mode']))


        '''
        Gather statistics
        '''
        stats = {
            'learnerCount': len(trainer.getAgents(sortTasks=[runInfo['environmentName']])[0].team.learners),
            'instructionCount': 0,
            'add': 0,
            'subtract': 0,
            'multiply': 0,
            'divide': 0,
            'neg':0,
            'memRead':0,
            'memWrite':0,
        }

         #Total instructions in the best root team
        learners = set()

        #Collect instruction info!
        trainer.getAgents(sortTasks=[runInfo['environmentName']])[0].team.compileLearnerStats(
            learners,
            stats
            )


        teams = set()
        trainer.getAgents(sortTasks=[runInfo['environmentName']])[0].team.size(teams)
        print("root team size: " + str(len(teams)))

        #Save best root team each generation
        Path(runInfo['resultsPath']+"teams/").mkdir(parents=True, exist_ok=True)
        trainer.getAgents(sortTasks=[runInfo['environmentName']])[0].saveToFile(runInfo['resultsPath'] + "teams/root_team_gen_" + str(gen))

        #Save the trainer as a 'checkpoint' should we want to restart the run from this generation
        Path(runInfo['resultsPath']+"trainers/").mkdir(parents=True, exist_ok=True)
        runInfo['lastTrainerFile'] = "gen_" + str(gen)
        runInfo['lastTrainerPath'] = runInfo['resultsPath']+"trainers/"+runInfo['lastTrainerFile']
        trainer.saveToFile(runInfo['lastTrainerPath'])
        print(runInfo['lastTrainerPath'])

        # important to remember to set tasks right, unless not using task names
        # task name set in runAgent()
        trainer.evolve(tasks=[runInfo['environmentName']]) # go into next gen

        # an easier way to track stats than the above example
        scoreStats = trainer.fitnessStats
        allScores.append((scoreStats['min'], scoreStats['max'], scoreStats['average']))


        print('Time Taken (Hours): ' + str((time.time() - runInfo['tStart'])/3600))
        print('Gen: ' + str(gen))
        print('Results so far: ' + str(allScores))

        runStatsFile = open(runInfo['resultsPath'] + runInfo['runStatsFileName'],"a")

        runStatsFile.write(str(gen) + "," +
        str((time.time() - runInfo['tStart'])/3600) + "," +
        str(scoreStats['min']) + "," +
        str(scoreStats['max']) + "," +
        str(scoreStats['average']) + "," +
        str(len(learners)) + "," +
        str(len(teams)) + "," +
        str(stats['instructionCount']) + "," +
        str(stats['add']) + "," +
        str(stats['subtract']) + "," +
        str(stats['multiply']) + "," +
        str(stats['divide']) + "," +
        str(stats['neg']) + "," +
        str(stats['memRead']) + "," +
        str(stats['memWrite']) + "\n"
        )
        runStatsFile.flush()
        runStatsFile.close()

        if notifyCounter == 0:
            processPartialResults(runInfo, gen)

        notifyCounter += 1

        if notifyCounter == 250: #Notify every 250 gens
            notifyCounter = 0


    #Return scores and trainer for additional metrics post-run
    return allScores, trainer, runInfo['lastTrainerPath']

def writeRunInfo(runInfo):

    file = open(runInfo['resultsPath']+runInfo['runInfoFileName'], 'w')
    for i in runInfo:
        file.write(i + " = " + str(runInfo[i])+"\n")


    trainer = runInfo['trainer'] if 'trainer' in runInfo else None
    if trainer is not None:
        content = "Trainer Info\n"
        content +="teamPopSize = " + str(trainer.teamPopSize) + "\n"
        content +="rootBasedPop = "+ str(trainer.rootBasedPop) + "\n"
        content +="gap = " + str(trainer.gap) + "\n"
        content +="uniqueProgThresh = " + str(trainer.uniqueProgThresh) + "\n"
        content +="initMaxTeamSize = " + str(trainer.initMaxTeamSize) + "\n"
        content +="initMaxProgSize = " + str(trainer.initMaxProgSize) + "\n"
        content +="registerSize = " + str(trainer.registerSize) + "\n"
        content +="pDelLrn = " + str(trainer.pDelLrn) + "\n"
        content +="pAddLrn = " + str(trainer.pAddLrn) + "\n"
        content +="pMutLrn = " + str(trainer.pMutLrn) + "\n"
        content +="pMutProg = " + str(trainer.pMutProg) + "\n"
        content +="pMutAct = "+ str(trainer.pMutAct) + "\n"
        content +="pActAtom = "+ str(trainer.pActAtom) + "\n"
        content +="pDelInst = "+ str(trainer.pDelInst) + "\n"
        content +="pAddInst = "+ str(trainer.pAddInst) + "\n"
        content +="pSwpInst = " + str(trainer.pSwpInst) + "\n"
        content +="pMutInst = " + str(trainer.pMutInst) + "\n"
        content +="pSwapMutliAct = "+str(trainer.pSwapMultiAct ) + "\n"
        content +="pChangeMultiAct = "+ str(trainer.pChangeMultiAct) + "\n"
        content +="doElites = " + str(trainer.doElites) + "\n"
        content +="sourceRange = " + str(trainer.sourceRange) + "\n"
        content +="sharedMemory = "+ str(trainer.sharedMemory) + "\n"
        content +="memMatrixShape = "+ str(trainer.memMatrixShape) + "\n"
        content +="traversal = "+ str(trainer.traversal) + "\n"
        file.write(content)

    file.close()
