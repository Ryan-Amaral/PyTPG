import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def generateGraphs(runInfo, final=True):
    runData = pd.read_csv(
        runInfo['resultsPath'] + runInfo['runStatsFileName'],
        sep=',',
        header=0,
        dtype={
            'generation':'int32',
            'time taken':'float64',
            'min fitness':'float32',
            'avg fitness':'float32',
            'max fitness':'float32',
            'num learners':'int32',
            'num teams in root team':'int32',
            'num instructions':'int64',
            'add':'int64',
            'sub':'int64',
            'mult':'int64',
            'div':'int64',
            'neg':'int64',
            'memRead':'int64',
            'memWrite':'int64'
        }
        ).to_numpy()

    print(runData.dtype.names)
    print(runData.shape)
    print(runData[:,:])

    # Extract the number of generations in the csv file by subtracting 1 (header row)
    # from the number of records found.
    numGenerations = runData.shape[0] - 1

    # Compute a reasonable generation step
    if numGenerations <= 50:
        generationStep = 1
    elif numGenerations <= 100:
        generationStep = 2
    elif numGenerations <= 150:
        generationStep = 5
    elif numGenerations <= 250:
        generationStep = 10
    elif numGenerations <= 500:
        generationStep = 25
    elif numGenerations <= 1000:
        generationStep = 50
    elif numGenerations <= 2000:
        generationStep = 100
    else:
        generationStep = 250

    #Max Fitness Graph
    plt.figure(figsize=(22,17)) #Page sized figures
    x = runData[:,0]
    y = runData[:,3]
    plt.plot(
        x, #x
        y #y
        )
    plt.xlabel("Generation #")
    print('shape of x ' + str(x.shape))
    print('shape of y ' + str(y.shape))
    plt.xticks( np.arange(min(x),max(x)+1,generationStep))
    plt.ylabel("Max Fitness")
    plt.yticks ( np.linspace(min(y),max(y),20))
    plt.title("Max Fitness")

    plt.savefig(runInfo['resultsPath']+runInfo['maxFitnessFile'], format='svg')
    plt.close()

    #Avg Fitness Graph
    plt.figure(figsize=(22,17)) #Page sized figures
    x = runData[:,0]
    y = runData[:,4]
    plt.plot(
        x,
        y
    )
    plt.xlabel("Generation #")
    plt.xticks( np.arange(min(x),max(x)+1,generationStep))
    plt.ylabel("Avg Fitness")
    plt.yticks ( np.linspace(min(y),max(y),20))
    plt.title("Avg Fitness")

    plt.savefig(runInfo['resultsPath']+runInfo['avgFitnessFile'], format='svg')
    plt.close()

    #Min Fitness Graph
    plt.figure(figsize=(22,17)) #Page sized figures
    x = runData[:,0]
    y = runData[:,2]
    plt.plot(
        x,
        y
    )
    plt.xlabel("Generation #")
    plt.xticks( np.arange(min(x),max(x)+1,generationStep))
    plt.ylabel("Min Fitness")
    plt.yticks ( np.linspace(min(y),max(y),20))
    plt.title("Min Fitness")

    plt.savefig(runInfo['resultsPath']+runInfo['minFitnessFile'], format='svg')
    plt.close()

    #Time Taken Graph
    plt.figure(figsize=(22,17)) #Page sized figures
    x = runData[:,0]
    y = runData[:,1]
    plt.plot(
        x,
        y   
    )
    plt.xlabel("Generation #")
    plt.xticks( np.arange(min(x),max(x)+1,generationStep))
    plt.ylabel("Time Taken (hours)")
    plt.yticks ( np.linspace(min(y),max(y),20))
    plt.title("Time Taken")

    plt.savefig(runInfo['resultsPath']+runInfo['timeTakenFile'], format='svg')
    plt.close()

    #Instructions Composition Graph
    plt.figure(figsize=(22,17)) #Page sized figures

    generations = runData[:,0]

    adds = runData[:,8]
    subs = runData[:,9]
    mults = runData[:,10]
    divs = runData[:,11]
    negs = runData[:,12]
    memReads = runData[:,13]
    memWrites = runData[:,14]
    ind = [x for x, _ in enumerate(generations)]

    plt.bar(ind, memWrites, label="memWrites", bottom=memReads+negs+divs+mults+subs+adds)
    plt.bar(ind, memReads, label="memReads", bottom=negs+divs+mults+subs+adds)
    plt.bar(ind, negs, label="negs",bottom=divs+mults+subs+adds)
    plt.bar(ind, divs, label="div",bottom=mults+subs+adds)
    plt.bar(ind, mults, label="mult", bottom=subs+adds)
    plt.bar(ind, subs, label="sub",bottom=adds)
    plt.bar(ind, adds, label="add")

    plt.ylabel("# of Instructions")
    plt.xlabel("Generation #")
    plt.xticks( np.arange(min(ind),max(ind)+1,generationStep, dtype=int))
    plt.legend(loc="upper right")
    plt.title("Instruction Composition")

    plt.savefig(runInfo['resultsPath']+runInfo['instructionCompositionFile'], format='svg')
    plt.close()

    #Learners in Root Team
    plt.figure(figsize=(22,17)) #Page sized figures
    generations = runData[:,0]
    learners = runData[:,5]
    ind = [x for x, _ in enumerate(generations)]

    plt.bar(ind, learners)
    plt.xlabel("Generation #")
    plt.ylabel("# of Learners in Root Team")
    plt.yticks(np.arange(min(learners), max(learners), int(max(learners)/10), dtype=int))
    plt.title("Learners in Root Teams")
    plt.xticks( np.arange(min(ind),max(ind)+1,generationStep, dtype=int))

    plt.savefig(runInfo['resultsPath']+runInfo['learnersFile'], format='svg')
    plt.close()

    #Teams in Root Team
    plt.figure(figsize=(22,17)) #Page sized figures
    generations = runData[:,0]
    teams = runData[:,6]
    ind = [x for x, _ in enumerate(generations)]

    plt.bar(ind, teams)
    plt.xlabel("Generation #")
    plt.xticks( np.arange(min(ind),max(ind)+1,generationStep, dtype=int))
    plt.ylabel("# of Teams in Root Team")
    plt.yticks( np.arange(min(teams), max(teams), int(max(teams)/10), dtype=int))
    plt.title("Teams in Root Teams")

    plt.savefig(runInfo['resultsPath']+runInfo['teamsFile'], format='svg')
    plt.close()

    #Total Instructions Graph
    plt.figure(figsize=(22,17)) #Page sized figures

    generations = runData[:,0]
    totalInstructions = runData[:,7]
    ind = [indx for indx, _ in enumerate(generations)]

    plt.bar(ind, totalInstructions)
    plt.xlabel('Generation #')
    plt.ylabel('# of Instructions')
    plt.title("Total Instructions")
    plt.xticks( np.arange(min(ind),max(ind)+1,generationStep, dtype=int))

    plt.savefig(runInfo['resultsPath']+runInfo['instructionsFile'], format='svg')
    plt.close()

    #If these are final results
    if final:
        #Load Root Team Fitness Data
        rtfData = pd.read_csv(runInfo['resultsPath']+runInfo['finalRootTeamFitnessFileName'], sep=',',header=0).to_numpy()

        print(rtfData.dtype.names)
        print(rtfData.shape)
        print(rtfData)

        rtfData = rtfData[rtfData[:,1].argsort()[::-1]]

        print(rtfData)

        #Root Team Fitness Graph
        plt.figure(figsize=(22,17)) #Page sized figures

        teamIds = rtfData[:,0]
        fitnesses = rtfData[:,1]
        ind = [x for x, _ in enumerate(teamIds)]

        plt.bar(ind, fitnesses)
        plt.xlabel("Team Rank")
        plt.ylabel("Fitness")
        plt.title("Final Root Teams Fitness")
        plt.xticks( np.arange(min(ind),max(ind)+1,10, dtype=int))

        plt.savefig(runInfo['resultsPath']+runInfo['rootTeamsFitnessFile'], format='svg')
        plt.close()


    

