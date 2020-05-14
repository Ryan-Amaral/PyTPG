import time
import numpy as np
import gym
import random
from pathlib import Path
import multiprocessing as mp

from tpg.trainer import Trainer
from tpg.trainer import loadTrainer
from tpg.agent import Agent

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
            if i < numRandFrames:
                env.step(env.action_space.sample())
                continue

            act = agent.act(getState(np.array(state, dtype=np.int32)))

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
        trainer = Trainer(actions=range(numActions), teamPopSize=runInfo['teamPopulationSize'], rTeamPopSize=runInfo['teamPopulationSize'], sharedMemory=runInfo['useMemory'])

    man = mp.Manager()
    pool = mp.Pool(processes=runInfo['numThreads'], maxtasksperchild=1)

    allScores = [] #Track all scores each generation

    for gen in range(runInfo['maxGenerations']): #do maxGenerations of training
        scoreList = man.list()

        # get agents, noRef to not hold reference to trainer in each one
        # don't need reference to trainer in multiprocessing
        agents = trainer.getAgents()

        #run the agents
        pool.map(runAgent,
            [(agent, runInfo['environmentName'], scoreList, runInfo['episodes'], runInfo['numFrames'])
            for agent in agents])

        # apply scores, must do this when multiprocessing
        # because agents can't refer to trainer
        teams = trainer.applyScores(scoreList)


        '''
        Gather statistics 
        '''
        # Total learners in that root team
        learnerCount = len(trainer.getAgents(sortTasks=[runInfo['environmentName']])[0].team.learners)

         #Total instructions in the best root team
        instructionCount = 0
        allOperations = []
        addOperations = 0
        subtractOperations = 0
        multiplyOperations = 0
        divideOperations = 0
        negOperations = 0
        memReadOperations = 0
        memWriteOperations = 0
        learners = []

        #Collect instruction info!
        trainer.getAgents(sortTasks=[runInfo['environmentName']])[0].team.compileLearnerStats(
            learners,
            allOperations,
            addOperations,
            subtractOperations, 
            multiplyOperations,
            divideOperations,
            negOperations, 
            memReadOperations,
            memWriteOperations
            )
                    
            
        teams = []
        trainer.getAgents(sortTasks=[runInfo['environmentName']])[0].team.size(teams)
        print("root team size: " + str(len(teams)))

        #Save best root team each generation
        Path(runInfo['resultsPath']+"teams/").mkdir(parents=True, exist_ok=True)
        trainer.getAgents(sortTasks=[runInfo['environmentName']])[0].saveToFile(runInfo['resultsPath'] + "teams/root_team_gen_" + str(gen))

        #Save the trainer as a 'checkpoint' should we want to restart the run from this generation
        Path(runInfo['resultsPath']+"trainers/").mkdir(parents=True, exist_ok=True)
        trainer.saveToFile(runInfo['resultsPath']+"trainers/gen_" + str(gen))

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
        str(learnerCount) + "," +
        str(len(teams)) + "," + 
        str(instructionCount) + "," +
        str(addOperations) + "," +
        str(subtractOperations) + "," +
        str(multiplyOperations) + "," +
        str(divideOperations) + "," + 
        str(negOperations) + "," +
        str(memReadOperations) + "," +
        str(memWriteOperations) + "\n"
        )
        runStatsFile.close()

    #Return scores and trainer for additional metrics post-run
    return allScores, trainer
