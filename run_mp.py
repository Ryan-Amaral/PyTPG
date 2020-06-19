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
from optparse import OptionParser

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


parser = OptionParser()

parser.add_option('-e','--env', type="string", dest="environmentName", default="Boxing-v0")
parser.add_option('-x', '--max-gens', type="int", dest="maxGenerations", default=2000)
parser.add_option('-i', '--episodes', type="int", dest="episodes", default=10)
parser.add_option('-f','--frames', type="int", dest="numFrames",default=18000)
parser.add_option('-t','--threads', type="int", dest="numThreads", default=4)
parser.add_option('-p', '--team-pop', type="int", dest="teamPopulationSize",default=600)
parser.add_option('-y', '--use-memory', action="store_true", dest="useMemory", default=False)
parser.add_option('-v', '--traversal', type="string", dest="traversalType", default="team")
parser.add_option('-m','--mode', type="string", dest="mode", default="train")
parser.add_option('-r', '--results-path', type="string", dest="resultsPath", default="./results/")
parser.add_option('-o', '--output', type="string", dest="outputName", default="results")
parser.add_option('-s', '--ms-graph-config', type="string", dest="msGraphConfigPath")
parser.add_option('--email-list', type="string", dest="emailList", default="notify.json")
parser.add_option('-l','--load-path', type="string", dest="loadPath")
parser.add_option('-g','--resume-from-gen', type="int", dest="resumeGen")


(opts, args) = parser.parse_args()


#Collect some other stuff
hostname = platform.node()
strStartTime = time.ctime()

#Prevent overwriting results
resultsPath = determineResultsPath(opts.resultsPath)

emailList = json.load(open(opts.emailList))

runInfo = {
    'hostname': hostname,
    'startTime': strStartTime,
    'environmentName':opts.environmentName,
    'maxGenerations':opts.maxGenerations,
    'episodes':opts.episodes,
    'numFrames':opts.numFrames,
    'numThreads':opts.numThreads,
    'teamPopulationSize': opts.teamPopulationSize,
    'useMemory': opts.useMemory,
    'traversalType': opts.traversalType,
    'mode': opts.mode,
    'resultsPath': opts.resultsPath,
    'outputName':opts.outputName,
    'msGraphConfigPath': opts.msGraphConfigPath,
    'emailListPath': opts.emailList,
    'emailList': emailList,
    'loadPath':opts.loadPath,
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



#Start timestmap
tStart = time.time()
runInfo['tStart'] = tStart

#Print run info
for i in runInfo:
    print (i, runInfo[i])

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

