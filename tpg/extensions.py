"""
A collection of functions to get metrics of the population or individuals in the
population. For diagnostic or visualization purposes.
"""

import networkx as nx

def getFullGraph(trainer):
    g = nx.MultiDiGraph()
    colMap = []
    for team in trainer.rootTeams:
        graphTeam(team, g)

    nc, ec, ew = getAttributes(g)

    return g, nc, ec, ew

def getRootTeamGraph(rootTeam):
    g = nx.MultiDiGraph()
    colMap = []

    graphTeam(rootTeam, g)

    nc, ec, ew = getAttributes(g)

    return g, nc, ec, ew

def graphTeam(team, g, visTeams=set(), actionCounts={}):
    if team.learnerRefCount == 0:
        teamName = 'R:' + str(team.uid)
        g.add_node(teamName, color='red')
    else:
        teamName = 'T:' + str(team.uid)
        g.add_node(teamName, color='lightcoral')

    visTeams.add(team)

    for learner in team.learners:
        if learner.action.isAtomic():
            if learner.action.act not in actionCounts:
                actionCounts[learner.action.act] = 0
            else:
                actionCounts[learner.action.act] += 1
            actionName = 'A:' + str(learner.action.act)
            for ac in range(actionCounts[learner.action.act]):
                actionName = ' ' + actionName + ' '
            g.add_node(actionName, color='yellow')
            g.add_edge(teamName, actionName, color='grey', weight=1)
        else:
            if learner.action.act not in visTeams:
                graphTeam(learner.action.act, g, visTeams)
            g.add_edge(teamName, 'T:' + str(learner.action.act.uid), color='grey', weight=2)

def getAttributes(g):
    nodes = g.nodes(data=True)
    nodeColors = [d['color'] for n,d in nodes]
    edges = g.edges(data=True)
    edgeColors = [d['color'] for u,v,d in edges]
    edgeWeights = [d['weight'] for u,v,d in edges]

    return nodeColors, edgeColors, edgeWeights
