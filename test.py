from extras import runPopulation, runPopulationParallel
from tpg.agent import loadAgent
from tpg.trainer import loadTrainer

tests = {
    "spRun" : "None",
    "mpRun" : "None",
    "saveAgent" : "None",
    "saveTrainer" : "None",
    "loadAgent" : "None",
    "loadTrainer" : "None"}

# single processing run
try:
    spTrainer, spScore = runPopulation(
        envName="Boxing-v0", gens=2, popSize=10, reps=1,
        frames=18000, nRandFrames=30)
    tests["spRun"] = "Pass"
except:
    tests["spRun"] = "Fail"

# multiprocessing run
try:
    mpTrainer, mpScore = runPopulationParallel(
            envName="Boxing-v0", gens=2, popSize=50, reps=3,
            frames=18000, processes=23, nRandFrames=30)
    tests["mpRun"] = "Pass"
except:
    tests["mpRun"] = "Fail"

# save agent
try:
    spAgent = spTrainer.getAgents()[0]
    spAgent.saveToFile("spAgent.pkl")
    print(spAgent.team.outcomes)
    mpAgent = mpTrainer.getAgents()[0]
    mpAgent.saveToFile("mpAgent.pkl")
    print(mpAgent.team.outcomes)
    tests["saveAgent"] = "Pass"
except:
    tests["saveAgent"] = "Fail"

# save trainer
try:
    spTrainer.saveToFile("spTrainer.pkl")
    mpTrainer.saveToFile("mpTrainer.pkl")
    tests["saveTrainer"] = "Pass"
except:
    tests["saveTrainer"] = "Fail"

# load agent
try:
    spAgent = loadAgent("spAgent.pkl")
    print(spAgent.team.outcomes)
    mpAgent = loadAgent("mpAgent.pkl")
    print(mpAgent.team.outcomes)

    tests["loadAgent"] = "Pass"
except:
    tests["loadAgent"] = "Fail"

# load trainer
try:
    spTrainer = loadTrainer("spTrainer.pkl")
    mpTrainer = loadTrainer("mpTrainer.pkl")
    tests["loadTrainer"] = "Pass"
except:
    tests["loadTrainer"] = "Fail"

print(tests)
print(f"SP Score: {spScore}")
print(f"MP Score: {mpScore}")
