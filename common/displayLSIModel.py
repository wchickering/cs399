#!/usr/bin/env python

from optparse import OptionParser
import numpy as np
import csv
import math
import pickle
import os
import sys

import LSI_util as lsi
from SessionTranslator import SessionTranslator

# params
imgsrcTemplate = 'images/%s.jpg'
topnWords = 10

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='dbname',
        default='data/macys.db',
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('-k', type='int', dest='k', default=10,
        help='Number of concepts in LSI model.', metavar='NUM')
    parser.add_option('-n', '--topn', type='int', dest='topn', default=10,
        help='Number of items per concept to print.', metavar='NUM')
    parser.add_option('--tfidf', dest='tfidf', default=None,
        help='File containing pickled TF-IDF scores.', metavar='FILE')
    parser.add_option('--compare', action='store_true', dest='compare',
        help='Quantitatively compare concepts.')
    parser.add_option('--noimages', action='store_true', dest='noimages',
        help='Do not include topn images (faster processing).')
    return parser

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

def displayConceptImages(u, k, concept, topn, reverse, id2word, translator,
                         term_concepts):
    item_dist = lsi.showConcept(u, k, concept, topn=topn, reverse=reverse)
    items = [str(id2word[pair[1]]) for pair in item_dist]
    descriptions = translator.sessionToDesc(items)
    if reverse:
        sectionTitle = 'Top'
    else:
         sectionTitle = 'Bottom'
    print '<div><b>%s %d</b>' % (sectionTitle, len(items))
    for i in range(len(items)):
        imgsrc = imgsrcTemplate % items[i]
        print '<div><table><tr><td><img src="%s"></td>' % imgsrc
        mixture = term_concepts[:,item_dist[i][1]]
        print '<td><table>'
        for c in range(k):
            print '<tr><td>%d, %+.2e</td></tr>' % (c, mixture[c])
        print '<tr><td>(%s) %s</td></tr>' % (items[i], descriptions[i])
        print '</table></td></tr></table></div>' 
    print '</div>'

def genHtml(u, s, k, id2word, translator, topn, tfidf=None, compare=False,
            noimages=False):
    print >> sys.stderr, 'Compute term concepts. . .'
    term_concepts = lsi.getTermConcepts(u, s, k)
    print '<html lang="en" debug="true">'
    print '<head><title>Display LSI Concepts</title></head>'
    print '<body>'
    # print top N items from each concept
    print >> sys.stderr, 'Display concept info. . .'
    for concept in range(k):
        print '<hr><div><h3>Concept: %d</h3>' % concept
        if tfidf is not None:
            print '<p>Top words for concept %d</p>' % concept
            print '<ul>'
            for i in range(topnWords):
                print '<li>%s : %.3f</li>' %\
                    (tfidf[concept][i][0], tfidf[concept][i][1])
            print '</ul>'
        if not noimages:
            # top 10
            displayConceptImages(u, k, concept, topn, True, id2word,
                                 translator, term_concepts)
            # bottom 10
            displayConceptImages(u, k, concept, topn, False, id2word,
                                 translator, term_concepts)
        print '</div>'
    if compare and k > 1:
        print >> sys.stderr, 'Compare concepts. . .'
        prod_sims = []
        tfidf_sims = []
        for conceptA in range(k-1):
            if tfidf:
                tfidfA = [(x[1], x[0]) for x in tfidf[conceptA]]
                tfidfA.sort(key=lambda x: x[1])
            for conceptB in range(conceptA+1, k):
                # compare conceptA and conceptB
                print '<hr><div><b>Compare Concepts %d and %d</b>' %\
                      (conceptA, conceptB)
                prod_sims.append(lsi.conceptCorrelation(u, conceptA, conceptB))
                print '<p>Concept Space: correlation: %f</p>' % prod_sims[-1]
                if tfidf:
                    tfidfB = [(x[1], x[0]) for x in tfidf[conceptB]]
                    tfidfB.sort(key=lambda x: x[1])
                    tfidf_sims.append(cosSimSparseVecs(tfidfA, tfidfB))
                    print '<p>TF-IDF Space: CosineSim: %f</p>' % tfidf_sims[-1]
                print '</div>'
        if tfidf:
            print '<hr><div>'
            print '<b>Sample Correlation between Product and TF-IDF Sims: '
            correlation = sampleCorrelation(prod_sims, tfidf_sims)
            print '%f</b></div>' % correlation
    print '</body></html>'

def main():
    # Parse options
    usage = 'Usage: %prog [options] <svd.npz>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    modelfname = args[0]
    if not os.path.isfile(modelfname):
        print >> sys.stderr, 'ERROR: Cannot find %s' % modelfname
        return

    # load LSI model
    print >> sys.stderr, 'Load LSI model. . .'
    npzfile = np.load(modelfname)
    u = npzfile['u']
    s = npzfile['s']
    v = npzfile['v']
    id2word = npzfile['nodes']

    # get translator
    translator = SessionTranslator(options.dbname)

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
    genHtml(u, s, options.k, id2word, translator, options.topn, tfidf=tfidf,
            compare=options.compare, noimages=options.noimages)

if __name__ == '__main__':
    main()
