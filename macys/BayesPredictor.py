#!/usr/local/bin/python

from LDAPredictor import LDAPredictor
from gensim import corpora, models, similarities
from gensim.models import ldamodel
from numpy.random import multinomial
import logging

class BayesPredictor(LDAPredictor):
    """An implementation of an LDAPredictor that uses Bayes' rule to generate
    item predictions.
    """

    def __init__(self, topn_items=1000, **kwds):
        """Constructs a new BayesPredictor.

        Note that predictions associated with a topic are limited to the most
        likely topn_items items.
        """
        super(BayesPredictor, self).__init__(**kwds)
        self.topn_items = topn_items=1000

    def initSession(self):
        self.session_likes = set()
        self.session_dislikes = set()
        self.session_content = set()

    def feedback(self, likes, dislikes):
        print 'likes =', likes
        print 'dislikes =', dislikes
        negative_content = set([self.dictionary.token2id[str(-x)] for x in dislikes])
        print 'negative_content =', negative_content
        likes = set([self.dictionary.token2id[str(item)] for item in likes])
        print 'likes =', likes
        dislikes = set([self.dictionary.token2id[str(item)] for item in dislikes])
        print 'dislikes =', dislikes
        assert likes.isdisjoint(dislikes),\
            'likes and dislikes are not disjoint'
        assert self.session_likes.isdisjoint(likes),\
            'new likes are not disjoint with old likes'
        assert self.session_dislikes.isdisjoint(dislikes),\
            'new dislikes are not disjoint with old dislikes'
        assert self.session_content.isdisjoint(negative_content),\
            'new negative content is not disjoint with old content'
        self.session_likes = self.session_likes.union(likes)
        print 'self.session_likes =', self.session_likes
        self.session_dislikes = self.session_dislikes.union(dislikes)
        print 'self.session_dislikes =', self.session_dislikes
        self.session_content = self.session_content.union(likes)
        self.session_content = self.session_content.union(negative_content)
        print 'self.session_content =', self.session_content

    def predict(self, num_items):
        print 'self.session_content =', self.session_content
        content_vector = [(item, 1) for item in self.session_content]
        print 'content_vector =', content_vector
        topic_dist = self.model[content_vector]
        print 'topic_dist =', topic_dist
        topic_probs = [topic[1] for topic in topic_dist]
        print 'topic_probs =', topic_probs
        topic_sample = multinomial(num_items, topic_probs)
        print 'topic_sample =', topic_sample
        items = set()
        tokens = set()
        for i in range(len(topic_sample)):
            draws = topic_sample[i]
            if draws == 0:
                continue
            topicid = topic_dist[i][0]
            print 'i = %d, draws = %d, topicid = %d' % (i, draws, topicid)
            item_dist = self.model.show_topic(topicid, topn=self.topn_items)
            item_probs = [item[0] for item in item_dist]
            taken = 0
            while taken < draws:
                item_sample = multinomial(draws, item_probs)
                for j in range(len(item_sample)):
                    if item_sample[j] == 0:
                        continue
                    token = item_dist[j][1]
                    print 'token = %s' % token
                    if int(token) < 0:
                        continue
                    itemid = self.dictionary.token2id[token]
                    print 'j = %d, itemid = %d' % (j, itemid)
                    if itemid not in items and \
                       itemid not in self.session_likes and \
                       itemid not in self.session_dislikes:
                        taken += 1
                        items.add(itemid)
                        print 'items =', items
                        tokens.add(int(token))
                        print 'tokens =', tokens
        return tokens

def main():
    """A simple, sanity-checking test."""
    predictor = BayesPredictor(dict_fname='products.dict', model_fname='lda.pickle')
    print 'Loading Model. . .'
    predictor.loadModel()
    # induce population of mapping
    print predictor.dictionary[predictor.dictionary.token2id['960598']]
    likes = [960598,666644,632709,551024,932073,960606,824431,914853,1093859,1053814]
    dislikes = [515584,632705,1029423,954024,741969,816553,741970,682798,816570,716589]
    print 'Providing initial feedback. . .'
    predictor.feedback(likes, dislikes)
    print 'Soliciting prediction. . .'
    items = predictor.predict(10)
    print items

if __name__ == '__main__':
    main()
