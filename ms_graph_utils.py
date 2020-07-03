import requests
from zipfile import ZipFile
import matplotlib.pyplot as plt
import pandas as pd
import msal
import json
import numpy as np
import os
from graph_utils import generateGraphs

def getMSGraphToken(app, config):
    result = None

    # First, the code looks up a token from the cache.
    # Because we're looking for a token for the current app, not for a user,
    # use None for the account parameter.
    result = app.acquire_token_silent(config["scope"], account=None)

    if not result:
        print("No suitable token exists in cache. Let's get a new one from AAD.")
        result = app.acquire_token_for_client(scopes=config["scope"])

    if "access_token" in result:
        # Call a protected API with the access token.
        print(result["token_type"])
        return result
    else:
        print(result.get("error"))
        print(result.get("error_description"))
        print(result.get("correlation_id"))  # You might need this when reporting a bug.

def downloadRun(access_token, driveId, folderId, itemId, runInfo):

    http_headers = {
        'Authorization': 'Bearer ' + access_token,
    }
    endpoint = "https://graph.microsoft.com/v1.0/drives/" + driveId + "/items/" + itemId + "/content"
    request = requests.get(endpoint, headers=http_headers)
    print(endpoint)
    print('download run zip request status code: '+ str(request.status_code))

    # Save the downloaded file to the filesystem
    runZip = open('runZip.zip','wb')
    runZip.write(request.content)
    runZip.close()

    #Unzip the run
    with ZipFile('runZip.zip','r') as zipObj:
        # Extract run folder contents into the results folder
        zipObj.extractall()
        runInfo['resultsPath'] = './' + zipObj.namelist()[0].split('/')[0] + '/'
        zipObj.printdir()

    runInfo['loadPath'] = runInfo['resultsPath'] + 'trainers/' + runInfo['loadPath']

# Up to 60MB
def uploadFile(access_token, driveId, folderId, uploadedFilename, mimeType, filePath):
    # First create the upload session
    http_headers = {
        'Authorization': 'Bearer ' + access_token,
    }
    endpoint = "https://graph.microsoft.com/v1.0/drives/" + driveId + "/items/" + folderId + ":/"+uploadedFilename+":/createUploadSession"
    fileInfo = {
        '@microsoft.graph.conflictBehavior':'rename',
        'name': uploadedFilename
    }
    # Send create upload session request
    request = requests.post(endpoint, headers=http_headers, json=fileInfo)

    print('create upload session request status code: ' + str(request.status_code))


    # Parse upload session info
    uploadSession = request.json()

    uploadUrl = uploadSession['uploadUrl']
    fileData = open(filePath, 'rb').read()
    fileSizeInBytes = os.path.getsize(filePath)

    #Update HTTP headers for upload request
    http_headers = {
        'Content-Length': str(fileSizeInBytes), #Header values must be str
        'Content-Range': 'bytes 0-' + str((fileSizeInBytes-1)) + "/"+ str(fileSizeInBytes)
    }

    request = requests.put(uploadUrl, headers=http_headers, data=fileData)

    print('upload request status code: ' + str(request.status_code))

    #Parse response json
    data = request.json()

    # Return driveItem
    return data



# Up to 4MB!!
# Returns drive item
# https://docs.microsoft.com/en-us/graph/api/driveitem-put-content?view=graph-rest-1.0&tabs=http#http-request-to-upload-a-new-file
def uploadSmallFile(access_token, driveId, folderId, uploadedFilename, mimeType, filePath):
    http_headers = {
        'Authorization': 'Bearer ' + access_token,
        'Accept': 'application/json',
        'ContentType': mimeType
    }

    endpoint = "https://graph.microsoft.com/v1.0/drives/" + driveId + "/items/" + folderId + ":/"+uploadedFilename+":/content"
    fileData = open(filePath, 'rb').read()
    request = requests.put(endpoint, headers=http_headers, data=fileData)
    print('upload request status code: ' + str(request.status_code))

    #Parse response json
    data = request.json()

    #Return driveItem
    return data

# Returns drive item with specified id from specified drive id
# https://docs.microsoft.com/en-us/graph/api/driveitem-get?view=graph-rest-1.0&tabs=http#http-request
def getDriveItem(access_token, driveId, driveItemId):
    endpoint = "https://graph.microsoft.com/v1.0/drives/" + driveId + "/items/" + driveItemId
    http_headers = {
        'Authorization': 'Bearer ' + access_token,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = requests.get(endpoint, headers=http_headers, stream=False).json()
    return data

# Returns an anonymous shareable link to drive item with specified id. Link url will be in 'webUrl' field
# https://docs.microsoft.com/en-us/graph/api/driveitem-createlink?view=graph-rest-1.0&tabs=http#http-request
def getShareableLink(access_token, driveId, driveItemId):
    endpoint = "https://graph.microsoft.com/v1.0/drives/"+ driveId + "/items/"+ driveItemId +"/createLink"
    http_headers = {
        'Authorization': 'Bearer ' + access_token,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    payload = {
        'type':'edit',
        'scope': 'anonymous'
    }
    data = requests.post(endpoint, headers=http_headers, json=payload).json()
    link = data['link'] #Note that we send the link sub-object of the MS Graph response
    return link

# Sends an email to specified recipient addresses containig the results link
# See example request in MS Graph Explorer for more details https://developer.microsoft.com/en-us/graph/graph-explorer/preview
def sendEmailWithResultsLink(access_token, sender_id, resultsUrl, recipientEmails, runInfo, final, gen):



    content = "<h2>Run Info</h2>"
    for i in runInfo:
        content += i + " = " + str(runInfo[i]) + "<br>"

    trainer = runInfo['trainer']
    content +="<h2>Trainer Info</h2> <br>"
    content +="teamPopSize = " + str(trainer.teamPopSize) + "<br>"
    content +="rootBasedPop = "+ str(trainer.rootBasedPop) + "<br>"
    content +="gap = " + str(trainer.gap) + "<br>"
    content +="uniqueProgThresh = " + str(trainer.uniqueProgThresh) + "<br>"
    content +="initMaxTeamSize = " + str(trainer.initMaxTeamSize) + "<br>"
    content +="initMaxProgSize = " + str(trainer.initMaxProgSize) + "<br>"
    content +="registerSize = " + str(trainer.registerSize) + "<br>"
    content +="pDelLrn = " + str(trainer.pDelLrn) + "<br>"
    content +="pAddLrn = " + str(trainer.pAddLrn) + "<br>"
    content +="pMutLrn = " + str(trainer.pMutLrn) + "<br>"
    content +="pMutProg = " + str(trainer.pMutProg) + "<br>"
    content +="pMutAct = "+ str(trainer.pMutAct) + "<br>"
    content +="pActAtom = "+ str(trainer.pActAtom) + "<br>"
    content +="pDelInst = "+ str(trainer.pDelInst) + "<br>"
    content +="pAddInst = "+ str(trainer.pAddInst) + "<br>"
    content +="pSwpInst = " + str(trainer.pSwpInst) + "<br>"
    content +="pMutInst = " + str(trainer.pMutInst) + "<br>"
    content +="pSwapMutliAct = "+str(trainer.pSwapMultiAct ) + "<br>"
    content +="pChangeMultiAct = "+ str(trainer.pChangeMultiAct) + "<br>"
    content +="doElites = " + str(trainer.doElites) + "<br>"
    content +="sourceRange = " + str(trainer.sourceRange) + "<br>"
    content +="sharedMemory = "+ str(trainer.sharedMemory) + "<br>"
    content +="memMatrixShape = "+ str(trainer.memMatrixShape) + "<br>"
    content +="traversal = "+ str(trainer.traversal) + "<br>"



    #Encode recipients
    recipients = []
    for email in recipientEmails:
        recipients.append({
            "emailAddress":{
                "address": email
            }
        })

    endpoint = "https://graph.microsoft.com/v1.0/users/"+sender_id+"/sendMail"
    http_headers = {
        'Authorization': 'Bearer ' + access_token,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    if gen != 0:
        payload = {
            'message': {
                'subject':("PyTPG Run Complete [" if final else "PyTPG Run Progress [")+runInfo['environmentName']+" on "+ runInfo['hostname']+("]" if final else (" Gen " + str(gen) + "/" + str(runInfo['maxGenerations']) + ']')),
                'importance': 'Normal',
                'body': {
                    'contentType':'HTML',
                    'content': content + '<h3><a href="'+resultsUrl+ ('">Results link</a></h3>' if final else '">Partial Results link</a></h3>')
                },
                'toRecipients': recipients
            }
        }
    else:
        payload = {
            'message': {
                'subject':"PyTPG Run Started ["+runInfo['environmentName']+" on "+ runInfo['hostname']+ "]",
                'importance': 'Normal',
                'body': {
                    'contentType':'HTML',
                    'content': content
                },
                'toRecipients': recipients
            }
        }

    request = requests.post(endpoint, headers=http_headers, stream=False, json=payload)
    print('send email request status code: ' + str(request.status_code))
    if request.status_code != 202:
        errData = request.json()
        print(errData)



def processPartialResults(runInfo, gen):

    generateGraphs(runInfo, final=False)

    with ZipFile(runInfo['resultsPath']+runInfo['outputName'] + "_gen_"+ str(gen)+ ".zip","w") as zipFile:
        zipFile.write(runInfo['resultsPath']+runInfo['runInfoFileName'])
        zipFile.write(runInfo['resultsPath']+runInfo['runStatsFileName'])
        zipFile.write(runInfo['resultsPath']+runInfo['maxFitnessFile'])
        zipFile.write(runInfo['resultsPath']+runInfo['avgFitnessFile'])
        zipFile.write(runInfo['resultsPath']+runInfo['minFitnessFile'])
        zipFile.write(runInfo['resultsPath']+runInfo['timeTakenFile'])
        zipFile.write(runInfo['resultsPath']+runInfo['instructionCompositionFile'])
        zipFile.write(runInfo['resultsPath']+runInfo['learnersFile'])
        zipFile.write(runInfo['resultsPath']+runInfo['teamsFile'])
        zipFile.write(runInfo['resultsPath']+runInfo['instructionsFile'])
        zipFile.write(runInfo['lastTrainerPath'])

    #MS Graph Wizardry
    msGraphConfig = json.load(open(runInfo['msGraphConfigPath']))


    # Create a preferably long-lived app instance that maintains a token cache.
    app = msal.ConfidentialClientApplication(
        msGraphConfig["client_id"], authority=msGraphConfig["authority"],
        client_credential=msGraphConfig["secret"],
        # token_cache=...  # Default cache is in memory only.
                        # You can learn how to use SerializableTokenCache from
                        # https://msal-python.rtfd.io/en/latest/#msal.SerializableTokenCache
        )

    msGraphToken = getMSGraphToken(app, msGraphConfig)

    # Upload RunStats
    driveItem = uploadFile(
        msGraphToken['access_token'],
        msGraphConfig['drive_id'],
        msGraphConfig['tpg_runs_folder_id'],
        runInfo['outputName'] + "_gen_"+ str(gen)+".zip",
        "application/zip",
        runInfo['resultsPath'] + runInfo['outputName'] + "_gen_"+ str(gen)+".zip"
    )

    # Get a shareable link to the results
    link = getShareableLink(
        msGraphToken['access_token'],
        msGraphConfig['drive_id'],
        driveItem['id']
    )

    # Send emails
    if len(runInfo['emailList']) > 0:
        sendEmailWithResultsLink(
            msGraphToken['access_token'],
            msGraphConfig['user_id'],
            link['webUrl'],
            runInfo['emailList'],
            runInfo,
            False,
            gen
        )
