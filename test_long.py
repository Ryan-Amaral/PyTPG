from extras import runPopulation, runPopulationParallel
from tpg.agent import loadAgent
from tpg.trainer import loadTrainer

_, mpScore = runPopulationParallel(
    envName="Boxing-v0", gens=1000, popSize=360, reps=3,
    frames=18000, processes=12, nRandFrames=30)

print(f"MP Score: {mpScore}")
