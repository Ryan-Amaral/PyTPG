#Import libraries
import time
import sys
import random
import numpy as np
from distutils import util
from pathlib import Path
import msal

#Import tpg
from tpg.util.mp_utils import doRun
from tpg.util.mp_utils import runAgent 
from tpg.trainer import Trainer
from tpg.agent import Agent
import json
 



#Read program arguments
if len(sys.argv) > 1:
    environmentName = sys.argv[1]
    maxGenerations = int(sys.argv[2])
    episodes = int(sys.argv[3])
    numFrames = int(sys.argv[4])
    numThreads = int(sys.argv[5])
    teamPopulationSize = int(sys.argv[6])
    useMemory = bool(util.strtobool(sys.argv[7]))
    traversalType = sys.argv[8]
    resultsPath = sys.argv[9]
    msGraphConfigPath = sys.argv[10]
    if len(sys.argv) > 11:
        loadPath = sys.argv[11]
    else:
        loadPath = None
else:
    print("python run_mp.py <environmentName> <maxGenerations> <episodes> <numFrames> <numThreads> <teamPopulationSize> <useMemory> <traversalType> <resultsPath> <msGraphConfigPath> <loadPath>")
    sys.exit()

config = json.load(open(msGraphConfigPath))

# Create a preferably long-lived app instance that maintains a token cache.
app = msal.ConfidentialClientApplication(
    config["client_id"], authority=config["authority"],
    client_credential=config["secret"],
    # token_cache=...  # Default cache is in memory only.
                       # You can learn how to use SerializableTokenCache from
                       # https://msal-python.rtfd.io/en/latest/#msal.SerializableTokenCache
    )

print("Starting run with args:")
print("environmentName = " + environmentName)
print("maxGenerations = " + str(maxGenerations))
print("episodes = " + str(episodes))
print("numFrames = " + str(numFrames))
print("threads = " + str(numThreads))
print("teamPopulationSize = " + str(teamPopulationSize))
print("useMemory = " + str(useMemory))
print("traversalType = " + str(traversalType))
print("resultsPath = " + str(resultsPath))
print("msGraphConfigPath = " + str(msGraphConfigPath))
print("loadPath = " + str(loadPath))

#Start timestmap
tStart = time.time()

# Setup output files

# Create results path if it doesn't exist
Path(resultsPath).mkdir(parents=True, exist_ok=True) 

# RunInfo.txt - Program arguments, loaded configurations, implicit configurations
# RunStats.csv - Stats of interest collected during the generation loop
# RunFitnessStats.csv - Fitness scores of the generations, collected after the generation loop
# FinalRootTeamsFitness.csv - Fitness each team in the root team after the run is complete. 
runInfoFile = open(resultsPath + "RunInfo.txt", "a")
#TODO - print Program arguments, loaded configurations, implicit configurations. Don't print sensitive garbage!!
runInfoFile.close()

runStatsFile = open(resultsPath + "RunStats.csv", "a")
runStatsFile.write("Generation #, time taken, min fitness, max fitness, avg fitness, # of learners, # of teams in root team, # of instructions, add, sub, mult, div, neg, memRead, memWrite \n")
runStatsFile.close()

finalRootTeamsFitnessFile = open(resultsPath + "FinalRootTeamsFitness.csv","a")
finalRootTeamsFitnessFile.write("team id, fitness \n")
finalRootTeamsFitnessFile.close()

allScores, trainer = doRun(
    tStart,
    environmentName,
    maxGenerations, 
    teamPopulationSize, 
    episodes, 
    numFrames,
    useMemory,
    numThreads, 
    resultsPath,
    loadPath)


print('Time Taken (Hours): ' + str((time.time() - tStart)/3600))
print('Results:\nMin, Max, Avg')
for score in allScores:
    print(score[0],score[1],score[2])

# I want to see the fitness scores of the final root teams plotted from highest to lowest.
finalRootFitnessFile = open(resultsPath + "FinalRootTeamsFitness.csv","a")
for rt in trainer.rootTeams:
    if rt.fitness is not None:
        finalRootFitnessFile.write(str(rt.id) + "," + str(rt.fitness) + '\n')
finalRootFitnessFile.close()

