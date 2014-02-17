#!/usr/local/bin/python

from WalkPredictor import WalkPredictor
import pickle

# params
graph_fname = 'recGraph.pickle'

class MagicWardrobe:
    """
    Wrapper class for ItemPredictor.
    """

    def __init__(self):
        """Initializes predictor/feedback engine."""
        graph = self._loadGraph()
        self.predictor = WalkPredictor(graph)
        pass

    def initSession(self, sessionId):
        self.predictor.initSession(sessionId)

    def feedback(self, sessionId, likes, dislikes):
        self.predictor.feedback(sessionId, likes, dislikes)

    def nextItems(self, sessionId, num):
        return self.predictor.nextItems(sessionId, num)

    def _loadGraph(self):
        with open(graph_fname, 'r') as f:
            graph = pickle.load(f)
        return graph


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
