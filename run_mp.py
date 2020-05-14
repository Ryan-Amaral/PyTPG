#Import libraries
import time
import sys
import random
import numpy as np
import platform
from distutils import util
from pathlib import Path
from microsoftgraph.client import Client
import msal
import requests


#Import tpg
from tpg.util.mp_utils import doRun
from tpg.util.mp_utils import runAgent
from tpg.util.ms_graph_utils import getMSGraphToken 
from tpg.util.ms_graph_utils import uploadFile
from tpg.util.ms_graph_utils import getShareableLink
from tpg.util.ms_graph_utils import sendEmailWithResultsLink
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
    emailList = json.load(open(sys.argv[11]))
    if len(sys.argv) > 12:
        loadPath = sys.argv[12]
    else:
        loadPath = None

    #Collect some other stuff
    hostname = platform.node()
    strStartTime = time.ctime()

    runInfo = {
        'hostname': hostname,
        'startTime': strStartTime,
        'environmentName':environmentName,
        'maxGenerations':maxGenerations,
        'episodes':episodes,
        'numFrames':numFrames,
        'numThreads':numThreads,
        'teamPopulationSize': teamPopulationSize,
        'useMemory': useMemory,
        'traversalType': traversalType,
        'resultsPath': resultsPath,
        'msGraphConfigPath': msGraphConfigPath,
        'emailListPath': sys.argv[11],
        'emailList': emailList,
        'loadPath':loadPath,
        'runInfoFileName': "RunInfo.txt",
        'runStatsFileName':"RunStats.csv",
        'finalRootTeamFitnessFileName':"FinalRootTeamsFitness.csv"
    }
else:
    print("python run_mp.py <environmentName> <maxGenerations> <episodes> <numFrames> <numThreads> <teamPopulationSize> <useMemory> <traversalType> <resultsPath> <msGraphConfigPath> <emailListPath> <loadPath>")
    sys.exit()



#MS Graph Wizardry
msGraphConfig = json.load(open(msGraphConfigPath))


# Create a preferably long-lived app instance that maintains a token cache.
app = msal.ConfidentialClientApplication(
    msGraphConfig["client_id"], authority=msGraphConfig["authority"],
    client_credential=msGraphConfig["secret"],
    # token_cache=...  # Default cache is in memory only.
                       # You can learn how to use SerializableTokenCache from
                       # https://msal-python.rtfd.io/en/latest/#msal.SerializableTokenCache
    )

msGraphToken = getMSGraphToken(app, msGraphConfig)

#Start timestmap
tStart = time.time()
runInfo['tStart'] = tStart

print("Starting run with args:")
print("host = " + runInfo['hostname'])
print("startTime = " + runInfo['startTime'])
print("tStart = " + str(runInfo['tStart']))
print("environmentName = " + runInfo['environmentName'])
print("maxGenerations = " + str(runInfo['maxGenerations']))
print("episodes = " + str(runInfo['episodes']))
print("numFrames = " + str(runInfo['numFrames']))
print("threads = " + str(runInfo['numThreads']))
print("teamPopulationSize = " + str(runInfo['teamPopulationSize']))
print("useMemory = " + str(runInfo['useMemory']))
print("traversalType = " + str(runInfo['traversalType']))
print("resultsPath = " + str(runInfo['resultsPath']))
print("msGraphConfigPath = " + str(runInfo['msGraphConfigPath']))
print("emailListPath = " + runInfo['emailListPath'])
print("emailList: ")
for email in runInfo['emailList']:
    print("\t" + email)
print("loadPath = " + str(runInfo['loadPath']))



# Setup output files

# Create results path if it doesn't exist
Path(resultsPath).mkdir(parents=True, exist_ok=True) 

# RunInfo.txt - Program arguments, loaded configurations, implicit configurations
# RunStats.csv - Stats of interest collected during the generation loop
# RunFitnessStats.csv - Fitness scores of the generations, collected after the generation loop
# FinalRootTeamsFitness.csv - Fitness each team in the root team after the run is complete. 
runInfoFile = open(runInfo['resultsPath'] + runInfo['runInfoFileName'], "a")
#TODO - print Program arguments, loaded configurations, implicit configurations. Don't print sensitive garbage!!
runInfoFile.close()

runStatsFile = open(runInfo['resultsPath'] + runInfo['runStatsFileName'], "a")
runStatsFile.write("Generation #, time taken, min fitness, max fitness, avg fitness, # of learners, # of teams in root team, # of instructions, add, sub, mult, div, neg, memRead, memWrite \n")
runStatsFile.close()

finalRootTeamsFitnessFile = open(runInfo['resultsPath'] + runInfo['finalRootTeamFitnessFileName'],"a")
finalRootTeamsFitnessFile.write("team id, fitness \n")
finalRootTeamsFitnessFile.close()

allScores, trainer = doRun(runInfo)


print('Time Taken (Hours): ' + str((time.time() - runInfo['tStart'])/3600))
print('Results:\nMin, Max, Avg')
for score in allScores:
    print(score[0],score[1],score[2])

# I want to see the fitness scores of the final root teams plotted from highest to lowest.
finalRootFitnessFile = open(resultsPath + "FinalRootTeamsFitness.csv","a")
for rt in trainer.rootTeams:
    if rt.fitness is not None:
        finalRootFitnessFile.write(str(rt.id) + "," + str(rt.fitness) + '\n')
finalRootFitnessFile.close()

# Upload RunStats #TODO replace this with zip of full results
driveItem = uploadFile(
    msGraphToken['access_token'],
    msGraphConfig['drive_id'],
    msGraphConfig['tpg_runs_folder_id'],
    runInfo['runStatsFileName'],
    "text/csv",
    runInfo['resultsPath'] + runInfo['runStatsFileName']
)

# Get a shareable link to the results
link = getShareableLink(
    msGraphToken['access_token'],
    msGraphConfig['drive_id'],
    driveItem['id']
)

# Send emails
if len(emailList) > 0:
    sendEmailWithResultsLink(
        msGraphToken['access_token'],
        msGraphConfig['user_id'],
        link['webUrl'],
        runInfo['emailList'],
        runInfo
    )

