#!/usr/local/bin/python

from LDAPredictor import LDAPredictor
from gensim import corpora, models, similarities
from gensim.models import ldamodel
from numpy.random import multinomial

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
        assert self.session_content.isdisjoint(negative_content),\
            'new negative content is not disjoint with old content'

        self.session_likes = self.session_likes.union(likes)
        self.session_dislikes = self.session_dislikes.union(dislikes)
        self.session_content =\
            self.session_content.union(likes).union(negative_content)

    def predict(self, num_items):
        content_vector = [(item, 1) for item in self.session_content]
        topic_dist = self.model[content_vector]
        topic_probs = [topic[1] for topic in topic_dist]
        topic_sample = multinomial(num_items, topic_probs)
        items = set()
        tokens = set()
        for i in range(len(topic_sample)):
            draws = topic_sample[i]
            if draws == 0:
                continue
            topicid = topic_dist[i][0]
            item_dist = self.model.show_topic(topicid, topn=self.topn_items)
            item_probs = [item[0] for item in item_dist]
            taken = 0
            while taken < draws:
                item_sample = multinomial(draws, item_probs)
                for j in range(len(item_sample)):
                    if item_sample[j] == 0:
                        continue
                    token_str = item_dist[j][1]
                    if int(token_str) < 0:
                        continue
                    itemid = self.dictionary.token2id[token_str]
                    if itemid not in items and \
                       itemid not in self.session_likes and \
                       itemid not in self.session_dislikes:
                        taken += 1
                        items.add(itemid)
                        tokens.add(int(token_str))
        return tokens

def main():
    """A simple, sanity-checking test."""
    predictor = BayesPredictor(dict_fname='tokens.dict', model_fname='lda.pickle')
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
