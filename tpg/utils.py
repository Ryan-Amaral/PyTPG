import random
import numpy as np

"""
Various useful functions for use within TPG, and for using TPG, like metrics,
etc.
"""

"""
Coin flips, at varying levels of success based on prob.
"""
def flip(prob):
    return random.uniform(0.0,1.0) < prob

"""
Returns the teams that this team references, either immediate or
recursively.
"""
def getTeams(team, rec=True, visited=None):
    if rec:
        # recursively search all teams
        nTeams = 0

        # track visited teams to not repeat
        if visited is None:
            visited = set()

        visited.add(team)

        # get team count from each learner that has a team
        for lrnr in team.learners:
            lrnrTeam = lrnr.getActionTeam()
            if lrnrTeam is not None and lrnrTeam not in visited:
                getTeams(lrnrTeam, rec=True, visited=visited)

        return list(visited)

    else:
        # just the teams attached directly to this team
        return [lrnr.getActionTeam() for lrnr in team.learners
            if not lrnr.isActionAtomic()]

"""
Returns the learners on this team, immediately or recursively.
"""
def getLearners(team, rec=True, tVisited=None, lVisited=None):
    if rec:

        # track visited teams to not repeat
        if tVisited is None:
            tVisited = set()
            lVisited = set()

        tVisited.add(team)
        [lVisited.add(lrnr) for lrnr in team.learners]

        # get team count from each learner that has a team
        for lrnr in team.learners:
            lrnrTeam = lrnr.getActionTeam()
            if lrnrTeam is not None and lrnrTeam not in tVisited:
                getLearners(lrnrTeam, rec=True, tVisited=tVisited, lVisited=lVisited)

        return list(lVisited)

    else:
        # just the teams attached directly to this team
        return list(team.learners)

"""

"""
def outDegree():
    pass

"""

"""
def meanLearners():
    pass

"""
Returns a dictionary containing counts of each type of instruction and other basic
stats relating to instructions.
"learners" is a list of learners that you want the stats from. "operations" is a
list of strings representing the current operation set, can be obtained from Program.
"""
def learnerInstructionStats(learners, operations):

    # stats tracked for each operation and overall
    partialStats = {
        "total": 0,
        "min": float("inf"),
        "max": 0,
        "avg": 0
    }

    # dictionary that we put results in and return
    results = {"overall": partialStats.copy()}
    for op in operations:
        results[op] = partialStats.copy()

    # get instruction data from all provided learners
    for lrnr in learners:
        insts = lrnr.program.instructions
        results["overall"]["total"] += len(insts)
        results["overall"]["min"] = min(len(insts), results["overall"]["min"])
        results["overall"]["max"] = max(len(insts), results["overall"]["max"])
        results["overall"]["avg"] += len(insts)/len(learners)

        for i, op in enumerate(operations):
            opCount = np.count_nonzero(insts[:,1]==i)
            results[op]["total"] += opCount
            results[op]["min"] = min(opCount, results[op]["min"])
            results[op]["max"] = max(opCount, results[op]["max"])
            results[op]["avg"] += opCount/len(learners)

    return results
