#!/usr/local/bin/python

class ItemPredictor(object):
    """An abstract class for item prediction."""

    def initSession(self, sessionId):
        """Initializes a new session associated with sessionId.
        This function does not return anything.
        """
        raise NotImplementedError

    def feedback(self, sessionId, likes, dislikes):
        """Informs the ItemPredictor that items in the `likes' set are liked and
        the items in the `dislikes' set are disliked in the present session. The
        provided sets must be disjoint with each other and with all sets previously
        provided. This function does not return anything.
        """
        raise NotImplementedError

    def nextItems(self, sessionId, num):
        """Returns `num' new items that are disjoint with all `likes' and
        `dislikes'  sets previous provided to the feedback() function.
        """
        raise NotImplementedError
