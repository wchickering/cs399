#!/usr/bin/env python

from gensim import corpora, models, similarities
from gensim.models import ldamodel
from optparse import OptionParser
import csv
import pickle
import random
import os
import sys

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--dictfname', dest='dictfname',
        default='data/tokens.dict',
        help='Dictionary that maps itemids to tokens.', metavar='FILE')
    return parser

def getCorpus(dictionary, filename):
    with open(filename) as csvIn:
        reader = csv.reader(csvIn)
        records = [record for record in reader]
    return [dictionary.doc2bow(record) for record in records]

def main():
    # Parse options
    usage = 'Usage: %prog [options] <model.pickle> <testdocs>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    modelfname = args[0]
    if not os.path.isfile(modelfname):
        print >> sys.stderr, 'Cannot find %s' % modelfname
        return
    testfname = args[1]
    if not os.path.isfile(testfname):
        print >> sys.stderr, 'Cannot find %s' % testfname
        return

    # get dictionary
    print 'Loading dictionary. . .'
    dictionary = corpora.Dictionary.load_from_text(options.dictfname)

    # load lda model
    print 'Loading LDA model. . .'
    with open(modelfname, 'r') as f:
        model = pickle.load(f)

    # get test corpus
    print 'Loading test corpus. . .'
    corpus = getCorpus(dictionary, testfname)

    # print lower bound on perplexity
    print 'Perplexity lower bound:', model.bound(corpus)

if __name__ == '__main__':
    main()

