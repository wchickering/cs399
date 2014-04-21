#!/usr/bin/env python

from optparse import OptionParser
import csv
import math
import pickle
import os
import sys

import LDA_util as lda
from SessionTranslator import SessionTranslator

# params
imgsrcTemplate = 'images/%s.jpg'
topnWords = 10

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='dbname',
        default='data/macys.db',
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('-n', '--topn', type='int', dest='topn', default=10,
        help='Number of items per topic to print.', metavar='NUM')
    parser.add_option('--testcorpus', dest='testcorpus', default=None,
        help='CSV File containing test corpus.', metavar='FILE')
    parser.add_option('--tfidf', dest='tfidf', default=None,
        help='File containing pickled TF-IDF scores.', metavar='FILE')
    parser.add_option('--compare', action='store_true', dest='compare',
        help='Quantitatively compare topics.')
    parser.add_option('--noimages', action='store_true', dest='noimages',
        help='Do not include topn images (faster processing).')
    return parser

def getCorpus(model, filename):
    with open(filename) as csvIn:
        reader = csv.reader(csvIn)
        records = [record for record in reader]
    return [model.id2word.doc2bow(record) for record in records]

def cosSimSparseVecs(listA, listB):
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
    return numerator/math.sqrt(varA*varB)

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

def genHtml(model, translator, topn, test_corpus=None, tfidf=None,
            compare=False, noimages=False):
    print >> sys.stderr, 'Compute p(topic | item) values. . .'
    p_topic_given_item = lda.getTopicGivenItemProbs(model)
    print '<html lang="en" debug="true">'
    print '<head><title>Display LDA Topics</title></head>'
    print '<body>'
    print '<p>model.alpha =', model.alpha, '</p>'
    if test_corpus is not None:
        print >> sys.stderr, 'Compute model perplexity for test corpus. . .'
        print '<p>model.log_perplexity(test_corpus) = %.3f</p>' %\
              model.log_perplexity(test_corpus)
    # print top N items from each topic
    print >> sys.stderr, 'Display topic info. . .'
    for topic in range(model.num_topics):
        print '<hr><div><b>Topic: %d</b>' % topic
        if tfidf is not None:
            print '<p>Top words for topic %d</p>' % topic
            print '<ul>'
            for i in range(topnWords):
                print '<li>%s : %.3f</li>' %\
                    (tfidf[topic][i][0], tfidf[topic][i][1])
            print '</ul>'
        if not noimages:
            item_dist = model.show_topic(topic, topn=topn)
            items = [pair[1] for pair in item_dist]
            descriptions = translator.sessionToDesc(items)
            for i in range(len(items)):
                imgsrc = imgsrcTemplate % items[i]
                print '<div><table><tr><td><img src="%s"></td>' % imgsrc
                mixture = p_topic_given_item[:,model.id2word.token2id[items[i]]]
                print '<td><table>'
                for topic in range(model.num_topics):
                    print '<tr><td>%d, %.3f</td></tr>' % (topic, mixture[topic])
                print '<tr><td>(%s) %s</td></tr>' % (items[i], descriptions[i])
                print '</table></td></tr></table></div>' 
        print '</div>'
    if compare and model.num_topics > 1:
        print >> sys.stderr, 'Compare topics. . .'
        prod_sims = []
        tfidf_sims = []
        for topicA in range(model.num_topics-1):
            tfidfA = [(x[1], x[0]) for x in tfidf[topicA]]
            tfidfA.sort(key=lambda x: x[1])
            for topicB in range(topicA+1, model.num_topics):
                # compare topicA and topicB
                print '<hr><div><b>Compare Topics %d and %d</b>' %\
                      (topicA, topicB)
                tfidfB = [(x[1], x[0]) for x in tfidf[topicB]]
                tfidfB.sort(key=lambda x: x[1])
                prod_sims.append(lda.cosSimTopics(model, topicA, topicB))
                print '<p>Product Space: CosineSim: %f</p>' % prod_sims[-1]
                tfidf_sims.append(cosSimSparseVecs(tfidfA, tfidfB))
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
        print >> sys.stderr, 'ERROR: Cannot find %s' % modelfname
        return

    # load lda model
    print >> sys.stderr, 'Load LDA model. . .'
    with open(modelfname, 'r') as f:
        model = pickle.load(f)

    # get translator
    translator = SessionTranslator(options.dbname)

    # get test corpus
    if options.testcorpus is not None:
        print >> sys.stderr, 'Load test corpus. . .'
        if not os.path.isfile(options.testcorpus):
            print >> sys.stderr, 'WARNING: Cannot find %s' % options.testcorpus
            test_corpus = None
        else:
            test_corpus = getCorpus(model, options.testcorpus)
    else:
        test_corpus = None

    # get tf-idf scores
    if options.tfidf is not None:
        print >> sys.stderr, 'Load TF-IDF scores. . .'
        with open(options.tfidf, 'r') as f:
            try:
                tfidf = pickle.load(f)
            except:
                print >> sys.stderr, 'ERROR: Failed to parse tfidf file.'
                return
    else:
        tfidf = None

    # generate html document
    genHtml(model, translator, options.topn, test_corpus=test_corpus,
            tfidf=tfidf, compare=options.compare, noimages=options.noimages)

if __name__ == '__main__':
    main()
