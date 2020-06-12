from optparse import OptionParser

from tpg.util.mp_utils import generateGraphs

parser = OptionParser()

# Read path to result directory
parser.add_option("-s",'--src-dir', type="string", dest="resultsPath", default="./")

# Need a RunStats.csv file to build graphs
parser.add_option("-r","--run-stats", type="string", dest="runStatsFile", default="RunStats.csv")

# Final root team fitness graph is optional, as it can only be provided at the end of a run
parser.add_option("-f","--final-root-team-fitness", type="string", dest="finalRootTeamFitnessStatsFile")

(opts, args) = parser.parse_args()

# Populate a dummy runInfo dict with only the values required to generate the graphs
runInfo = {
    'resultsPath' : opts.resultsPath,
    'runStatsFileName': opts.runStatsFile,
    'finalRootTeamFitnessFileName': opts.finalRootTeamFitnessStatsFile,
    'maxFitnessFile': 'max_fitness.svg',
    'avgFitnessFile':'avg_fitness.svg',
    'minFitnessFile':'min_fitness.svg',
    'timeTakenFile':'time_taken.svg',
    'instructionCompositionFile':'instruction_composition.svg',
    'learnersFile':'learners.svg',
    'teamsFile':'teams.svg',
    'instructionsFile':'instructions.svg',
    'rootTeamsFitnessFile':'final_root_teams.fitness.svg'
}

if opts.finalRootTeamFitnessStatsFile == None:
    generateGraphs(runInfo, False)
else:
     generateGraphs(runInfo, True)