#Import libraries
import time
import sys
import random
import numpy as np
import gym
import multiprocessing as mp

#Import tpg
from tpg.util.mp_utils import runAgent
from tpg.trainer import Trainer
from tpg.agent import Agent

from tpg.memory.memory_trainer import Trainer as mTrainer
from tpg.memory.memory_agent import Agent as mAgent

#Start timestmap
tStart = time.time()

#Read program arguments
if len(sys.argv) > 1:
    environmentName = sys.argv[1]
    maxGenerations = sys.argv[2]
    episodes = sys.argv[3]
    numFrames = sys.argv[4]
    numThreads = sys.argv[5]
    teamPopulationSize = sys.argv[6]
    useMemory = sys.argv[7]
    traversalType = sys.argv[8]
    resultsPath = sys.argv[9]
    msGraphConfigPath = sys.argv[10]
    loadAgentPath = sys.argv[11]
else:
    print("python run_mp.py <environmentName> <maxGenerations> <episodes> <numFrames> <numThreads> <teamPopulationSize> <useMemory> <traversalType> <resultsPath> <msGraphConfigPath> <loadAgentPath>")

print("Starting run with args:")
print("environmentName = " + environmentName)
print("maxGenerations = " + maxGenerations)
print("episodes = " + episodes)
print("numFrames = " + numFrames)
print("threads = " + numThreads)
print("teamPopulationSize = " + teamPopulationSize)
print("useMemory = " + useMemory)
print("traversalType = " + traversalType)
print("resultsPath = " + resultsPath)
print("msGraphConfigPath = " + msGraphConfigPath)
print("loadAgentPath = " + loadAgentPath)

#Setup output files
# RunInfo.txt - Program arguments, loaded configurations, implicit configurations
# RunStats.csv - Stats of interest collected during the generation loop
# RunFitnessStats.csv - Fitness scores of the generations, collected after the generation loop
# FinalRootTeamsFitness.csv - Fitness each team in the root team after the run is complete. 
runInfoFile = open(resultsPath + "RunInfo.txt", "w")
#TODO - print Program arguments, loaded configurations, implicit configurations. Don't print sensitive garbage!!
runInfoFile.close()

runStatsFile = open(resultsPath + "RunStats.csv", "a")
runStatsFile.write("Generation #, time taken, min fitness, max fitness, avg fitness, # of learners, # of teams in root team, # of instructions, add, sub, mult, div, neg, memRead, memWrite \n")
runStatsFile.close()

finalRootTeamsFitnessFile = open(resultsPath + "FinalRootTeamsFitness.csv","a")
finalRootTeamsFitnessFile.write("team id, fitness \n")
finalRootTeamsFitnessFile.close()

allScores, trainer = doRun(environmentName, maxGenerations, teamPopulationSize, episodes, numFrames, resultsPath)

print('Time Taken (Hours): ' + str((time.time() - tStart)/3600))
print('Results:\nMin, Max, Avg')
for score in allScores:
    print(score[0],score[1],score[2])

# I want to see the fitness scores of the final root teams plotted from highest to lowest.
finalRootFitnessFile = open("final_root_team_fitness.txt", "a")
for rt in trainer.rootTeams:
    if rt.fitness is not None:
        finalRootFitnessFile.write(str(rt.id) + "," + str(rt.fitness) + '\n')
finalRootFitnessFile.close()


def doRun(environmentName, maxGenerations, teamPopulationSize, episodes, numFrames, resultsPath):

    #get num actions
    env = gym.make(environmentName)
    numActions = env.action_space.n
    del env

    trainer = Trainer(actions=range(numActions), teamPopSize=teamPopulationSize, rTeamPopSize=teamPopulationSize)

    man = mp.Manager
    pool = mp.Pool(processes=numThreads, maxtasksperchild=1)

    allScores = [] #Track all scores each generation

    for gen in range(maxGenerations): #do maxGenerations of training
        scoreList = man.list()

        # get agents, noRef to not hold reference to trainer in each one
        # don't need reference to trainer in multiprocessing
        agents = trainer.getAgents()

        #run the agents
        pool.map(runAgent,
            [(agent, environmentName, scoreList, episodes, numFrames)
            for agent in agents])

        # apply scores, must do this when multiprocessing
        # because agents can't refer to trainer
        teams = trainer.applyScores(scoreList)


        '''
        Gather statistics 
        '''
        # Total learners in that root team
        learnerCount = len(trainer.getAgents(sortTasks=[environmentName])[0].team.learners)

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
        for learner in trainer.getAgents(sortTasks=[environmentName])[0].team.learners:
            instructionCount += len(learner.program.instructions)
            print(str(learner.program.operations))
            for value in learner.program.operations:
                allOperations.append(value)
                if value == 0:
                    addOperations += 1
                elif value == 1:
                    subtractOperations += 1
                elif value == 2:
                    multiplyOperations += 1
                elif value == 3:
                    divideOperations += 1
                elif value == 7:
                    negOperations += 1
                elif value == 8:
                    memReadOperations += 1
                elif value == 9:
                    memWriteOperations += 1
                    
            
        teams = []
        trainer.getAgents(sortTasks=[environmentName])[0].team.size(teams)
        print("root team size: " + str(len(teams)))


        # important to remember to set tasks right, unless not using task names
        # task name set in runAgent()
        trainer.evolve(tasks=[environmentName]) # go into next gen
        
        # an easier way to track stats than the above example
        scoreStats = trainer.fitnessStats
        allScores.append((scoreStats['min'], scoreStats['max'], scoreStats['average']))
        
       
        print('Time Taken (Hours): ' + str((time.time() - tStart)/3600))
        print('Gen: ' + str(gen))
        print('Results so far: ' + str(allScores))

        runStatsFile = open(resultsPath + "RunStats.csv","a")
        
        runStatsFile.write(str(gen) + "," +
        str((time.time() - tStart)/3600) + "," + 
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
