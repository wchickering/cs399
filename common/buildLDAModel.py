#!/usr/bin/env python

"""
Construct and save LDA model using Radim Rehurek's gensim module.
"""

from gensim import corpora
from gensim.models import ldamodel
from optparse import OptionParser
import numpy as np
import pickle
import csv
import os
import sys

# local modules
from Util import loadPickle, getAndCheckFilename

# gensim params
chunksize=100
update_every=1
eta=None
decay=0.5
eval_every=10

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-f', '--docfile', dest='docfile', default=None,
        help=('CSV file containing training data. Each line consists of tokens '
              'liked in a single session.'), metavar='FILE')
    parser.add_option('-m', '--matrixfile', dest='matrixfile', default=None,
        help=('NPZ file with probability matrix from random walks '
              '(rows are distributions).'), metavar='FILE')
    parser.add_option('-l', '--lda-file', dest='lda_filename',
        default='lda.pickle', help='Save file for LDA model.',
        metavar='FILE')
    parser.add_option('-t', '--num-topics', dest='num_topics', type='int',
        default=20, help='Number of topics in LDA model.', metavar='NUM')
    parser.add_option('-p', '--passes', dest='passes', type='int', default=1,
        help='Number of passes for training LDA model.', metavar='NUM')
    parser.add_option('--alpha', dest='alpha', default='symmetric',
        help='Alpha param for gensim.LdaModel().', metavar='VAL')
    return parser

def getDictFromMatrix(filename):
    npzfile = np.load(filename)
    matrix = npzfile['matrix']
    id2item = npzfile['dictionary']
    return corpora.Dictionary([[str(item)] for item in id2item])

def getCorpusFromMatrix(filename, dictionary):
    npzfile = np.load(filename)
    matrix = npzfile['matrix']
    id2item = npzfile['dictionary']
    return [[(dictionary.token2id[str(id2item[ind])], prob)\
            for ind, prob in enumerate(doc)] for doc in matrix]

def getDictFromDocs(filename):
    termDict = {}
    with open(filename) as csvIn:
        reader = csv.reader(csvIn)
        for record in reader:
            for term in record:
                termDict[term] = 1
    return corpora.Dictionary([[term] for term in termDict.keys()])

def getCorpusFromDocs(filename, dictionary):
    with open(filename) as csvIn:
        reader = csv.reader(csvIn)
        records = [record for record in reader]
    corpus = [dictionary.doc2bow(record) for record in records]
    return corpus

def buildModel(dictionary, num_topics, passes, alpha):
    return ldamodel.LdaModel(corpus=None,
                             num_topics=num_topics,
                             id2word=dictionary,
                             chunksize=chunksize,
                             passes=passes,
                             update_every=update_every,
                             alpha=alpha,
                             eta=eta,
                             decay=decay,
                             eval_every=eval_every)

def main():
    # Parse options
    usage = 'Usage: %prog [options] [model.pickle]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if options.docfile is None and options.matrixfile is None:
        parser.error(('Must provide either document file (--docfile) or matrix '
                      'file (--matrixfile).'))

    # Load LDA model
    model = None
    dictionary = None
    if len(args) == 1:
        modelfname = getAndCheckFilename(args[0])
        print 'Loading model from %s. . .' % modelfname
        model = loadPickle(modelfname)
        dictionary = model.id2word

    # Build dictionary
    if dictionary is None:
        if options.matrixfile is not None:
            print 'Building dictionary from %s. . .' % options.matrixfile
            dictionary = getDictFromMatrix(options.matrixfile)
        else:
            print 'Building dictionary from %s. . .' % options.docfile
            dictionary = getDictFromDocs(options.docfile)

    # Construct corpus
    if options.matrixfile is not None:
        print 'Building corpus from %s. . .' % options.matrixfile
        corpus = getCorpusFromMatrix(options.matrixfile, dictionary)
    else:
        print 'Building corpus from %s. . .' % options.docfile
        corpus = getCorpusFromDocs(options.docfile, dictionary)

    # Build model
    if model is None:
        print 'Building model. . .'
        model = buildModel(dictionary, options.num_topics, options.passes,
                           options.alpha)

    # Train LDA Model
    print 'Training model. . .'
    model.update(corpus)

    # Save LDA Model
    print 'Saving model to %s. . .' % options.lda_filename
    pickle.dump(model, open(options.lda_filename, 'w'))

if __name__ == '__main__':
    main()
