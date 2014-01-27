#!/usr/local/bin/python

from gensim import corpora, models, similarities
from gensim.models import ldamodel
import sqlite3
import logging
import pickle
import csv

# params
db_fname = 'macys.db'
inFile = 'trainSessions.csv'
testFile = 'testSessions.csv'
corpusFile = 'categorySessions.corp'
dictFile = 'products.dict'
ldaFile = 'lda.pickle'

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

def getDictionary(filename):
    try:
        dictionary = corpora.Dictionary.load_from_text(dictFile)
        logging.info('Reading dictionary from %s.' % dictFile)
    except IOError:
        with open(filename) as csvIn:
            reader = csv.reader(csvIn)
            records = [record for record in reader]
            dictionary = corpora.Dictionary(records)
            dictionary.save_as_text(dictFile)
    return dictionary
            
def getCorpus(dictionary, filename):
    logging.info('Reading corpus from %s.' % filename)
    with open(filename) as csvIn:
        reader = csv.reader(csvIn)
        records = [record for record in reader]
        return [dictionary.doc2bow(record) for record in records]

def getLDA():
    try:
        with open(ldaFile, 'r') as f:
            lda = pickle.load(f)
            logging.info('Reading LDA model from %s.' % ldaFile)
    except IOError:
        dictionary = getDictionary(inFile)
        corpus = getCorpus(dictionary, inFile)
        lda = ldamodel.LdaModel(corpus=corpus,
                                id2word=dictionary,
                                num_topics=100,
                                passes=40,
                                update_every=1,
                                chunksize=800)
        pickle.dump(lda, open(ldaFile, 'w'))
    return lda

def getSessionCats(db_curs, dictionary, session):
    selectCategoriesStmt = 'SELECT Category FROM Categories WHERE Id = :Id'
    sessionCats = {}
    for product in session:
        productId = dictionary[product[0]]
        db_curs.execute(selectCategoriesStmt, (productId,))
        for row in db_curs.fetchall():
            category = row[0]
            if category in sessionCats:
                sessionCats[category] += 1
            else:
                sessionCats[category] = 1
    return sessionCats
    

def handleSession(lda, db_curs, dictionary, session):
    print getSessionCats(db_curs, dictionary, session)
    print lda[session]

def main():
    # Either fetch or construct LDA model
    lda = getLDA()

    # Connect to product db
    db_conn = sqlite3.connect(db_fname)
    with db_conn:
        db_curs = db_conn.cursor()
        
        #print 'Top 10 productIds from first 10 topics:'
        #lda.print_topics()

        dictionary = getDictionary(inFile)
        testCorpus = getCorpus(dictionary, testFile)
        for session in testCorpus:
            #print lda[session]
            handleSession(lda, db_curs, dictionary, session)

if __name__ == '__main__':
    main()
