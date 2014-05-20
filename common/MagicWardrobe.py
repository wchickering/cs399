#!/usr/bin/env python

from RRBFSDirectedPredictor import RRBFSDirectedPredictor
import pickle

# local modules
from Graph_util import loadGraph

# params
graph_fname = 'data/recDirectedGraph.pickle'

class MagicWardrobe:
    """
    Wrapper class for ItemPredictor.
    """

    def __init__(self):
        """Initializes predictor/feedback engine."""
        graph = loadGraph(graph_fname)
        self.predictor = RRBFSDirectedPredictor(graph)
        pass

    def initSession(self, sessionId):
        self.predictor.initSession(sessionId)

    def feedback(self, sessionId, likes, dislikes):
        self.predictor.feedback(sessionId, likes, dislikes)

    def nextItems(self, sessionId, num):
        return self.predictor.nextItems(sessionId, num)

##########################
# ROUGH UNIT TEST
##########################

def main():
    wardrobe = MagicWardrobe()
    sessionId = 1
    likes = [45, 74]
    dislikes = [888757, 826391]
    num = 10
    wardrobe.initSession(sessionId)
    wardrobe.feedback(sessionId, likes, dislikes)
    items = wardrobe.nextItems(sessionId, num)
    print 'items =', items

if __name__ == '__main__':
    main()
