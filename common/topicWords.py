#!/usr/bin/env python

from gensim import corpora
from gensim.models import ldamodel
from optparse import OptionParser
import pickle
import os
import sys
import math
import sqlite3

from SessionTranslator import SessionTranslator

# db_params
selectProducts =\
   ('SELECT P.Id, Description '
    'FROM Products P join Categories C '
    'WHERE Category = :Category ')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='dbname',
        default='data/macys.db',
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('-i', '--idfname', dest='idfname',
        help='Name of pickle with saved idfs')
    parser.add_option('--dictfname', dest='dictfname',
        default='data/tokens.dict',
        help='Dictionary that maps itemids to tokens.', metavar='FILE')
    parser.add_option('-n', '--topn', type='int', dest='topn', default=100,
        help='Number of items per topic to print.', metavar='NUM')
    parser.add_option('-k', '--topnWords', type='int', dest='topnWords', default=10,
        help='Number of words per topic to print.', metavar='NUM')
    parser.add_option('-o', '--outputpickle', dest='outputpickle',
        default='data/tfidfs.pickle',
        help='Name of pickle to save tfidfs per topic')
    parser.add_option('--category', dest='category', help='Category of products')
    return parser

def getTopicStrength(dictionary, model, item, topic):
    item_dist = model.show_topic(topic, topn=len(dictionary))
    topicStrength = [kvp[0] for kvp in item_dist if kvp[1] == item][0]
    return topicStrength

def getItemTopics(dictionary, model, item):
    mixture = [0]*model.num_topics
    for topic in range(model.num_topics):
        item_dist = model.show_topic(topic, topn=len(dictionary))
        mixture[topic] = [kvp[0] for kvp in item_dist if kvp[1] == item][0]
    total = sum([x for x in mixture])
    return [(ind, x/total) for ind, x in enumerate(mixture)]

def getTopWordsOfTopic(topic, items, descriptions, dictionary, model, idf):
    tf = {}
    # Count terms over descriptions of all topn products to determine tf
    for i in range(len(items)):
        #  mixture = getItemTopics(dictionary, model, items[i])
        #  topicStrength = mixture[topic]
        topicStrength = getTopicStrength(dictionary, model, items[i], topic)
        words = descriptions[i].split()
        for word in words:
            word = word.lower()
            if word in tf:
                tf[word] += topicStrength
            else:
                tf[word] = topicStrength
    # Sort words by tfidf
    tfidfs = []
    for word in tf: 
        if word not in idf:
            continue
        tfidfScore = tf[word] * idf[word]
        tfidf = [word, tfidfScore]
        tfidfs.append(tfidf)
    tfidfs.sort(key=lambda tup: tup[1], reverse=True)
    return tfidfs

def getTopWordsByTopic(dictionary, model, translator, idf, topn):
    tfidfPerTopic = []
    for topic in range(model.num_topics):
        print 'Topic %d...' % topic
        item_dist = model.show_topic(topic, topn=topn)
        items = [pair[1] for pair in item_dist]
        descriptions = translator.sessionToDesc(items)
        tfidfPerTopic.append(getTopWordsOfTopic(topic, items, descriptions, dictionary,
                model, idf))
    return tfidfPerTopic
        
def main():
    # Parse options
    usage = 'Usage: %prog [options] <lda.pickle>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    modelfname = args[0]
    if not os.path.isfile(modelfname):
        print >> sys.stderr, 'Cannot find %s' % modelfname
        return

    # get dictionary
    print 'getting dictionary...'
    dictionary = corpora.Dictionary.load_from_text(options.dictfname)

    # load lda model
    print 'loading lda model...'
    with open(modelfname, 'r') as f:
        model = pickle.load(f)

    # get translator
    print 'getting translator...'
    translator = SessionTranslator(options.dbname)

    # calculate idfs over all products
    print 'loading idfs...'
    idfpickle = options.idfname
    with open(idfpickle, 'r') as f:
        idf = pickle.load(f)

    # get top words for each topic 
    print 'getting top words...'
    tfidfs = getTopWordsByTopic(dictionary, model, translator, idf, options.topn)
    pickle.dump(tfidfs, open(options.outputpickle, 'w'))

    # Print the topnWords
    for topic in range(model.num_topics):
        print ''
        print 'Top words for topic %d' % topic
        print '======================='
        for i in range(options.topnWords):
            print tfidfs[topic][i][0] + ': ' + str(tfidfs[topic][i][1])

if __name__ == '__main__':
    main()
