#!/usr/local/bin/python

"""
Conduct a stupidly simple simulation of user-predictor interaction.
"""

from SessionTranslator import SessionTranslator
#from BayesPredictor import BayesPredictor
from ArgMaxPredictor import ArgMaxPredictor
import sqlite3
import random

# params
db_fname = 'macys.db'
dict_fname = 'tokens.dict'
model_fname = 'lda.pickle'
NUM_INIT_ITEMS = 10
NUM_ITEMS_PER_ROUND = 10
ROUNDS = 25
                                  # argmax  bayes
#CATEGORY = 'T-Shirts'            # 0.548   0.356   0.420
CATEGORY = 'Sunglasses'          # 0.996   0.996   0.724
#CATEGORY = 'Calvin Klein'        # 0.5     0.576   0.404
#CATEGORY = 'Swimwear'            # 0.31    0.207   0.420
#CATEGORY = 'Lucky Brand Jeans'   # 0.23    0.254   0.132
#CATEGORY = 'Dress Shirts'        # 0.98    0.884   0.592

selectItemsStmt = 'SELECT Id FROM Categories WHERE Category = :category'
selectCatsStmt = 'SELECT Category FROM Categories WHERE Id = :id'

def randomPop(data):
    if data != []:
        pos = random.randrange( len(data) )
        elem = data[pos]
        data[pos] = data[-1]
        del data[-1]
        return elem
    else:
        return None

def getInitItems(cursor, category):
    """Randomly choose and return NUM_INIT_ITEMS from `category'."""
    cursor.execute(selectItemsStmt, (category,))
    all_items = [row[0] for row in cursor.fetchall()]
    init_items = []
    for i in range(NUM_INIT_ITEMS):
        init_items.append(randomPop(all_items))
    return init_items

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
    random.seed()
    print 'Connecting to db. . .'
    db_conn = sqlite3.connect(db_fname)
    with db_conn:
        cursor = db_conn.cursor()
        translator = SessionTranslator(db_fname)
        #predictor = BayesPredictor(dict_fname=dict_fname, model_fname=model_fname)
        predictor = ArgMaxPredictor(dict_fname=dict_fname, model_fname=model_fname)
        print 'Loading LDA Model. . .'
        predictor.loadModel()
        print 'Generating initial items (%s). . .' % CATEGORY
        items = getInitItems(cursor, CATEGORY)
        print items
        print 'Translating to cats. . .'
        print translator.sessionToCats(items)
        print translator.sessionToDesc(items)
        print 'Starting session. . .'
        likes = 0
        dislikes = 0
        predictor.feedback(items, [])
        for i in range(ROUNDS):
            print '=========================================='
            print 'Round %d' % i
            new_items = predictor.predict(NUM_ITEMS_PER_ROUND)
            print translator.sessionToDesc(new_items)
            print translator.sessionToCats(new_items)
            judgements = judgeItems(cursor, CATEGORY, new_items)
            round_likes = len(judgements['likes'])
            round_dislikes = len(judgements['dislikes'])
            print 'likes = %d, dislikes = %d, score = %.3f' %\
                (round_likes, round_dislikes,
                 float(round_likes)/(round_likes + round_dislikes))
            likes += round_likes
            dislikes += round_dislikes
            predictor.feedback(judgements['likes'], judgements['dislikes'])
        print 'Total likes = %d, Total dislikes = %d, Final Score %.3f' %\
            (likes, dislikes, float(likes)/(likes + dislikes))

if __name__ == '__main__':
    main()
