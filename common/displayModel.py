#!/usr/bin/env python

from gensim import corpora
from gensim.models import ldamodel
from optparse import OptionParser
import math
import pickle
import os
import sys

from SessionTranslator import SessionTranslator

# params
imgsrcTemplate = 'images/%s.jpg'
topnWords = 10

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='dbname',
        default='data/macys.db',
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('--dictfname', dest='dictfname',
        default='data/tokens.dict',
        help='Dictionary that maps itemids to tokens.', metavar='FILE')
    parser.add_option('-n', '--topn', type='int', dest='topn', default=10,
        help='Number of items per topic to print.', metavar='NUM')
    parser.add_option('--tfidf', dest='tfidf', default=None,
        help='File containing pickled TF-IDF scores.', metavar='FILE')
    parser.add_option('--compare', action='store_true', dest='compare',
        help='Quantitatively compare topics.')
    return parser

def cosineSim(listA, listB):
    numerator = 0.0
    varA = 0.0
    varB = 0.0
    i = 0
    j = 0
    while i < len(listA) and j < len(listB):
        if listA[i][1] < listB[j][1]:
            varA += listA[i][0]**2
            i += 1
        elif listA[i][1] > listB[j][1]:
            varB += listB[j][0]**2
            j += 1
        else:
            numerator += listA[i][0]*listB[j][0]
            varA += listA[i][0]**2
            varB += listB[j][0]**2
            i += 1
            j += 1
    return numerator/(math.sqrt(varA)*math.sqrt(varB))

def sampleCorrelation(listA, listB):
    assert(len(listA) == len(listB))
    avgA = sum(listA)/len(listA)
    avgB = sum(listB)/len(listB)
    numerator = 0.0
    varA = 0.0
    varB = 0.0
    for i in range(len(listA)):
        numerator += (listA[i] - avgA)*(listB[i] - avgB)
        varA += (listA[i] - avgA)**2
        varB += (listB[i] - avgB)**2
    return numerator/math.sqrt(varA*varB)

def getItemTopics(dictionary, model, item):
    alpha_sum = sum(model.alpha)
    p_topic = [x/alpha_sum for x in model.alpha]
    p_item = 0
    p_item_given_topic = [0]*model.num_topics
    for topic in range(model.num_topics):
        item_dist = model.show_topic(topic, topn=len(dictionary))
        p_item_given_topic[topic] =\
            [kvp[0] for kvp in item_dist if kvp[1] == item][0]
        p_item += p_item_given_topic[topic]*p_topic[topic]
    p_topic_given_item = [0]*model.num_topics
    for topic in range(model.num_topics):
        p_topic_given_item[topic] =\
            p_item_given_topic[topic]*p_topic[topic]/p_item
    return [(ind, x) for ind, x in enumerate(p_topic_given_item)]

def genHtml(dictionary, model, translator, topn, tfidf=None, compare=False):
    print '<html lang="en" debug="true">'
    print '<head><title>Display LDA Topics</title></head>'
    print '<body>'
    print '<p>model.alpha =', model.alpha, '</p>'
    # print top N items from each topic
    for topic in range(model.num_topics):
        print '<hr><div><b>Topic: %d</b>' % topic
        if tfidf is not None:
            print '<p>Top words for topic %d</p>' % topic
            print '<ul>'
            for i in range(topnWords):
                print '<li>%s : %.3f</li>' %\
                    (tfidf[topic][i][0], tfidf[topic][i][1])
            print '</ul>'
        item_dist = model.show_topic(topic, topn=topn)
        items = [pair[1] for pair in item_dist]
        descriptions = translator.sessionToDesc(items)
        for i in range(len(items)):
            imgsrc = imgsrcTemplate % items[i]
            print '<div><table><tr><td><img src="%s"></td>' % imgsrc
            doc_bow = [(dictionary.token2id[items[i]], 1)]
            mixture = getItemTopics(dictionary, model, items[i])
            print >> sys.stderr, 'DBG: mixture =', mixture
            print '<td><table>'
            for component in mixture:
                print '<tr><td>%d, %.3f</td></tr>' %\
                      (component[0], component[1])
            print '<tr><td>(%s) %s</td></tr>' % (items[i], descriptions[i])
            print '</table></td></tr></table></div>' 
        print '</div>'
    if compare and model.num_topics > 1:
        prod_sims = []
        tfidf_sims = []
        for topicA in range(model.num_topics-1):
            topic_distA = model.show_topic(topicA, len(dictionary))
            topic_distA.sort(key=lambda x: x[1])
            tfidfA = [(x[1], x[0]) for x in tfidf[topicA]]
            tfidfA.sort(key=lambda x: x[1])
            for topicB in range(topicA+1, model.num_topics):
                # compare topicA and topicB
                print '<hr><div><b>Compare Topics %d and %d</b>' %\
                      (topicA, topicB)
                topic_distB = model.show_topic(topicB, len(dictionary))
                topic_distB.sort(key=lambda x: x[1])
                tfidfB = [(x[1], x[0]) for x in tfidf[topicB]]
                tfidfB.sort(key=lambda x: x[1])
                prod_sims.append(cosineSim(topic_distA, topic_distB))
                print '<p>Product Space: CosineSim: %f</p>' % prod_sims[-1]
                tfidf_sims.append(cosineSim(tfidfA, tfidfB))
                print '<p>TF-IDF Space: CosineSim: %f</p>' % tfidf_sims[-1]
                print '</div>'
        print '<hr><div>'
        print '<b>Sample Correlation between Product and TF-IDF Sims: '
        correlation = sampleCorrelation(prod_sims, tfidf_sims)
        print '%f</b></div>' % correlation
    print '</body></html>'

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
    dictionary = corpora.Dictionary.load_from_text(options.dictfname)

    # load lda model
    with open(modelfname, 'r') as f:
        model = pickle.load(f)

    # get translator
    translator = SessionTranslator(options.dbname)

    # get tf-idf scores
    if options.tfidf is not None:
        with open(options.tfidf, 'r') as f:
            try:
                tfidf = pickle.load(f)
            except:
                print >> sys.stderr, 'ERROR: Failed to parse tfidf file.'
                return
    else:
        tfidf = None

    # generate html document
    genHtml(dictionary, model, translator, options.topn, tfidf=tfidf,
            compare=options.compare)

if __name__ == '__main__':
    main()
