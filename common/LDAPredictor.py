#!/usr/local/bin/python

from gensim import corpora, models, similarities
from gensim.models import ldamodel
import pickle

class LDAPredictor(object):
    """An abstract class that loads an LDA model from disk and utilizes it to
    predict new items for a session given previously liked and disliked items.
    """

    def __init__(self, dict_fname=None, model_fname=None):
        """Constructs a new LDAPredictor.

        Arguments are the filenames that store the dictionary and LDA model.
        """
        self.dict_fname = dict_fname
        self.model_fname = model_fname
        self.initSession()

    def loadModel(self):
        """Loads a dictionary that maps item tokens to LDA Ids as well as a
        corresonding LDA model from disk.
        """
        self.dictionary = self._loadDictionary(self.dict_fname)
        self.model = self._loadModel(self.model_fname)

    def initSession(self):
        """Initializes a new session. This function does not return anything."""
        raise NotImplementedError

    def feedback(self, likes, dislikes):
        """Informs the LDAPredictor that items in the `likes' set are liked and
        the items in the `dislikes' set are disliked in the present session. The
        provided sets must be disjoint with each other and with all sets previously
        provided. This function does not return anything.
        """
        raise NotImplementedError

    def predict(self, num_items):
        """Returns `num_items' new items that are disjoint with all `likes' and
        `dislikes'  sets previous provided to the feedback() function.
        """
        raise NotImplementedError

    def _loadDictionary(self, filename):
        """Loads dictionary from a text file."""
        dictionary = corpora.Dictionary.load_from_text(filename)
        return dictionary
    
    def _loadModel(self, filename):
        """Loads a pickled LDA model."""
        with open(filename, 'r') as f:
            lda = pickle.load(f)
        return lda
