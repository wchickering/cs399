#!/usr/bin/env python

from LDAPredictor import LDAPredictor
from numpy.random import multinomial

class BayesPredictor(LDAPredictor):
    """An implementation of an LDAPredictor that uses Bayes' rule to generate
    item predictions.
    """

    def __init__(self, ignore_dislikes=True, topn_items=1000, **kwds):
        """Constructs a new BayesPredictor.

        Note that predictions associated with a topic are limited to the most
        likely topn_items items.
        """
        super(BayesPredictor, self).__init__(**kwds)
        self.ignore_dislikes = ignore_dislikes
        self.topn_items = topn_items=1000

    def initSession(self):
        self.session_likes = set()
        self.session_dislikes = set()
        self.session_content = set()

    def feedback(self, likes, dislikes):
        if not self.ignore_dislikes:
            negative_content = set([self.model.id2word.token2id[str(-token)]\
                                    for token in dislikes])
        likes =\
            set([self.model.id2word.token2id[str(token)] for token in likes])
        dislikes =\
            set([self.model.id2word.token2id[str(token)] for token in dislikes])

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
        topic_probs = [topic[1] for topic in topic_dist]
        topic_sample = multinomial(num_items, topic_probs)
        items = set()
        predictions = []
        for i in range(len(topic_sample)):
            draws = topic_sample[i]
            if draws == 0:
                continue
            topicid = topic_dist[i][0]
            item_dist = self.model.show_topic(topicid, topn=self.topn_items)
            item_probs = [item[0] for item in item_dist]
            taken = 0
            while taken < draws:
                item_sample = multinomial(draws - taken, item_probs)
                for j in range(len(item_sample)):
                    if item_sample[j] == 0:
                        continue
                    token_str = item_dist[j][1]
                    if not self.ignore_dislikes and int(token_str) < 0:
                        continue
                    itemid = self.model.id2word.token2id[token_str]
                    if itemid not in items and \
                       itemid not in self.session_likes and \
                       itemid not in self.session_dislikes:
                        taken += 1
                        items.add(itemid)
                        predictions.append(int(token_str))
        return predictions

def main():
    """A simple, sanity-checking test."""
    predictor = BayesPredictor(model_fname='data/lda.pickle')
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
