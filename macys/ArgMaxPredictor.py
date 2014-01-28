#!/usr/local/bin/python

from LDAPredictor import LDAPredictor
from gensim import corpora, models, similarities
from gensim.models import ldamodel
from numpy.random import multinomial
import operator

class ArgMaxPredictor(LDAPredictor):
    """An implementation of an LDAPredictor that uses Bayes' rule to generate
    item predictions.
    """

    def __init__(self, ignore_dislikes=True, topn_items=1000, **kwds):
        """Constructs a new BayesPredictor.

        Note that predictions associated with a topic are limited to the most
        likely topn_items items.
        """
        super(ArgMaxPredictor, self).__init__(**kwds)
        self.ignore_dislikes = ignore_dislikes
        self.topn_items = topn_items=1000

    def initSession(self):
        self.session_likes = set()
        self.session_dislikes = set()
        self.session_content = set()

    def feedback(self, likes, dislikes):
        print 'likes =', likes
        print 'dislikes =', dislikes
        if not self.ignore_dislikes:
            negative_content =\
                set([self.dictionary.token2id[str(-token)] for token in dislikes])
        likes =\
            set([self.dictionary.token2id[str(token)] for token in likes])
        dislikes =\
            set([self.dictionary.token2id[str(token)] for token in dislikes])

        assert likes.isdisjoint(dislikes),\
            'likes and dislikes are not disjoint'
        assert self.session_likes.isdisjoint(likes),\
            'new likes are not disjoint with old likes'
        assert self.session_dislikes.isdisjoint(dislikes),\
            'new dislikes are not disjoint with old dislikes'
        if not self.ignore_dislikes:
            assert self.session_content.isdisjoint(negative_content),\
                'new negative content is not disjoint with old content'

        self.session_likes = self.session_likes.union(likes)
        self.session_dislikes = self.session_dislikes.union(dislikes)
        self.session_content = self.session_content.union(likes)
        if not self.ignore_dislikes:
            self.session_content = self.session_content.union(negative_content)

    def predict(self, num_items):
        content_vector = [(item, 1) for item in self.session_content]
        topic_dist = self.model[content_vector]
        candidates = {}
        for topic_cpd in topic_dist:
            topic = topic_cpd[0]
            topic_prob = topic_cpd[1]
            item_dist = self.model.show_topic(topic, topn=self.topn_items)
            for item_cpd in item_dist:
                item_prob = item_cpd[0]
                token_str = item_cpd[1]
                if not self.ignore_dislikes and int(token_str) < 0:
                    continue
                if token_str in candidates:
                    candidates[token_str] += topic_prob*item_prob
                else:
                    candidates[token_str] = topic_prob*item_prob
        sorted_candidates = sorted(candidates.iteritems(),
                                   key=operator.itemgetter(1),
                                   reverse=True)
        predictions = []
        scores = []
        taken = 0
        for candidate in sorted_candidates:
            itemid = self.dictionary.token2id[candidate[0]]
            if itemid not in self.session_likes and \
               itemid not in self.session_dislikes:
                scores.append(candidate[1])
                taken += 1
                predictions.append(int(candidate[0]))
                if taken >= num_items:
                    break
        print 'scores =', scores
        return predictions

def main():
    """A simple, sanity-checking test."""
    predictor = ArgMaxPredictor(dict_fname='tokens.dict', model_fname='lda.pickle')
    print 'Loading Model. . .'
    predictor.loadModel()
    likes = set([960598,666644,632709,551024,932073,960606,824431,914853,1093859,1053814])
    dislikes = set([515584,632705,1029423,954024,741969,816553,741970,682798,816570,716589])
    print 'Providing initial feedback. . .'
    print 'likes =', likes
    print 'dislikes =', dislikes
    predictor.feedback(likes, dislikes)
    print 'Soliciting prediction. . .'
    new_items = predictor.predict(10)
    print new_items

if __name__ == '__main__':
    main()
