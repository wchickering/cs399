#!/usr/local/bin/python

from ItemPredictor import ItemPredictor
from RoundRobinBFS import roundRobinBFS

class RRBFSPredictor(ItemPredictor):
    """An ItemPredictor that is implemented using a round robin BFS algorithm on
    a recommendation graph.
    """

    class Session(object):
        """Inner class that defines a user session."""
        def __init__(self):
            self.likes = set()
            self.dislikes = set()
            self.sources = []

    def __init__(self, graph):
        self.graph = graph
        self.sessions = {}

    def initSession(self, sessionId):
        self.sessions[sessionId] = self.Session()

    def feedback(self, sessionId, likes, dislikes):
        assert sessionId in self.sessions
        likes = set(likes)
        dislikes = set(dislikes)
        assert likes.isdisjoint(dislikes)
        assert likes.isdisjoint(self.sessions[sessionId].likes)
        assert dislikes.isdisjoint(self.sessions[sessionId].dislikes)
        self.sessions[sessionId].likes =\
            self.sessions[sessionId].likes.union(likes)
        self.sessions[sessionId].dislikes =\
            self.sessions[sessionId].dislikes.union(dislikes)
        [self.sessions[sessionId].sources.append(item) for item in likes]

    def nextItems(self, sessionId, num):
        assert sessionId in self.sessions
        # TODO: Fix this to rotate sources properly!
        self.sessions[sessionId].sources.reverse()
        items = roundRobinBFS(self.graph,
                              self.sessions[sessionId].sources,
                              self.sessions[sessionId].dislikes,
                              num)
        self.sessions[sessionId].sources.reverse()
        return items
        
        

##########################
# ROUGH UNIT TEST
##########################

import pickle

# params
graph_fname = 'recGraph.pickle'

def loadGraph():
    with open(graph_fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def main():
    graph = loadGraph()
    predictor = RRBFSPredictor(graph)
    sessionId = 1
    likes = [45, 74]
    dislikes = [888757, 826391]
    num = 10
    predictor.initSession(sessionId)
    predictor.feedback(sessionId, likes, dislikes)
    items = predictor.nextItems(sessionId, num)
    print 'items =', items

if __name__ == '__main__':
    main()
