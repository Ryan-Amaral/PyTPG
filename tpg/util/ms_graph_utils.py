import requests


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

# Up to 4MB!!
# Returns drive item 
# https://docs.microsoft.com/en-us/graph/api/driveitem-put-content?view=graph-rest-1.0&tabs=http#http-request-to-upload-a-new-file
def uploadFile(access_token, driveId, folderId, uploadedFilename, mimeType, filePath):
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
def sendEmailWithResultsLink(access_token, sender_id, resultsUrl, recipientEmails, runInfo):

    content = "<h2>Run Info</h2>"
    content += "host = " + runInfo['hostname'] + "<br>"
    content += "startTime = " + runInfo['startTime']+ "<br>"
    content += "tStart = " + str(runInfo['tStart'])+ "<br>"
    content +="environmentName = " + runInfo['environmentName']+ "<br>"
    content +="maxGenerations = " + str(runInfo['maxGenerations'])+ "<br>"
    content +="episodes = " + str(runInfo['episodes'])+ "<br>"
    content +="numFrames = " + str(runInfo['numFrames'])+ "<br>"
    content +="threads = " + str(runInfo['numThreads'])+ "<br>"
    content +="teamPopulationSize = " + str(runInfo['teamPopulationSize'])+ "<br>"
    content +="useMemory = " + str(runInfo['useMemory'])+ "<br>"
    content +="traversalType = " + str(runInfo['traversalType'])+ "<br>"
    content +="resultsPath = " + str(runInfo['resultsPath'])+ "<br>"
    content +="msGraphConfigPath = " + str(runInfo['msGraphConfigPath'])+ "<br>"
    content +="emailListPath = " + runInfo['emailListPath']+ "<br>"
    content +="emailList: <ul>"
    for email in runInfo['emailList']:
        content +="<li>" + email + "</li>"
    content += "</ul>"
    content +="loadPath = " + str(runInfo['loadPath'])+ "<br>"

    trainer = runInfo['trainer']
    content +="<h3>Trainer Info</h3> <br>"
    content +="teamPopSize = " + str(trainer.teamPopSize) + "<br>"
    content +="rTeamPopSize = "+ str(trainer.rTeamPopSize) + "<br>"
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
    content +="pSwapMutliAct = "+str(trainer.pSwapMutliAct) + "<br>"
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
    payload = {
        'message': {
            'subject':"PyTPG Run Complete ["+runInfo['environmentName']+" on "+ runInfo['hostname']+"]",
            'importance': 'Normal',
            'body': {
                'contentType':'HTML',
                'content': content + '<h3><a href="'+resultsUrl+'">Results link</a></h3>'
            },
            'toRecipients': recipients
        }
    }
    request = requests.post(endpoint, headers=http_headers, stream=False, json=payload)
    print('send email request status code: ' + str(request.status_code))
    if request.status_code != 202: 
        errData = request.json()
        print(errData)
