#!/usr/bin/env python

import pickle

class LDAPredictor(object):
    """An abstract class that loads an LDA model from disk and utilizes it to
    predict new items for a session given previously liked and disliked items.
    """

    def __init__(self, model_fname=None):
        """Constructs a new LDAPredictor.

        Argument is the filename that stores the LDA model.
        """
        self.model_fname = model_fname
        self.initSession()

    def loadModel(self):
        """Loads LDA model from disk.
        """
        self.model = self._loadModel(self.model_fname)

    def initSession(self):
        """Initializes a new session. This function does not return anything."""
        raise NotImplementedError

    def feedback(self, likes, dislikes):
        """Informs the LDAPredictor that items in the `likes' set are liked and
        the items in the `dislikes' set are disliked in the present session. The
        provided sets must be disjoint with each other and with all sets
        previously provided. This function does not return anything.
        """
        raise NotImplementedError

    def predict(self, num_items):
        """Returns `num_items' new items that are disjoint with all `likes' and
        `dislikes'  sets previous provided to the feedback() function.
        """
        raise NotImplementedError

    def _loadModel(self, filename):
        """Loads a pickled LDA model."""
        with open(filename, 'r') as f:
            lda = pickle.load(f)
        return lda
