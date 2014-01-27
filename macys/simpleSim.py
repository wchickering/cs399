#!/usr/local/bin/python

"""
Conduct a stupidly simple simulation of user-predictor interaction.
"""

from SessionTranslator import SessionTranslator
from BayesPredictor import BayesPredictor
import sqlite3

# params
db_fname = 'macys.db'
dict_fname = 'tokens.dict'
model_fname = 'lda.pickle'
NUM_INIT_ITEMS = 10
NUM_ITEMS_PER_ROUND = 10
#CATEGORY = 'T-Shirts'            # ~0.3 accurancy
#CATEGORY = 'Sunglasses'          # ~0.9
#CATEGORY = 'Calvin Klein'        # ~0.3
#CATEGORY = 'Swimwear'            # ~0.03 huh?
#CATEGORY = 'Lucky Brand Jeans'   # ~0.2
CATEGORY = 'Dress Shirts'        # ~0.3
ROUNDS = 100

selectItemsStmt = 'SELECT Id FROM Categories WHERE Category = :category LIMIT :limit'
selectCatsStmt = 'SELECT Category FROM Categories WHERE Id = :id'

def getInitItems(cursor, category):
    cursor.execute(selectItemsStmt, (category, NUM_INIT_ITEMS))
    return [row[0] for row in cursor.fetchall()]

def judgeItems(cursor, category, items):
    """Partition items into likes and dislikes using the simple-minded protocol
    that items in CATEGORY are liked, all other items are disliked.
    """
    judgements = {}
    judgements['likes'] = []
    judgements['dislikes'] = []
    for item in items:
        cursor.execute(selectCatsStmt, (item,))
        cats = [row[0] for row in cursor.fetchall()]
        if category in cats:
            judgements['likes'].append(item)
        else:
            judgements['dislikes'].append(item)
    return judgements

def main():
    print 'Connecting to db. . .'
    db_conn = sqlite3.connect(db_fname)
    with db_conn:
        cursor = db_conn.cursor()
        translator = SessionTranslator(db_fname)
        predictor = BayesPredictor(dict_fname=dict_fname, model_fname=model_fname)
        print 'Loading LDA Model. . .'
        predictor.loadModel()
        print 'Generating initial items (%s). . .' % CATEGORY
        items = getInitItems(cursor, CATEGORY)
        print items
        print 'Translating to cats. . .'
        print translator.sessionToCats(items)
        print 'Starting session. . .'
        likes = 0
        dislikes = 0
        predictor.feedback(items, [])
        for i in range(ROUNDS):
            print '=========================================='
            print 'Round %d' % i
            new_items = predictor.predict(NUM_ITEMS_PER_ROUND)
            judgements = judgeItems(cursor, CATEGORY, new_items)
            round_likes = len(judgements['likes'])
            round_dislikes = len(judgements['dislikes'])
            print 'likes = %d, dislikes = %d, score = %.3f' %\
                (round_likes, round_dislikes,
                 float(round_likes)/(round_likes + round_dislikes))
            likes += round_likes
            dislikes += round_dislikes
        print 'Total likes = %d, Total dislikes = %d, Final Score %.3f' %\
            (likes, dislikes, float(likes)/(likes + dislikes))

if __name__ == '__main__':
    main()
