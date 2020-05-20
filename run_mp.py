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
from zipfile import ZipFile
import json

#Import tpg
from tpg.util.mp_utils import doRun
from tpg.util.mp_utils import runAgent
from tpg.util.mp_utils import writeRunInfo
from tpg.util.mp_utils import generateGraphs
from tpg.util.mp_utils import determineResultsPath
from tpg.util.ms_graph_utils import getMSGraphToken 
from tpg.util.ms_graph_utils import uploadFile
from tpg.util.ms_graph_utils import getShareableLink
from tpg.util.ms_graph_utils import sendEmailWithResultsLink
from tpg.trainer import Trainer
from tpg.agent import Agent



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
    outputName = sys.argv[10]
    msGraphConfigPath = sys.argv[11]
    emailList = json.load(open(sys.argv[12]))
    if len(sys.argv) > 13:
        loadPath = sys.argv[13]
    else:
        loadPath = None

    #Collect some other stuff
    hostname = platform.node()
    strStartTime = time.ctime()

    #Prevent overwriting results
    resultsPath = determineResultsPath(resultsPath)

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
        'outputName':outputName,
        'msGraphConfigPath': msGraphConfigPath,
        'emailListPath': sys.argv[12],
        'emailList': emailList,
        'loadPath':loadPath,
        'runInfoFileName': "RunInfo.txt",
        'runStatsFileName':"RunStats.csv",
        'finalRootTeamFitnessFileName':"FinalRootTeamsFitness.csv",
        #Define graph file names
        'maxFitnessFile':'max_fitness.svg',
        'avgFitnessFile':'avg_fitness.svg',
        'minFitnessFile':'min_fitness.svg',
        'timeTakenFile':'time_taken.svg',
        'instructionCompositionFile': 'instruction_composition.svg',
        'learnersFile':'learners.svg',
        'teamsFile':'teams.svg',
        'instructionsFile':'instructions.svg',
        'rootTeamsFitnessFile':'final_root_teams_fitness.svg'
    }
else:
    print("python run_mp.py <environmentName> <maxGenerations> <episodes> <numFrames> <numThreads> <teamPopulationSize> <useMemory> <traversalType> <resultsPath> <outputName> <msGraphConfigPath> <emailListPath> <loadPath>")
    sys.exit()


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
print("outputName = " + runInfo['outputName'])
print("msGraphConfigPath = " + str(runInfo['msGraphConfigPath']))
print("emailListPath = " + runInfo['emailListPath'])
print("emailList: ")
for email in runInfo['emailList']:
    print("\t" + email)
print("loadPath = " + str(runInfo['loadPath']))



# Setup output files

# Create results path if it doesn't exist
Path(runInfo['resultsPath']).mkdir(parents=True, exist_ok=True) 

# RunInfo.txt - Program arguments, loaded configurations, implicit configurations
# RunStats.csv - Stats of interest collected during the generation loop
# FinalRootTeamsFitness.csv - Fitness each team in the root team after the run is complete. 
runInfoFile = open(runInfo['resultsPath'] + runInfo['runInfoFileName'], "a")
#TODO - print Program arguments, loaded configurations, implicit configurations. Don't print sensitive garbage!!
runInfoFile.close()
writeRunInfo(runInfo)

runStatsFile = open(runInfo['resultsPath'] + runInfo['runStatsFileName'], "a")
runStatsFile.write("generation,time taken,min fitness,max fitness,avg fitness,num learners,num teams in root team,num instructions,add,sub,mult,div,neg,memRead,memWrite\n")
runStatsFile.close()

finalRootTeamsFitnessFile = open(runInfo['resultsPath'] + runInfo['finalRootTeamFitnessFileName'],"a")
finalRootTeamsFitnessFile.write("team id,fitness\n")
finalRootTeamsFitnessFile.close()

allScores, trainer = doRun(runInfo)


print('Time Taken (Hours): ' + str((time.time() - runInfo['tStart'])/3600))
print('Results:\nMin, Max, Avg')
for score in allScores:
    print(score[0],score[1],score[2])

# I want to see the fitness scores of the final root teams plotted from highest to lowest.
finalRootFitnessFile = open(runInfo['resultsPath'] + runInfo['finalRootTeamFitnessFileName'],"a")
for rt in trainer.rootTeams:
    if rt.fitness is not None:
        finalRootFitnessFile.write(str(rt.id) + "," + str(rt.fitness) + '\n')
finalRootFitnessFile.close()

#Generate Graphs
generateGraphs(runInfo)

#Create ZIP file
with ZipFile(runInfo['resultsPath']+runInfo['outputName']+'.zip','w') as zipFile:
    zipFile.write(runInfo['resultsPath']+runInfo['runInfoFileName'])
    zipFile.write(runInfo['resultsPath']+runInfo['runStatsFileName'])
    zipFile.write(runInfo['resultsPath']+runInfo['finalRootTeamFitnessFileName'])
    zipFile.write(runInfo['resultsPath']+runInfo['maxFitnessFile'])
    zipFile.write(runInfo['resultsPath']+runInfo['avgFitnessFile'])
    zipFile.write(runInfo['resultsPath']+runInfo['minFitnessFile'])
    zipFile.write(runInfo['resultsPath']+runInfo['timeTakenFile'])
    zipFile.write(runInfo['resultsPath']+runInfo['instructionCompositionFile'])
    zipFile.write(runInfo['resultsPath']+runInfo['learnersFile'])
    zipFile.write(runInfo['resultsPath']+runInfo['teamsFile'])
    zipFile.write(runInfo['resultsPath']+runInfo['instructionsFile'])
    zipFile.write(runInfo['resultsPath']+runInfo['rootTeamsFitnessFile'])
    

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

# Upload RunStats #TODO replace this with zip of full results
driveItem = uploadFile(
    msGraphToken['access_token'],
    msGraphConfig['drive_id'],
    msGraphConfig['tpg_runs_folder_id'],
    runInfo['outputName'] + ".zip",
    "application/zip",
    runInfo['resultsPath'] + runInfo['outputName'] + ".zip"
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
        runInfo,
        True,
        -1
    )

