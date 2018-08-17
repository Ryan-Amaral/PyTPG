"""
A collection of functions to get metrics of the population or individuals in the
population. For diagnostic or visualization purposes.
"""

"""
Returns all nodes and edges that make up the population.
"""
def getFullGraph(trainer):
    nodes = []
    edges = []
    for team in trainer.rootTeams:
        graphTeam(team, nodes, edges)

    return nodes, edges

"""
Returns all nodes and edges from this root team.
"""
def getRootTeamGraph(rootTeam):
    nodes = []
    edges = []
    graphTeam(rootTeam, nodes, edges)

    return nodes, edges

"""
Helper function to make traversing teams easier.
"""
def graphTeam(team, nodes, edges, actionCounts={}):
    if team.learnerRefCount == 0:
        teamName = 'R:' + str(team.uid)
    else:
        teamName = 'T:' + str(team.uid)
    nodes.append(teamName)

    for learner in team.learners:
        if learner.action.isAtomic():
            if learner.action.act not in actionCounts:
                actionCounts[learner.action.act] = 0
            else:
                actionCounts[learner.action.act] += 1
            actionName = 'A:' + str(learner.action.act) + ':' + str(actionCounts[learner.action.act])
            nodes.append(actionName)
            edges.append((teamName, actionName))
        else:
            teamName2 = 'T:' + str(learner.action.act.uid)
            if teamName2 not in nodes:
                graphTeam(learner.action.act, nodes, edges, actionCounts)
            edges.append((teamName, teamName2))
