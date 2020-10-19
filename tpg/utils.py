import random

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
Returns the number of teams that this team references, either immediate or
recursively.
"""
def numTeams(team, rec=True, visited=None):
    if rec:
        # recursively search all teams
        nTeams = 0

        # track visited teams to not repeat
        if visited is None:
            visited = set([None])

        visited.add(team)

        # get team count from each learner that has a team
        for lrnr in team.learners:
            lrnrTeam = lrnr.getActionTeam()
            if lrnrTeam not in visited:
                nTeams += numTeams(lrnrTeam, rec=True, visited=visited)

        return nTeams

    else:
        # just the teams attached directly to this team
        return len(team.learners) - team.numAtomicActions()

"""
Returns the number of learners on this team, immediately or recursively.
"""
def numLearners(team, rec=True, tVisited=None, lVisited=None):
    if rec:

        # recursively search all learners
        lVisited.add(team.learners)

        # track visited teams to not repeat
        if tVisited is None:
            tVisited = set([None])

        tVisited.add(team)

        # get team count from each learner that has a team
        for lrnr in team.learners:
            lrnrTeam = lrnr.getActionTeam()
            if lrnrTeam not in tVisited:
                numLearners(lrnrTeam, rec=True, tVisited=tVisited, lVisited=lVisited)

        return len(lVisited)

    else:
        # just the teams attached directly to this team
        return len(team.learners)

"""

"""
def outDegree():
    pass

"""

"""
def meanLearners():
    pass

"""

"""
def numInstructions():
    pass
