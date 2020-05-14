#Import libraries
import time
import sys
import random
import numpy as np
from distutils import util
from pathlib import Path
from microsoftgraph.client import Client
import msal
import requests


#Import tpg
from tpg.util.mp_utils import doRun
from tpg.util.mp_utils import runAgent
from tpg.util.ms_graph_utils import getMSGraphToken 
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

#MS Grap Wizardry
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

endpoint = "https://graph.microsoft.com/v1.0/drives/"+msGraphConfig['drive_id']+"/root/children"
http_headers = {
    'Authorization': 'Bearer ' + msGraphToken['access_token'],
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
data = requests.get(endpoint, headers=http_headers, stream=False).json()

print(data)







#client = Client(msGraphConfig['client_id'], msGraphConfig['secret'], account_type=msGraphConfig['tenant_id'])

#client.set_token(msGraphToken)

#print(client.drive_specific_folder("01A5CO2OYH4EJROVUEA5EZPOUTJQ4MNVPV"))

#print(client.drive_root_children_items())


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

http_headers = {
    'Authorization': 'Bearer ' + msGraphToken['access_token'],
    'Accept': 'application/json',
    'ContentType':'text/csv'
}

endpoint = "https://graph.microsoft.com/v1.0/drives/"+msGraphConfig['drive_id']+"/items/"+msGraphConfig['tpg_runs_folder_id']+":/RunStats.csv:/content"
fileData = open(resultsPath+'RunStats.csv', 'rb').read()
request = requests.put(endpoint, headers=http_headers, data=fileData)
print(request.status_code)

data = request.json()
print(data)

itemId = data['id']

endpoint = "https://graph.microsoft.com/v1.0/drives/"+msGraphConfig['drive_id']+"/items/" + data['id']
http_headers = {
    'Authorization': 'Bearer ' + msGraphToken['access_token'],
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
data = requests.get(endpoint, headers=http_headers, stream=False).json()
print(data)

endpoint = "https://graph.microsoft.com/v1.0/drives/"+msGraphConfig['drive_id']+"/items/"+itemId+"/createLink"
payload = {
    'type':'edit',
    'scope': 'anonymous'
}
data = requests.post(endpoint, headers=http_headers, json=payload).json()
print(data)
link = data['link']

endpoint = "https://graph.microsoft.com/v1.0/users/"+msGraphConfig['user_id']+"/sendMail"
payload = {
    'message': {
        'subject':'Py-TPG test email',
        'importance': 'Normal',
        'body': {
            'contentType':'HTML',
            'content':'Your run is <b>done</b>! <a href="'+link['webUrl']+'">link</a>'
        },
        'toRecipients':[
            {
                "emailAddress":{
                    "address":"aianta@dal.ca"
                }
            }
        ]
    }
}
request = requests.post(endpoint, headers=http_headers, stream=False, json=payload)
print(request.status_code)
if request.status_code != 202: 
    errData = request.json()
    print(errData)
