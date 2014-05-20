#!/usr/bin/env python

from ItemPredictor import ItemPredictor
from RoundRobinBFS_directed import roundRobinBFS
from collections import deque

class RRBFSDirectedPredictor(ItemPredictor):
    """An ItemPredictor that is implemented using a round robin BFS algorithm on
    a recommendation graph.
    """

    class Session(object):
        """Inner class that defines a user session."""
        def __init__(self):
            self.likes = set()
            self.dislikes = set()
            self.sources = deque()

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
        [self.sessions[sessionId].sources.appendleft(item) for item in likes]

    def nextItems(self, sessionId, num):
        assert sessionId in self.sessions
        items = []
        firstTry = True
        while len(items) < num:
            if not firstTry:
                # if necessary, moves dislikes to likes to find items
                item = self.sessions[sessionId].dislikes.pop()
                self.sessions[sessionId].likes.add(item)
                self.sessions[sessionId].sources.appendleft(item)
            items += roundRobinBFS(self.graph,
                                   self.sessions[sessionId].sources,
                                   self.sessions[sessionId].dislikes,
                                   num - len(items))
            firstTry = False
        return items
        
        

##########################
# ROUGH UNIT TEST
##########################

import pickle

# local modules
from Graph_util import loadGraph

# params
graph_fname = 'data/recDirectedGraph.pickle'

def main():
    graph = loadGraph(graph_fname)
    predictor = RRBFSDirectedPredictor(graph)
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
